"""Tests for the c download patch runner."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _write_script(
    download_dir: Path,
    name: str,
    body: str,
    *,
    age_seconds: int = 0,
) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)

    if age_seconds:
        timestamp = time.time() - age_seconds
        os.utime(path, (timestamp, timestamp))

    return path


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

    _write_script(
        download_dir,
        "older_patch.sh",
        f"#!/usr/bin/env bash\necho old\n: > {old_marker}\n",
        age_seconds=30,
    )
    latest = _write_script(
        download_dir,
        "latest_patch.sh",
        f"#!/usr/bin/env bash\necho latest\n: > {latest_marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert latest_marker.exists()
    assert not old_marker.exists()
    assert not latest.exists()
    assert (download_dir / "done" / "latest_patch.sh").exists()
    assert (download_dir / "older_patch.sh").exists()
    assert "latest" in result.stdout
    assert "\x1b[" in result.stdout
    assert "c · RepoDossier Download Patch Runner" in result.stdout

    logs = _logs(download_dir)
    assert len(logs) == 1
    assert "latest" in logs[0].read_text(encoding="utf-8")


def test_c_runner_moves_failed_script_to_failed_and_keeps_log(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    failing = _write_script(
        download_dir,
        "failing_patch.sh",
        "#!/usr/bin/env bash\necho before-fail\nexit 7\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 7
    assert not failing.exists()
    assert (download_dir / "failed" / "failing_patch.sh").exists()
    assert "Patch fehlgeschlagen" in result.stdout

    logs = _logs(download_dir)
    assert len(logs) == 1
    assert "before-fail" in logs[0].read_text(encoding="utf-8")


def test_c_runner_refuses_old_script_without_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    old_script = _write_script(
        download_dir,
        "old_patch.sh",
        f"#!/usr/bin/env bash\n: > {marker}\n",
        age_seconds=61 * 60,
    )

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 2
    assert old_script.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "old_patch.sh").exists()
    assert not (download_dir / "failed" / "old_patch.sh").exists()
    assert "älter" in result.stdout
    assert "Trotzdem ausführen" in result.stdout

    logs = _logs(download_dir)
    assert len(logs) == 1


def test_c_runner_executes_old_script_after_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    old_script = _write_script(
        download_dir,
        "old_confirmed_patch.sh",
        f"#!/usr/bin/env bash\n: > {marker}\n",
        age_seconds=61 * 60,
    )

    result = _run_runner(download_dir, input_text="y\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not old_script.exists()
    assert (download_dir / "done" / "old_confirmed_patch.sh").exists()
    assert "Bestätigung erhalten" in result.stdout


def test_c_runner_failed_syntax_moves_script_to_failed(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    broken = _write_script(
        download_dir,
        "broken_patch.sh",
        "#!/usr/bin/env bash\nif true; then\necho broken\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode != 0
    assert not broken.exists()
    assert (download_dir / "failed" / "broken_patch.sh").exists()
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout

    logs = _logs(download_dir)
    assert len(logs) == 1
    assert "Syntaxprüfung" in logs[0].read_text(encoding="utf-8")
