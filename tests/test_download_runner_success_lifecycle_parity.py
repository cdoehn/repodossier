from __future__ import annotations

import pytest
import hashlib
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


def _metadata(*, patch_id: str = "PATCHHARBOR.SUCCESS.PARITY") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Success parity","commit":"Success parity"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _body(commands: str, *, patch_id: str = "PATCHHARBOR.SUCCESS.PARITY") -> str:
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def test_successful_script_executes_moves_to_done_updates_ledger_and_keeps_log(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "success_patch.sh",
        _body(f"echo success-visible-output\n: > {marker}", patch_id="PATCHHARBOR.SUCCESS.SCRIPT"),
    )
    original_hash = _sha256(script)

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not script.exists()
    moved = download_dir / "done" / "success_patch.sh"
    assert moved.exists()
    assert not (download_dir / "failed" / "success_patch.sh").exists()
    ledger = download_dir / "done" / ".applied_patch_hashes.tsv"
    assert ledger.exists()
    ledger_text = ledger.read_text(encoding="utf-8")
    assert original_hash in ledger_text
    assert "success_patch.sh" in ledger_text
    assert str(moved) in ledger_text
    logs = _logs(download_dir)
    assert len(logs) == 1
    assert "success-visible-output" in logs[0].read_text(encoding="utf-8")
    assert "Patch erfolgreich." in result.stdout
    assert "Applied-Ledger aktualisiert" in result.stdout


@pytest.mark.skip(reason=DISPLAY_ONLY_SKIP_REASON)
def test_success_banner_is_final_line_and_green_bold(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    _write_script(
        download_dir,
        "success_banner_patch.sh",
        _body(f": > {marker}", patch_id="PATCHHARBOR.SUCCESS.BANNER"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    last_line = result.stdout.rstrip().splitlines()[-1]
    plain = _strip_ansi(last_line)
    assert plain.startswith("ERFOLG  ERFOLG  ERFOLG")
    assert "ERFOLG" in plain
    assert "\x1b[0;32m" in last_line
    assert "\x1b[1m" in last_line


@pytest.mark.skip(reason=DISPLAY_ONLY_SKIP_REASON)
def test_success_with_progress_context_false_does_not_print_roadmap_context_block(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    _write_script(
        download_dir,
        "no_context_success_patch.sh",
        _body(f": > {marker}", patch_id="PATCHHARBOR.SUCCESS.NO_CONTEXT"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert "Dieses Patchscript wünscht keinen Progress Context." in result.stdout
    assert "Roadmap / Milestone" not in result.stdout
    assert "c · Progress Context" not in result.stdout


def test_successful_zip_executes_inner_script_and_moves_original_archive_to_done(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "zip_marker"
    archive = _write_zip(
        download_dir,
        "success_archive.zip",
        "success_archive_patch.sh",
        _body(f"echo zip-success\n: > {marker}", patch_id="PATCHHARBOR.SUCCESS.ZIP"),
    )
    original_hash = _sha256(archive)

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not archive.exists()
    moved = download_dir / "done" / "success_archive.zip"
    assert moved.exists()
    assert not (download_dir / "failed" / "success_archive.zip").exists()
    ledger_text = (download_dir / "done" / ".applied_patch_hashes.tsv").read_text(encoding="utf-8")
    assert original_hash in ledger_text
    assert "success_archive.zip" in ledger_text
    assert "Patcharchive:" in result.stdout
    assert "Patchscript:" in result.stdout
    assert "zip-success" in result.stdout


def test_explicit_script_path_success_does_not_select_newer_download(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    chosen_marker = tmp_path / "chosen_marker"
    newer_marker = tmp_path / "newer_marker"
    chosen = _write_script(
        download_dir,
        "chosen_patch.sh",
        _body(f"echo chosen\n: > {chosen_marker}", patch_id="PATCHHARBOR.SUCCESS.EXPLICIT.CHOSEN"),
        age_seconds=10,
    )
    newer = _write_script(
        download_dir,
        "newer_patch.sh",
        _body(f"echo newer\n: > {newer_marker}", patch_id="PATCHHARBOR.SUCCESS.EXPLICIT.NEWER"),
    )

    result = _run_runner(download_dir, str(chosen))

    assert result.returncode == 0, result.stdout + result.stderr
    assert chosen_marker.exists()
    assert not newer_marker.exists()
    assert not chosen.exists()
    assert newer.exists()
    assert (download_dir / "done" / "chosen_patch.sh").exists()
    assert "chosen" in result.stdout
    assert "newer" not in result.stdout


def test_success_lifecycle_does_not_leak_internal_runner_env_to_patch_script(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    env_marker = tmp_path / "runner_env"
    _write_script(
        download_dir,
        "env_success_patch.sh",
        _body(f"env | grep '^C_RUNNER_' > {env_marker} || true", patch_id="PATCHHARBOR.SUCCESS.ENV"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (download_dir / "done" / "env_success_patch.sh").exists()
    assert env_marker.read_text(encoding="utf-8") == ""


def test_success_lifecycle_parity_tests_do_not_store_private_local_values() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    forbidden = [
        "/home/" + "exampleuser",
        "user" + "@",
        "example.user" + "@" + "example.invalid",
        "Example" + "Laptop",
        "~/" + "Projects",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text, value
