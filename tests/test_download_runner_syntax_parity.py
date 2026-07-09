from __future__ import annotations

import os
import subprocess
import time
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _metadata(*, patch_id: str = "PATCHHARBOR.SYNTAX.PARITY") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Syntax parity","commit":"Syntax parity"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _broken_body(*, patch_id: str = "PATCHHARBOR.SYNTAX.PARITY") -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"{_metadata(patch_id=patch_id)}\n"
        "set -euo pipefail\n"
        "print_footer() {\n"
        "  echo footer\n"
        "}\n"
        "python3 -m py_compile scripts/dev/validate_patch_metadata.py\n"
        "if true; then\n"
        "echo broken\n"
    )


def _write_script(download_dir: Path, name: str, body: str) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    timestamp = time.time()
    os.utime(path, (timestamp, timestamp))
    return path


def _write_zip(download_dir: Path, name: str, script_name: str, body: str) -> Path:
    path = download_dir / name
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(script_name, body)
    timestamp = time.time()
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
    env["C_RUNNER_MAX_AGE_SECONDS"] = "3600"
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


def test_syntax_failure_moves_script_to_failed_and_does_not_execute(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "broken_syntax_patch.sh",
        _broken_body(patch_id="PATCHHARBOR.SYNTAX.NORMAL") + f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode != 0
    assert not script.exists()
    assert not marker.exists()
    assert (download_dir / "failed" / "broken_syntax_patch.sh").exists()
    assert not (download_dir / "done" / "broken_syntax_patch.sh").exists()
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout
    assert "Exit-Code:" in result.stdout
    assert "Script verschoben nach:" in result.stdout
    assert "Logfile bleibt in Downloads:" in result.stdout


def test_syntax_failure_in_dry_run_keeps_script_in_downloads(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "dry_run_broken_syntax_patch.sh",
        _broken_body(patch_id="PATCHHARBOR.SYNTAX.DRYRUN") + f": > {marker}\n",
    )

    result = _run_runner(download_dir, "--dry-run")

    assert result.returncode != 0
    assert script.exists()
    assert not marker.exists()
    assert not (download_dir / "failed" / "dry_run_broken_syntax_patch.sh").exists()
    assert not (download_dir / "done" / "dry_run_broken_syntax_patch.sh").exists()
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout
    assert "Dry-run: Script bleibt unverändert in Downloads:" in result.stdout
    assert "DRY-RUN OK" not in result.stdout


def test_syntax_failure_for_explicit_script_path_moves_that_script_to_failed(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "explicit_broken_syntax_patch.sh",
        _broken_body(patch_id="PATCHHARBOR.SYNTAX.EXPLICIT") + f": > {marker}\n",
    )

    result = _run_runner(download_dir, str(script))

    assert result.returncode != 0
    assert not script.exists()
    assert not marker.exists()
    assert (download_dir / "failed" / "explicit_broken_syntax_patch.sh").exists()
    assert "Patchscript:" in result.stdout
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout


def test_syntax_failure_inside_zip_moves_archive_to_failed_and_does_not_execute(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    archive = _write_zip(
        download_dir,
        "broken_syntax_archive.zip",
        "broken_syntax_archive_patch.sh",
        _broken_body(patch_id="PATCHHARBOR.SYNTAX.ZIP") + f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode != 0
    assert not archive.exists()
    assert not marker.exists()
    assert (download_dir / "failed" / "broken_syntax_archive.zip").exists()
    assert not (download_dir / "done" / "broken_syntax_archive.zip").exists()
    assert "Patcharchive:" in result.stdout
    assert "Patchscript:" in result.stdout
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout


def test_syntax_failure_inside_zip_in_dry_run_keeps_archive_in_downloads(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    archive = _write_zip(
        download_dir,
        "dry_run_broken_syntax_archive.zip",
        "dry_run_broken_syntax_archive_patch.sh",
        _broken_body(patch_id="PATCHHARBOR.SYNTAX.ZIP.DRYRUN") + f": > {marker}\n",
    )

    result = _run_runner(download_dir, "--dry-run")

    assert result.returncode != 0
    assert archive.exists()
    assert not marker.exists()
    assert not (download_dir / "failed" / "dry_run_broken_syntax_archive.zip").exists()
    assert not (download_dir / "done" / "dry_run_broken_syntax_archive.zip").exists()
    assert "Patcharchive:" in result.stdout
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout
    assert "Dry-run: Script bleibt unverändert in Downloads:" in result.stdout


def test_syntax_failure_in_wait_child_moves_script_to_failed_without_prompt(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "wait_child_broken_syntax_patch.sh",
        _broken_body(patch_id="PATCHHARBOR.SYNTAX.WAIT.CHILD") + f": > {marker}\n",
    )

    result = _run_runner(download_dir, str(script), env_extra={"C_RUNNER_WAIT_CHILD": "1"})

    assert result.returncode != 0
    assert not script.exists()
    assert not marker.exists()
    assert (download_dir / "failed" / "wait_child_broken_syntax_patch.sh").exists()
    assert "Trotzdem ausführen? [y/N]" not in result.stdout
    assert "Trotzdem erneut ausführen? [y/N]" not in result.stdout
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout


def test_syntax_parity_tests_do_not_store_private_local_values() -> None:
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
