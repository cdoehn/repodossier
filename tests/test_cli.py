import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from repocontext.cli import main

AUTHOR_NAME = "Test Author"
AUTHOR_EMAIL = "author@example.com"
COMMIT_ENV = {
    "GIT_AUTHOR_DATE": "2023-01-01T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2023-01-01T00:00:00+00:00",
}

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git executable is required")


def run_git_command(
    repo_path: Path, *args: str, env: Optional[dict[str, str]] = None
) -> subprocess.CompletedProcess[str]:
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        env=env_vars,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )


def setup_repository(repo_path: Path) -> Path:
    repo_path.mkdir()
    run_git_command(repo_path, "init")
    run_git_command(repo_path, "config", "user.name", AUTHOR_NAME)
    run_git_command(repo_path, "config", "user.email", AUTHOR_EMAIL)
    readme_path = repo_path / "README.md"
    readme_path.write_text("Initial content\n", encoding="utf-8")
    run_git_command(repo_path, "add", "README.md")
    run_git_command(repo_path, "commit", "-m", "Initial commit", env=COMMIT_ENV)
    return repo_path


def test_cli_info_command_inside_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    monkeypatch.chdir(repo_path)

    exit_code = main(["info"])

    assert exit_code == 0
    captured = capsys.readouterr()
    output = captured.out
    assert "Repository info:" in output
    assert "Name:" in output
    assert "Root:" in output
    assert "Branch:" in output
    assert "Commit:" in output
    assert "Short commit:" in output
    assert "Remote:" in output
    assert "Dirty:" in output
    assert "Commit author:" in output
    assert "Commit date:" in output
    assert "Commit subject:" in output
    assert "Tracked files:" in output


def test_cli_default_command_delegates_to_info(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo_path = setup_repository(tmp_path / "repo_default")
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    captured = capsys.readouterr()
    output = captured.out
    assert "Repository info:" in output
    assert "Name:" in output
    assert "Root:" in output


def test_cli_info_command_outside_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    non_repo_path = tmp_path / "outside"
    non_repo_path.mkdir()
    monkeypatch.chdir(non_repo_path)

    exit_code = main(["info"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Could not determine the repository root." in captured.out
