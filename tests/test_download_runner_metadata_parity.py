from __future__ import annotations

import os
import re
import subprocess
import time
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _metadata(*, patch_id: str = "PATCHHARBOR.METADATA.PARITY") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Metadata parity","commit":"Metadata parity"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _valid_preflight_body(commands: str, *, patch_id: str = "PATCHHARBOR.METADATA.PARITY") -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"{_metadata(patch_id=patch_id)}\n"
        "print_footer() {\n"
        "  echo footer\n"
        "}\n"
        f"{commands}\n"
        "python3 -m py_compile scripts/dev/validate_patch_metadata.py\n"
    )


def _write_script(download_dir: Path, name: str, body: str, *, age_seconds: int = 0) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    if age_seconds:
        timestamp = time.time() - age_seconds
        os.utime(path, (timestamp, timestamp))
    return path


def _write_zip(download_dir: Path, name: str, script_name: str, body: str) -> Path:
    path = download_dir / name
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(script_name, body)
    return path


def _run_runner(download_dir: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env.pop("NO_COLOR", None)
    env.pop("C_RUNNER_WAIT_CHILD", None)
    env.pop("C_RUNNER_WATCH_CHILD", None)
    env.pop("C_RUNNER_SELF_COPY", None)
    env.pop("C_RUNNER_ORIGINAL", None)
    env.pop("C_RUNNER_TEMP_COPY", None)
    return subprocess.run(
        [str(RUNNER), *args],
        cwd=REPO_ROOT,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def test_valid_metadata_with_progress_context_false_is_accepted_in_dry_run(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "valid_metadata_patch.sh",
        _valid_preflight_body(f": > {marker}"),
    )

    result = _run_runner(download_dir, "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert "Metadata OK" in result.stdout
    assert "Metadaten OK" in result.stdout
    assert "Dieses Patchscript wünscht keinen Progress Context." in result.stdout
    assert "DRY-RUN OK" in result.stdout
    # Current legacy runner contract: progress_context=false is accepted and logged.
    # Full context-panel suppression is a runner behavior change, not a metadata parity requirement.


def test_invalid_metadata_missing_commit_stops_before_execution(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "missing_commit_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.BAD","title":"Bad"}\n'
        '# repodossier-meta: {"type":"display","progress_context":false}\n'
        f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "missing_commit_patch.sh").exists()
    assert not (download_dir / "failed" / "missing_commit_patch.sh").exists()
    assert "Metadata invalid:" in result.stdout
    assert 'missing or invalid string field "commit"' in result.stdout
    assert "Metadatenprüfung fehlgeschlagen" in result.stdout


def test_display_progress_context_false_rejects_progress_metadata_before_execution(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "mixed_progress_context_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.MIXED","title":"Mixed","commit":"Mixed"}\n'
        '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"scripts/dev/patch-rules.md","start":1,"end":1}\n'
        '# repodossier-meta: {"type":"display","progress_context":false}\n'
        f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert "display progress_context=false must not be combined with progress metadata records" in result.stdout
    assert "Metadatenprüfung fehlgeschlagen" in result.stdout


def test_missing_progress_metadata_without_display_override_is_rejected(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "missing_progress_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.NO_PROGRESS","title":"No progress","commit":"No progress"}\n'
        f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert "missing required roadmap progress metadata record" in result.stdout
    assert "missing required milestone progress metadata record" in result.stdout


def test_invalid_progress_file_is_rejected_before_execution(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "bad_progress_file_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.BAD_FILE","title":"Bad file","commit":"Bad file"}\n'
        '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"docs/missing-example.md","start":1,"end":1}\n'
        '# repodossier-meta: {"type":"progress","panel":"milestone","status":"active","file":"docs/missing-example.md","start":1,"end":1}\n'
        f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert "file does not exist: docs/missing-example.md" in result.stdout
    assert "Metadatenprüfung fehlgeschlagen" in result.stdout


def test_invalid_metadata_inside_zip_stops_before_execution_and_keeps_archive(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    archive = _write_zip(
        download_dir,
        "bad_metadata_archive.zip",
        "bad_metadata_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.ZIP_BAD","title":"Zip bad"}\n'
        '# repodossier-meta: {"type":"display","progress_context":false}\n'
        f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10, result.stdout + result.stderr
    assert archive.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "bad_metadata_archive.zip").exists()
    assert not (download_dir / "failed" / "bad_metadata_archive.zip").exists()
    assert "Patcharchive:" in result.stdout
    assert "Metadata invalid:" in result.stdout
    assert 'missing or invalid string field "commit"' in result.stdout


def test_metadata_parity_tests_do_not_store_private_local_values() -> None:
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
