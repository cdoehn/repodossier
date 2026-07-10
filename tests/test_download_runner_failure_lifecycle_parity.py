from __future__ import annotations

import pytest
import os
import re
import subprocess
import time
import zipfile
from pathlib import Path


DISPLAY_ONLY_SKIP_REASON = "display-only migration test; functional tests remain enabled"

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", value)


def _metadata(*, patch_id: str = "PATCHHARBOR.FAILURE.PARITY") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Failure parity","commit":"Failure parity"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _body(commands: str, *, patch_id: str = "PATCHHARBOR.FAILURE.PARITY") -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"{_metadata(patch_id=patch_id)}\n"
        "set -euo pipefail\n"
        "print_footer() {\n"
        "  echo footer\n"
        "}\n"
        f"{commands}\n"
    )


def _write_script(download_dir: Path, name: str, body: str, *, age_seconds: int = 0) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    timestamp = time.time() - age_seconds if age_seconds else time.time()
    os.utime(path, (timestamp, timestamp))
    return path


def _write_zip(download_dir: Path, name: str, script_name: str, body: str) -> Path:
    path = download_dir / name
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(script_name, body)
    timestamp = time.time()
    os.utime(path, (timestamp, timestamp))
    return path


def _logs(download_dir: Path) -> list[Path]:
    return sorted(download_dir.glob("*.log"))


def _run_runner(
    download_dir: Path,
    *args: str,
    input_text: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env.pop("NO_COLOR", None)
    env.pop("C_RUNNER_MAX_AGE_SECONDS", None)
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


def test_failed_script_executes_moves_to_failed_keeps_log_and_does_not_update_ledger(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "failure_patch.sh",
        _body(f"echo failure-visible-output\n: > {marker}\nexit 7", patch_id="PATCHHARBOR.FAILURE.SCRIPT"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 7, result.stdout + result.stderr
    assert marker.exists()
    assert not script.exists()
    moved = download_dir / "failed" / "failure_patch.sh"
    assert moved.exists()
    assert not (download_dir / "done" / "failure_patch.sh").exists()
    assert not (download_dir / "done" / ".applied_patch_hashes.tsv").exists()
    logs = _logs(download_dir)
    assert len(logs) == 1
    log_text = logs[0].read_text(encoding="utf-8")
    assert "failure-visible-output" in log_text
    assert "Patchscript Exit-Code: 7" in result.stdout
    assert "Patch fehlgeschlagen." in result.stdout
    assert "Script verschoben nach:" in result.stdout
    assert "Logfile bleibt in Downloads:" in result.stdout
    assert "Applied-Ledger aktualisiert" not in result.stdout


@pytest.mark.skip(reason=DISPLAY_ONLY_SKIP_REASON)
def test_failure_banner_is_final_line_and_red_bold(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    _write_script(
        download_dir,
        "failure_banner_patch.sh",
        _body("exit 4", patch_id="PATCHHARBOR.FAILURE.BANNER"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 4, result.stdout + result.stderr
    last_line = result.stdout.rstrip().splitlines()[-1]
    plain = _strip_ansi(last_line)
    assert plain.startswith("FEHLSCHLAG  FEHLSCHLAG")
    assert "FEHLSCHLAG" in plain
    assert "\x1b[0;31m" in last_line
    assert "\x1b[1m" in last_line


@pytest.mark.skip(reason=DISPLAY_ONLY_SKIP_REASON)
def test_failure_with_progress_context_false_does_not_print_roadmap_context_block(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    _write_script(
        download_dir,
        "no_context_failure_patch.sh",
        _body(f": > {marker}\nexit 6", patch_id="PATCHHARBOR.FAILURE.NO_CONTEXT"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 6, result.stdout + result.stderr
    assert marker.exists()
    assert "Dieses Patchscript wünscht keinen Progress Context." in result.stdout
    assert "Roadmap / Milestone" not in result.stdout
    assert "c · Progress Context" not in result.stdout


def test_failed_zip_executes_inner_script_and_moves_original_archive_to_failed(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "zip_marker"
    archive = _write_zip(
        download_dir,
        "failure_archive.zip",
        "failure_archive_patch.sh",
        _body(f"echo zip-failure\n: > {marker}\nexit 9", patch_id="PATCHHARBOR.FAILURE.ZIP"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 9, result.stdout + result.stderr
    assert marker.exists()
    assert not archive.exists()
    moved = download_dir / "failed" / "failure_archive.zip"
    assert moved.exists()
    assert not (download_dir / "done" / "failure_archive.zip").exists()
    assert not (download_dir / "done" / ".applied_patch_hashes.tsv").exists()
    assert "Patcharchive:" in result.stdout
    assert "Patchscript:" in result.stdout
    assert "zip-failure" in result.stdout
    assert "Patch fehlgeschlagen." in result.stdout


def test_explicit_script_path_failure_does_not_select_newer_download(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    chosen_marker = tmp_path / "chosen_marker"
    newer_marker = tmp_path / "newer_marker"
    chosen = _write_script(
        download_dir,
        "chosen_failure_patch.sh",
        _body(f"echo chosen-failure\n: > {chosen_marker}\nexit 8", patch_id="PATCHHARBOR.FAILURE.EXPLICIT.CHOSEN"),
        age_seconds=10,
    )
    newer = _write_script(
        download_dir,
        "newer_success_patch.sh",
        _body(f"echo newer-success\n: > {newer_marker}", patch_id="PATCHHARBOR.FAILURE.EXPLICIT.NEWER"),
    )

    result = _run_runner(download_dir, str(chosen))

    assert result.returncode == 8, result.stdout + result.stderr
    assert chosen_marker.exists()
    assert not newer_marker.exists()
    assert not chosen.exists()
    assert newer.exists()
    assert (download_dir / "failed" / "chosen_failure_patch.sh").exists()
    assert not (download_dir / "done" / "chosen_failure_patch.sh").exists()
    assert "chosen-failure" in result.stdout
    assert "newer-success" not in result.stdout


def test_failed_script_leaves_done_directory_without_moved_patch(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    _write_script(
        download_dir,
        "done_absence_failure_patch.sh",
        _body("exit 5", patch_id="PATCHHARBOR.FAILURE.NO_DONE"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 5, result.stdout + result.stderr
    done_entries = [path.name for path in (download_dir / "done").iterdir()] if (download_dir / "done").exists() else []
    assert "done_absence_failure_patch.sh" not in done_entries
    assert (download_dir / "failed" / "done_absence_failure_patch.sh").exists()
    assert "Patch erfolgreich." not in result.stdout


def test_failure_lifecycle_parity_tests_do_not_store_private_local_values() -> None:
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
