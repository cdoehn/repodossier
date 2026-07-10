from __future__ import annotations

import os
import subprocess
import time
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _metadata(*, patch_id: str = "PATCHHARBOR.FRESHNESS.PARITY") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Freshness parity","commit":"Freshness parity"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _valid_preflight_body(commands: str, *, patch_id: str = "PATCHHARBOR.FRESHNESS.PARITY") -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"{_metadata(patch_id=patch_id)}\n"
        "print_footer() {\n"
        "  echo footer\n"
        "}\n"
        f"{commands}\n"
        "python3 -m py_compile scripts/dev/lint_patch_script.py\n"
    )


def _write_script(download_dir: Path, name: str, body: str, *, age_seconds: int = 0) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    if age_seconds:
        timestamp = time.time() - age_seconds
        os.utime(path, (timestamp, timestamp))
    return path


def _write_zip(download_dir: Path, name: str, script_name: str, body: str, *, age_seconds: int = 0) -> Path:
    path = download_dir / name
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(script_name, body)
    if age_seconds:
        timestamp = time.time() - age_seconds
        os.utime(path, (timestamp, timestamp))
    return path


def _run_runner(
    download_dir: Path,
    *args: str,
    input_text: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env["C_RUNNER_MAX_AGE_SECONDS"] = "1"
    env.pop("NO_COLOR", None)
    env.pop("C_RUNNER_WAIT_CHILD", None)
    env.pop("C_RUNNER_WATCH_CHILD", None)
    env.pop("C_RUNNER_SELF_COPY", None)
    env.pop("C_RUNNER_ORIGINAL", None)
    env.pop("C_RUNNER_TEMP_COPY", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [str(RUNNER), *args],
        cwd=REPO_ROOT,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def test_fresh_script_passes_freshness_check_in_dry_run(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "fresh_patch.sh",
        _valid_preflight_body(f": > {marker}"),
    )

    result = _run_runner(download_dir, "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert "Patchscript ist frisch genug" in result.stdout
    assert "DRY-RUN OK" in result.stdout


def test_old_script_without_confirmation_is_refused_and_left_in_place(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "old_patch.sh",
        _valid_preflight_body(f": > {marker}", patch_id="PATCHHARBOR.FRESHNESS.OLD.NO"),
        age_seconds=10,
    )

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 2, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "old_patch.sh").exists()
    assert not (download_dir / "failed" / "old_patch.sh").exists()
    assert "Das Patchscript ist älter als" in result.stdout
    assert "Trotzdem ausführen? [y/N]" in result.stdout
    assert "Abgebrochen. Das ältere Script wurde nicht ausgeführt und bleibt in Downloads." in result.stdout


def test_old_script_after_confirmation_executes_and_moves_to_done(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "old_confirmed_patch.sh",
        _valid_preflight_body(f": > {marker}", patch_id="PATCHHARBOR.FRESHNESS.OLD.YES"),
        age_seconds=10,
    )

    result = _run_runner(download_dir, input_text="y\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not script.exists()
    assert (download_dir / "done" / "old_confirmed_patch.sh").exists()
    assert not (download_dir / "failed" / "old_confirmed_patch.sh").exists()
    assert "Das Patchscript ist älter als" in result.stdout
    assert "Bestätigung erhalten. c führt das ältere Script aus." in result.stdout


def test_old_script_accepts_german_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "old_ja_patch.sh",
        _valid_preflight_body(f": > {marker}", patch_id="PATCHHARBOR.FRESHNESS.OLD.JA"),
        age_seconds=10,
    )

    result = _run_runner(download_dir, input_text="ja\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not script.exists()
    assert (download_dir / "done" / "old_ja_patch.sh").exists()
    assert "Bestätigung erhalten. c führt das ältere Script aus." in result.stdout


def test_old_zip_without_confirmation_is_refused_and_archive_is_left_in_place(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    archive = _write_zip(
        download_dir,
        "old_archive.zip",
        "old_archive_patch.sh",
        _valid_preflight_body(f": > {marker}", patch_id="PATCHHARBOR.FRESHNESS.OLD.ZIP"),
        age_seconds=10,
    )

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 2, result.stdout + result.stderr
    assert archive.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "old_archive.zip").exists()
    assert not (download_dir / "failed" / "old_archive.zip").exists()
    assert "Patcharchive:" in result.stdout
    assert "Patchscript:" in result.stdout
    assert "Das Patchscript ist älter als" in result.stdout
    assert "Abgebrochen. Das ältere Script wurde nicht ausgeführt und bleibt in Downloads." in result.stdout


def test_old_script_in_wait_child_is_refused_without_prompt(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "old_wait_child_patch.sh",
        _valid_preflight_body(f": > {marker}", patch_id="PATCHHARBOR.FRESHNESS.WAIT.CHILD"),
        age_seconds=10,
    )

    result = _run_runner(download_dir, str(script), env_extra={"C_RUNNER_WAIT_CHILD": "1"})

    assert result.returncode == 2, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert "Warte-Kindprozess verweigert altes Patchscript" in result.stdout
    assert "Trotzdem ausführen? [y/N]" not in result.stdout


def test_freshness_parity_tests_do_not_store_private_local_values() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    forbidden = [
        "/home/" + "christian",
        "christian" + "@",
        "christian.doehn" + "@" + "gmail.com",
        "Think" + "Pad",
        "~/" + "Projekte",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text, value
