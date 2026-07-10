from __future__ import annotations

import hashlib
import os
import subprocess
import time
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _metadata(*, patch_id: str = "PATCHHARBOR.REPEAT.PARITY") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Repeat parity","commit":"Repeat parity"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _valid_body(commands: str, *, patch_id: str = "PATCHHARBOR.REPEAT.PARITY") -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"{_metadata(patch_id=patch_id)}\n"
        "set -euo pipefail\n"
        "print_footer() {\n"
        "  echo footer\n"
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


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ledger(done_dir: Path, artifact: Path) -> Path:
    done_dir.mkdir(parents=True, exist_ok=True)
    ledger = done_dir / ".applied_patch_hashes.tsv"
    ledger.write_text(f"{_hash(artifact)}\t2026-01-01T00:00:00+00:00\t{artifact.name}\t{done_dir / artifact.name}\n", encoding="utf-8")
    return ledger


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


def test_repeated_script_from_ledger_without_confirmation_is_refused_and_left_in_place(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "repeat_patch.sh",
        _valid_body(f": > {marker}", patch_id="PATCHHARBOR.REPEAT.LEDGER.NO"),
    )
    _ledger(download_dir / "done", script)

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 3, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "repeat_patch.sh").exists()
    assert not (download_dir / "failed" / "repeat_patch.sh").exists()
    assert "Dieses Patchscript wurde bereits erfolgreich angewendet." in result.stdout
    assert "Trotzdem erneut ausführen? [y/N]" in result.stdout
    assert "Abgebrochen. Bereits angewendetes Script wurde nicht erneut ausgeführt." in result.stdout


def test_repeated_script_from_ledger_after_confirmation_executes_and_moves_to_done(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "repeat_confirmed_patch.sh",
        _valid_body(f": > {marker}", patch_id="PATCHHARBOR.REPEAT.LEDGER.YES"),
    )
    _ledger(download_dir / "done", script)

    result = _run_runner(download_dir, input_text="y\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not script.exists()
    assert (download_dir / "done" / "repeat_confirmed_patch.sh").exists()
    assert "Bestätigung erhalten. c führt das bereits angewendete Script erneut aus." in result.stdout
    assert "Patch erfolgreich." in result.stdout


def test_repeated_script_accepts_german_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "repeat_ja_patch.sh",
        _valid_body(f": > {marker}", patch_id="PATCHHARBOR.REPEAT.LEDGER.JA"),
    )
    _ledger(download_dir / "done", script)

    result = _run_runner(download_dir, input_text="ja\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not script.exists()
    assert (download_dir / "done" / "repeat_ja_patch.sh").exists()
    assert "Bestätigung erhalten. c führt das bereits angewendete Script erneut aus." in result.stdout


def test_repeated_script_can_be_detected_from_existing_done_file_without_ledger(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    done_dir = download_dir / "done"
    done_dir.mkdir(parents=True)
    marker = tmp_path / "marker"
    body = _valid_body(f": > {marker}", patch_id="PATCHHARBOR.REPEAT.DONEFILE")
    done_file = done_dir / "already_done_patch.sh"
    done_file.write_text(body, encoding="utf-8")
    done_file.chmod(0o755)
    script = _write_script(download_dir, "already_done_patch.sh", body)

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 3, result.stdout + result.stderr
    assert script.exists()
    assert done_file.exists()
    assert not marker.exists()
    assert "Dieses Patchscript wurde bereits erfolgreich angewendet." in result.stdout
    assert "Fundstelle: done-file" in result.stdout


def test_repeated_zip_from_ledger_without_confirmation_is_refused_and_archive_stays(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    archive = _write_zip(
        download_dir,
        "repeat_archive.zip",
        "repeat_archive_patch.sh",
        _valid_body(f": > {marker}", patch_id="PATCHHARBOR.REPEAT.ZIP.NO"),
    )
    _ledger(download_dir / "done", archive)

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 3, result.stdout + result.stderr
    assert archive.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "repeat_archive.zip").exists()
    assert not (download_dir / "failed" / "repeat_archive.zip").exists()
    assert "Patcharchive:" in result.stdout
    assert "Dieses Patchscript wurde bereits erfolgreich angewendet." in result.stdout
    assert "Abgebrochen. Bereits angewendetes Script wurde nicht erneut ausgeführt." in result.stdout


def test_repeated_script_in_wait_child_is_refused_without_prompt(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "repeat_wait_child_patch.sh",
        _valid_body(f": > {marker}", patch_id="PATCHHARBOR.REPEAT.WAIT.CHILD"),
    )
    _ledger(download_dir / "done", script)

    result = _run_runner(download_dir, str(script), env_extra={"C_RUNNER_WAIT_CHILD": "1"})

    assert result.returncode == 3, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert "Dieses Patchscript wurde bereits erfolgreich angewendet." in result.stdout
    assert "Trotzdem erneut ausführen? [y/N]" not in result.stdout


def test_repeat_parity_tests_do_not_store_private_local_values() -> None:
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
