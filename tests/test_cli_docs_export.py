"""CLI regression tests for the documentation export command."""

from __future__ import annotations

import subprocess
from pathlib import Path

from repodossier.cli import main


def run_git_command(repository_root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def setup_docs_export_repository(tmp_path: Path) -> Path:
    run_git_command(tmp_path, "init")
    run_git_command(tmp_path, "config", "user.email", "tester@example.com")
    run_git_command(tmp_path, "config", "user.name", "Tester")

    (tmp_path / "src").mkdir()
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

    run_git_command(tmp_path, "add", "README.md", "src/app.py")
    run_git_command(tmp_path, "commit", "-m", "Initial commit")
    return tmp_path


def test_cli_export_docs_command_creates_only_docs_export(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    repository_root = setup_docs_export_repository(tmp_path)
    monkeypatch.chdir(repository_root)

    exit_code = main(["export-docs"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Wrote" in output
    assert "docs.txt" in output

    assert (repository_root / "docs.txt").exists()
    assert not (repository_root / "full.txt").exists()
    assert not (repository_root / "ai.txt").exists()

    docs_content = (repository_root / "docs.txt").read_text(encoding="utf-8")
    assert docs_content.startswith("# Documentation Context")
    assert "### File: README.md" in docs_content
    assert "### File: src/app.py" not in docs_content
    assert "print('hello')" not in docs_content


def test_cli_export_docs_command_updates_gitignore_for_docs_txt(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository_root = setup_docs_export_repository(tmp_path)
    monkeypatch.chdir(repository_root)

    exit_code = main(["export-docs"])

    assert exit_code == 0
    gitignore_content = (repository_root / ".gitignore").read_text(encoding="utf-8")
    assert "# RepoDossier exports" in gitignore_content
    assert gitignore_content.count("full.txt") == 1
    assert gitignore_content.count("ai.txt") == 1
    assert gitignore_content.count("docs.txt") == 1
    assert gitignore_content.count("changed.txt") == 1


def test_cli_export_docs_command_writes_to_repository_root_from_subdirectory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository_root = setup_docs_export_repository(tmp_path)
    nested_directory = repository_root / "nested" / "dir"
    nested_directory.mkdir(parents=True)
    monkeypatch.chdir(nested_directory)

    exit_code = main(["export-docs"])

    assert exit_code == 0
    assert (repository_root / "docs.txt").exists()
    assert not (nested_directory / "docs.txt").exists()


def test_cli_export_docs_command_outside_repository(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["export-docs"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Error:" in output
    assert "repository root" in output
    assert not (tmp_path / "docs.txt").exists()
