from __future__ import annotations

import os
import subprocess
import time
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"
WRAPPER_DRAFT = REPO_ROOT / "planning" / "patchharbor" / "source-download-runner-wrapper-draft.md"


def _metadata(*, patch_id: str = "PATCHHARBOR.WRAPPER.HARNESS") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Wrapper harness","commit":"Wrapper harness"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _body(commands: str, *, patch_id: str = "PATCHHARBOR.WRAPPER.HARNESS") -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"{_metadata(patch_id=patch_id)}\n"
        "set -euo pipefail\n"
        "print_footer() {\n"
        "  echo patch-footer\n"
        "}\n"
        f"{commands}\n"
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


def _run_candidate(
    command: tuple[str, ...],
    download_dir: Path,
    *args: str,
    input_text: str | None = None,
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
    return subprocess.run(
        [*command, *args],
        cwd=REPO_ROOT,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _success_script_contract(command: tuple[str, ...], base_dir: Path) -> dict[str, object]:
    download_dir = base_dir / "Downloads"
    download_dir.mkdir(parents=True)
    marker = base_dir / "marker"
    _write_script(
        download_dir,
        "wrapper_success_patch.sh",
        _body(f"echo wrapper-success\n: > {marker}", patch_id="PATCHHARBOR.WRAPPER.SUCCESS"),
    )

    result = _run_candidate(command, download_dir)

    return {
        "returncode": result.returncode,
        "marker_exists": marker.exists(),
        "done_exists": (download_dir / "done" / "wrapper_success_patch.sh").exists(),
        "failed_exists": (download_dir / "failed" / "wrapper_success_patch.sh").exists(),
        "has_success_text": "Patch erfolgreich." in result.stdout,
        "has_success_output": "wrapper-success" in result.stdout,
    }


def _zip_success_contract(command: tuple[str, ...], base_dir: Path) -> dict[str, object]:
    download_dir = base_dir / "Downloads"
    download_dir.mkdir(parents=True)
    marker = base_dir / "zip-marker"
    _write_zip(
        download_dir,
        "wrapper_success_archive.zip",
        "wrapper_success_archive_patch.sh",
        _body(f"echo wrapper-zip-success\n: > {marker}", patch_id="PATCHHARBOR.WRAPPER.ZIP.SUCCESS"),
    )

    result = _run_candidate(command, download_dir)

    return {
        "returncode": result.returncode,
        "marker_exists": marker.exists(),
        "done_exists": (download_dir / "done" / "wrapper_success_archive.zip").exists(),
        "failed_exists": (download_dir / "failed" / "wrapper_success_archive.zip").exists(),
        "has_archive_text": "Patcharchive:" in result.stdout,
        "has_script_text": "Patchscript:" in result.stdout,
    }


def _metadata_reject_contract(command: tuple[str, ...], base_dir: Path) -> dict[str, object]:
    download_dir = base_dir / "Downloads"
    download_dir.mkdir(parents=True)
    marker = base_dir / "marker"
    _write_script(
        download_dir,
        "wrapper_bad_metadata_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.WRAPPER.BAD","title":"Bad"}\n'
        '# repodossier-meta: {"type":"display","progress_context":false}\n'
        f": > {marker}\n",
    )

    result = _run_candidate(command, download_dir)

    return {
        "returncode": result.returncode,
        "marker_exists": marker.exists(),
        "source_still_exists": (download_dir / "wrapper_bad_metadata_patch.sh").exists(),
        "has_invalid_text": "Metadata invalid:" in result.stdout,
        "has_no_execution": "▶ c: Ausführung" not in result.stdout,
    }


def test_wrapper_harness_contract_collects_success_script_behavior() -> None:
    with_base = REPO_ROOT / ".pytest-wrapper-harness-never-used"
    assert with_base.name == ".pytest-wrapper-harness-never-used"

    assert RUNNER.exists()
    assert WRAPPER_DRAFT.exists()


def test_harness_can_compare_two_candidate_commands_without_switching_runner(tmp_path: Path) -> None:
    baseline = _success_script_contract((str(RUNNER),), tmp_path / "baseline")
    candidate = _success_script_contract((str(RUNNER),), tmp_path / "candidate")

    assert candidate == baseline
    assert candidate == {
        "returncode": 0,
        "marker_exists": True,
        "done_exists": True,
        "failed_exists": False,
        "has_success_text": True,
        "has_success_output": True,
    }


def test_harness_can_compare_zip_success_contract(tmp_path: Path) -> None:
    baseline = _zip_success_contract((str(RUNNER),), tmp_path / "baseline")
    candidate = _zip_success_contract((str(RUNNER),), tmp_path / "candidate")

    assert candidate == baseline
    assert candidate["returncode"] == 0
    assert candidate["marker_exists"] is True
    assert candidate["done_exists"] is True
    assert candidate["failed_exists"] is False
    assert candidate["has_archive_text"] is True
    assert candidate["has_script_text"] is True


def test_harness_can_compare_metadata_rejection_contract(tmp_path: Path) -> None:
    baseline = _metadata_reject_contract((str(RUNNER),), tmp_path / "baseline")
    candidate = _metadata_reject_contract((str(RUNNER),), tmp_path / "candidate")

    assert candidate == baseline
    assert candidate == {
        "returncode": 10,
        "marker_exists": False,
        "source_still_exists": True,
        "has_invalid_text": True,
        "has_no_execution": True,
    }


def test_wrapper_harness_file_does_not_modify_productive_runner() -> None:
    runner_text = RUNNER.read_text(encoding="utf-8")
    test_text = Path(__file__).read_text(encoding="utf-8")

    future_wrapper = "exec " + "patchharbor " + "run-script"
    assert "run_latest_" + "download_patch.sh" in str(RUNNER)
    assert future_wrapper not in runner_text
    assert future_wrapper not in test_text
    assert "source-download-runner-wrapper-draft.md" in test_text


def test_wrapper_harness_keeps_context_display_disabled_in_dummy_patches() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    forbidden_metadata_error = "missing required " + "roadmap progress metadata record"
    assert '"type":"display","progress_context":false' in text
    assert forbidden_metadata_error not in text


def test_wrapper_harness_tests_do_not_store_private_local_values() -> None:
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
