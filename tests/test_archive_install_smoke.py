from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_enabled() -> bool:
    return os.environ.get("REPODOSSIER_RUN_INSTALL_SMOKE") == "1"


@pytest.mark.skipif(not _run_enabled(), reason="set REPODOSSIER_RUN_INSTALL_SMOKE=1 to run installation smoke tests")
def test_pip_install_dot_exposes_repodossier_command(tmp_path: Path) -> None:
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    python = venv / "bin" / "python"
    command = venv / "bin" / "repodossier"

    result = subprocess.run(
        [str(python), "-m", "pip", "install", "--no-deps", str(ROOT)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    help_result = subprocess.run(
        [str(command), "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert help_result.returncode == 0
    assert "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER" in help_result.stdout


@pytest.mark.skipif(not _run_enabled(), reason="set REPODOSSIER_RUN_INSTALL_SMOKE=1 to run installation smoke tests")
def test_pipx_install_dot_exposes_repodossier_command(tmp_path: Path) -> None:
    pipx = shutil.which("pipx")
    if pipx is None:
        pytest.skip("pipx is not installed")

    env = os.environ.copy()
    env["PIPX_HOME"] = str(tmp_path / "pipx-home")
    env["PIPX_BIN_DIR"] = str(tmp_path / "pipx-bin")
    Path(env["PIPX_BIN_DIR"]).mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [pipx, "install", "--pip-args=--no-deps", str(ROOT)],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 and "PyYAML" in (result.stdout + result.stderr):
        pytest.skip("pipx isolated install could not resolve the PyYAML dependency in this environment")
    assert result.returncode == 0, result.stdout + result.stderr

    command = Path(env["PIPX_BIN_DIR"]) / "repodossier"
    help_result = subprocess.run(
        [str(command), "--help"],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert help_result.returncode == 0
    assert "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER" in help_result.stdout
