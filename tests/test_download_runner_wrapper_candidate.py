from __future__ import annotations

import os
import subprocess
import time
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"
CANDIDATE = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch_patchharbor_candidate.sh"


def _metadata(*, patch_id: str = "PATCHHARBOR.WRAPPER.CANDIDATE") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Wrapper candidate","commit":"Wrapper candidate"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _body(commands: str, *, patch_id: str = "PATCHHARBOR.WRAPPER.CANDIDATE") -> str:
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


def _run_command(
    command: tuple[str, ...],
    download_dir: Path,
    *,
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
        [*command],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _success_contract(command: tuple[str, ...], base_dir: Path) -> dict[str, object]:
    download_dir = base_dir / "Downloads"
    download_dir.mkdir(parents=True)
    marker = base_dir / "marker"
    _write_script(
        download_dir,
        "candidate_success_patch.sh",
        _body(f"echo candidate-success\n: > {marker}", patch_id="PATCHHARBOR.CANDIDATE.SUCCESS"),
    )

    result = _run_command(command, download_dir)

    return {
        "returncode": result.returncode,
        "marker_exists": marker.exists(),
        "done_exists": (download_dir / "done" / "candidate_success_patch.sh").exists(),
        "failed_exists": (download_dir / "failed" / "candidate_success_patch.sh").exists(),
        "has_success_text": "Patch erfolgreich." in result.stdout,
        "has_success_output": "candidate-success" in result.stdout,
    }


def _zip_contract(command: tuple[str, ...], base_dir: Path) -> dict[str, object]:
    download_dir = base_dir / "Downloads"
    download_dir.mkdir(parents=True)
    marker = base_dir / "marker"
    _write_zip(
        download_dir,
        "candidate_archive.zip",
        "candidate_archive_patch.sh",
        _body(f"echo candidate-zip\n: > {marker}", patch_id="PATCHHARBOR.CANDIDATE.ZIP"),
    )

    result = _run_command(command, download_dir)

    return {
        "returncode": result.returncode,
        "marker_exists": marker.exists(),
        "done_exists": (download_dir / "done" / "candidate_archive.zip").exists(),
        "failed_exists": (download_dir / "failed" / "candidate_archive.zip").exists(),
        "has_archive_text": "Patcharchive:" in result.stdout,
        "has_script_text": "Patchscript:" in result.stdout,
    }


def _metadata_reject_contract(command: tuple[str, ...], base_dir: Path) -> dict[str, object]:
    download_dir = base_dir / "Downloads"
    download_dir.mkdir(parents=True)
    marker = base_dir / "marker"
    _write_script(
        download_dir,
        "candidate_bad_metadata_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.CANDIDATE.BAD","title":"Bad"}\n'
        '# repodossier-meta: {"type":"display","progress_context":false}\n'
        f": > {marker}\n",
    )

    result = _run_command(command, download_dir)

    return {
        "returncode": result.returncode,
        "marker_exists": marker.exists(),
        "source_still_exists": (download_dir / "candidate_bad_metadata_patch.sh").exists(),
        "has_invalid_text": "Metadata invalid:" in result.stdout,
        "has_no_execution": "▶ c: Ausführung" not in result.stdout,
    }


def test_candidate_script_exists_and_is_not_the_productive_runner() -> None:
    assert CANDIDATE.exists()
    assert os.access(CANDIDATE, os.X_OK)
    assert CANDIDATE != RUNNER
    assert RUNNER.exists()


def test_candidate_default_mode_preserves_success_contract(tmp_path: Path) -> None:
    baseline = _success_contract((str(RUNNER),), tmp_path / "baseline")
    candidate = _success_contract((str(CANDIDATE),), tmp_path / "candidate")
    assert candidate == baseline


def test_candidate_default_mode_preserves_zip_contract(tmp_path: Path) -> None:
    baseline = _zip_contract((str(RUNNER),), tmp_path / "baseline")
    candidate = _zip_contract((str(CANDIDATE),), tmp_path / "candidate")
    assert candidate == baseline


def test_candidate_default_mode_preserves_metadata_rejection_contract(tmp_path: Path) -> None:
    baseline = _metadata_reject_contract((str(RUNNER),), tmp_path / "baseline")
    candidate = _metadata_reject_contract((str(CANDIDATE),), tmp_path / "candidate")
    assert candidate == baseline


def test_candidate_patchharbor_mode_requires_explicit_path_for_now(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    result = _run_command(
        (str(CANDIDATE),),
        download_dir,
        env_extra={"PATCHHARBOR_DOWNLOAD_RUNNER_CANDIDATE_MODE": "patchharbor"},
    )
    assert result.returncode == 64
    assert "requires an explicit patch script path" in result.stderr


def test_candidate_rejects_unknown_mode_without_running_downloads(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    _write_script(
        download_dir,
        "unknown_mode_patch.sh",
        _body(f": > {marker}", patch_id="PATCHHARBOR.CANDIDATE.UNKNOWN.MODE"),
    )

    result = _run_command(
        (str(CANDIDATE),),
        download_dir,
        env_extra={"PATCHHARBOR_DOWNLOAD_RUNNER_CANDIDATE_MODE": "unknown"},
    )

    assert result.returncode == 64
    assert not marker.exists()
    assert "Unsupported PATCHHARBOR_DOWNLOAD_RUNNER_CANDIDATE_MODE" in result.stderr


def test_candidate_file_contains_future_patchharbor_path_but_productive_runner_does_not() -> None:
    candidate_text = CANDIDATE.read_text(encoding="utf-8")
    runner_text = RUNNER.read_text(encoding="utf-8")
    future_wrapper = "exec " + "patchharbor " + "run-script"
    assert future_wrapper in candidate_text
    assert future_wrapper not in runner_text


def test_candidate_tests_do_not_store_private_local_values() -> None:
    checked = [
        CANDIDATE,
        Path(__file__),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
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
