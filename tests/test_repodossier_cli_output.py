import subprocess
import sys
import tomllib
from pathlib import Path


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "repodossier", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_repodossier_help_uses_repodossier_branding():
    result = run_cli("--help")

    assert result.returncode == 0
    combined = result.stdout + result.stderr

    assert "RepoDossier" in combined
    assert "repodossier" in combined
    assert "RepoContext" not in combined


def test_repodossier_module_help_uses_current_command_examples():
    result = run_cli("--help")

    assert result.returncode == 0
    combined = result.stdout + result.stderr

    assert "repodossier" in combined
    assert "repodossier full" not in combined
    assert "repodossier export-ai" not in combined
    assert "repodossier export-docs" not in combined


def test_legacy_repodossier_console_script_is_still_declared():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    scripts = data["project"]["scripts"]

    assert scripts["repodossier"] == "repodossier.cli:main"
    assert scripts["repodossier"] == "repodossier.cli:main"


def test_legacy_repocontext_module_help_still_runs():
    result = subprocess.run(
        [sys.executable, "-m", "repocontext", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined = result.stdout + result.stderr

    assert "RepoDossier" in combined
    assert "RepoContext" not in combined
