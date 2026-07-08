from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/dev/run_repodossier_exports.sh"


def _run_r(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["HOME"] = str(tmp_path)
    env.pop("C_RUNNER_WAIT_CHILD", None)
    env.pop("C_RUNNER_WATCH_CHILD", None)
    env.pop("C_RUNNER_SELF_COPY", None)
    env.pop("C_RUNNER_ORIGINAL", None)
    env.pop("C_RUNNER_TEMP_COPY", None)

    return subprocess.run(
        [str(RUNNER), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_r_runner_lists_modes(tmp_path: Path) -> None:
    result = _run_r(tmp_path, "--list-modes")

    assert result.returncode == 0
    assert "all" in result.stdout
    assert "full" in result.stdout
    assert "ai" in result.stdout
    assert "docs" in result.stdout
    assert "changed" in result.stdout


def test_r_runner_help_mentions_dry_run_and_modes(tmp_path: Path) -> None:
    result = _run_r(tmp_path, "--help")

    assert result.returncode == 0
    assert "--dry-run" in result.stdout
    assert "full" in result.stdout
    assert "export-ai" in result.stdout
    assert "export-docs" in result.stdout


def test_r_runner_dry_run_defaults_to_all_modes(tmp_path: Path) -> None:
    result = _run_r(tmp_path, "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Modi: full ai docs changed" in result.stdout
    assert "Befehl: repodossier full" in result.stdout
    assert "Befehl: repodossier export-ai" in result.stdout
    assert "Befehl: repodossier export-docs" in result.stdout
    assert "Befehl: repodossier changed" in result.stdout


def test_r_runner_dry_run_accepts_explicit_modes_and_aliases(tmp_path: Path) -> None:
    result = _run_r(tmp_path, "--dry-run", "quick", "doc", "changes", "full")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Modi: ai docs changed full" in result.stdout
    assert "Befehl: repodossier export-ai" in result.stdout
    assert "Befehl: repodossier export-docs" in result.stdout
    assert "Befehl: repodossier changed" in result.stdout
    assert "Befehl: repodossier full" in result.stdout


def test_r_runner_rejects_unknown_mode(tmp_path: Path) -> None:
    result = _run_r(tmp_path, "--dry-run", "missing-mode")

    assert result.returncode == 2
    assert "Unbekannter r-Modus: missing-mode" in result.stdout
