from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _meta() -> str:
    return '\n'.join(
        [
            '# repodossier-meta: {"type":"patch","id":"TEST","title":"Test patch","commit":"Test patch"}',
            '# repodossier-meta: {"type":"display","context":1,"layout":"side-by-side","frame":false}',
        ]
    )


def _write_script(download_dir: Path, name: str, body: str, *, age_seconds: int = 0) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)

    if age_seconds:
        timestamp = time.time() - age_seconds
        os.utime(path, (timestamp, timestamp))

    return path


def _script_body(commands: str) -> str:
    return f"#!/usr/bin/env bash\n{_meta()}\n{commands}\n"


def _run_runner(download_dir: Path, *args: str, input_text: str | None = None):
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env.pop("NO_COLOR", None)

    return subprocess.run(
        [str(RUNNER), *args],
        cwd=REPO_ROOT,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _logs(download_dir: Path) -> list[Path]:
    return sorted(download_dir.glob("*.log"))


def test_c_runner_executes_newest_script_and_moves_to_done(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    old_marker = tmp_path / "old_marker"
    latest_marker = tmp_path / "latest_marker"

    _write_script(download_dir, "older_patch.sh", _script_body(f"echo old\n: > {old_marker}"), age_seconds=30)
    latest = _write_script(download_dir, "latest_patch.sh", _script_body(f"echo latest\n: > {latest_marker}"))

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert latest_marker.exists()
    assert not old_marker.exists()
    assert not latest.exists()
    assert (download_dir / "done" / "latest_patch.sh").exists()
    assert (download_dir / "older_patch.sh").exists()
    assert "Metadaten OK" in result.stdout
    assert "latest" in result.stdout
    assert "\x1b[" in result.stdout
    assert (download_dir / "done" / ".applied_patch_hashes.tsv").exists()
    assert len(_logs(download_dir)) == 1


def test_c_runner_rejects_invalid_metadata_before_execution(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    bad = _write_script(
        download_dir,
        "bad_meta_patch.sh",
        f"#!/usr/bin/env bash\n# repodossier-meta: {{\"type\":\"patch\",\"id\":\"BAD\"}}\n: > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10
    assert bad.exists()
    assert not marker.exists()
    assert "Metadatenprüfung fehlgeschlagen" in result.stdout


def test_c_runner_moves_failed_script_to_failed_and_keeps_log(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    failing = _write_script(download_dir, "failing_patch.sh", _script_body("echo before-fail\nexit 7"))

    result = _run_runner(download_dir)

    assert result.returncode == 7
    assert not failing.exists()
    assert (download_dir / "failed" / "failing_patch.sh").exists()
    assert "Patch fehlgeschlagen" in result.stdout
    assert "before-fail" in _logs(download_dir)[0].read_text(encoding="utf-8")


def test_c_runner_refuses_old_script_without_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    old_script = _write_script(
        download_dir,
        "old_patch.sh",
        _script_body(f": > {marker}"),
        age_seconds=61 * 60,
    )

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 2
    assert old_script.exists()
    assert not marker.exists()
    assert "älter" in result.stdout


def test_c_runner_executes_old_script_after_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    old_script = _write_script(download_dir, "old_confirmed_patch.sh", _script_body(f": > {marker}"), age_seconds=61 * 60)

    result = _run_runner(download_dir, input_text="y\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not old_script.exists()
    assert (download_dir / "done" / "old_confirmed_patch.sh").exists()


def test_c_runner_failed_syntax_moves_script_to_failed(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    broken = _write_script(
        download_dir,
        "broken_patch.sh",
        f"#!/usr/bin/env bash\n{_meta()}\nif true; then\necho broken\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode != 0
    assert not broken.exists()
    assert (download_dir / "failed" / "broken_patch.sh").exists()
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout


def test_c_runner_warns_red_and_refuses_already_applied_script(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    body = _script_body(f"echo applied\n: > {marker}")

    first = _write_script(download_dir, "first_patch.sh", body)
    first_result = _run_runner(download_dir)

    assert first_result.returncode == 0, first_result.stdout + first_result.stderr
    assert not first.exists()

    marker.unlink()
    duplicate = _write_script(download_dir, "duplicate_patch.sh", body)
    duplicate_result = _run_runner(download_dir, input_text="n\n")

    assert duplicate_result.returncode == 3
    assert duplicate.exists()
    assert not marker.exists()
    assert "bereits erfolgreich angewendet" in duplicate_result.stdout
    assert "\x1b[0;31m" in duplicate_result.stdout


def test_c_runner_can_rerun_already_applied_script_after_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    counter = tmp_path / "counter"
    body = _script_body(
        f"current=0\nif [ -f {counter} ]; then current=$(cat {counter}); fi\necho $((current + 1)) > {counter}"
    )

    first_result = _run_runner(download_dir, str(_write_script(download_dir, "first_patch.sh", body)))
    assert first_result.returncode == 0, first_result.stdout + first_result.stderr

    _write_script(download_dir, "duplicate_patch.sh", body)
    duplicate_result = _run_runner(download_dir, input_text="y\n")

    assert duplicate_result.returncode == 0, duplicate_result.stdout + duplicate_result.stderr
    assert counter.read_text(encoding="utf-8").strip() == "2"
    assert (download_dir / "done" / "duplicate_patch.sh").exists()
