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




def test_cli_info_command_includes_import_graph_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_path = setup_repository(tmp_path / "repo_info_import_graph")
    package_dir = repo_path / "src" / "app"
    package_dir.mkdir(parents=True)

    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "main.py").write_text(
        "import os\n"
        "import app.utils\n",
        encoding="utf-8",
    )
    (package_dir / "utils.py").write_text(
        "def helper():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )

    run_git_command(repo_path, "add", "src/app/__init__.py", "src/app/main.py", "src/app/utils.py")
    run_git_command(repo_path, "commit", "-m", "Add Python package", env=COMMIT_ENV)
    monkeypatch.chdir(repo_path)

    exit_code = main(["info"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Import graph:" in output
    assert "Python modules: 3" in output
    assert "Import dependencies: 1" in output
    assert "External imports: 1" in output
    assert "Unresolved imports: 0" in output
    assert "Analysis errors: 0" in output



def write_call_graph_cli_fixture(repo_path: Path) -> None:
    """Add a tiny Python package with a known imported function call."""

    package_dir = repo_path / "src" / "app"
    package_dir.mkdir(parents=True, exist_ok=True)

    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "helpers.py").write_text(
        "def helper():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    (package_dir / "main.py").write_text(
        "from app.helpers import helper\n"
        "\n"
        "def main():\n"
        "    return helper()\n",
        encoding="utf-8",
    )

    run_git_command(
        repo_path,
        "add",
        "src/app/__init__.py",
        "src/app/helpers.py",
        "src/app/main.py",
    )
    run_git_command(
        repo_path,
        "commit",
        "-m",
        "Add call graph fixture",
        env=COMMIT_ENV,
    )


def assert_full_export_contains_cli_call_graph(repo_path: Path) -> None:
    """Assert that the CLI-generated full.txt includes Call Graph data."""

    content = (repo_path / "full.txt").read_text(encoding="utf-8")
    assert "## Call Graph" in content
    assert "Internal calls by caller:" in content
    assert "app.main.main (src/app/main.py)" in content
    assert (
        "  - line 4: calls app.helpers.helper "
        "[function, imported_local]"
    ) in content

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

def test_cli_full_command_survives_syntax_error_python_file_and_keeps_call_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_path = setup_repository(tmp_path / "repo_cli_call_graph_syntax_error")
    write_call_graph_cli_fixture(repo_path)

    broken_path = repo_path / "src" / "app" / "broken.py"
    broken_path.write_text(
        "def broken(:\n"
        "    pass\n",
        encoding="utf-8",
    )
    run_git_command(repo_path, "add", "src/app/broken.py")
    run_git_command(
        repo_path,
        "commit",
        "-m",
        "Add syntax error fixture",
        env=COMMIT_ENV,
    )

    monkeypatch.chdir(repo_path)

    exit_code = main(["full"])

    assert exit_code == 0
    assert_full_export_contains_cli_call_graph(repo_path)

    content = (repo_path / "full.txt").read_text(encoding="utf-8")
    assert "## Import Graph" in content
    assert "Analysis errors:" in content
    assert "SyntaxError" in content
    assert "## Call Graph" in content
    assert "Traceback" not in content

    captured = capsys.readouterr()
    assert f"Wrote {repo_path / 'full.txt'}" in captured.out


def test_cli_export_command_survives_syntax_error_python_file_and_keeps_call_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_path = setup_repository(tmp_path / "repo_cli_export_call_graph_syntax_error")
    write_call_graph_cli_fixture(repo_path)

    broken_path = repo_path / "src" / "app" / "broken.py"
    broken_path.write_text(
        "def broken(:\n"
        "    pass\n",
        encoding="utf-8",
    )
    run_git_command(repo_path, "add", "src/app/broken.py")
    run_git_command(
        repo_path,
        "commit",
        "-m",
        "Add syntax error fixture",
        env=COMMIT_ENV,
    )

    monkeypatch.chdir(repo_path)

    exit_code = main(["export"])

    assert exit_code == 0
    assert_full_export_contains_cli_call_graph(repo_path)

    content = (repo_path / "full.txt").read_text(encoding="utf-8")
    assert "## Import Graph" in content
    assert "Analysis errors:" in content
    assert "SyntaxError" in content
    assert "## Call Graph" in content
    assert "Traceback" not in content

    captured = capsys.readouterr()
    assert f"Wrote {repo_path / 'full.txt'}" in captured.out


def test_cli_full_command_generates_call_graph_in_normal_export_flow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_path = setup_repository(tmp_path / "repo_cli_full_call_graph")
    write_call_graph_cli_fixture(repo_path)
    monkeypatch.chdir(repo_path)

    exit_code = main(["full"])

    assert exit_code == 0
    assert_full_export_contains_cli_call_graph(repo_path)
    captured = capsys.readouterr()
    assert f"Wrote {repo_path / 'full.txt'}" in captured.out


def test_cli_export_command_generates_call_graph_in_normal_export_flow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_path = setup_repository(tmp_path / "repo_cli_export_call_graph")
    write_call_graph_cli_fixture(repo_path)
    monkeypatch.chdir(repo_path)

    exit_code = main(["export"])

    assert exit_code == 0
    assert_full_export_contains_cli_call_graph(repo_path)
    captured = capsys.readouterr()
    assert f"Wrote {repo_path / 'full.txt'}" in captured.out



def test_cli_default_command_creates_ai_export_together_with_full_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_path = setup_repository(tmp_path / "repo_default_ai_export")
    package_dir = repo_path / "src" / "app"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "main.py").write_text(
        "def main():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    run_git_command(repo_path, "add", "src/app/__init__.py", "src/app/main.py")
    run_git_command(repo_path, "commit", "-m", "Add Python package", env=COMMIT_ENV)
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0

    full_output_path = repo_path / "full.txt"
    ai_output_path = repo_path / "ai.txt"

    assert full_output_path.exists()
    assert ai_output_path.exists()

    ai_content = ai_output_path.read_text(encoding="utf-8")
    assert ai_content.startswith("# AI CONTEXT\n")
    assert "## Architecture Summary" in ai_content
    assert "## Important Files" in ai_content
    assert "## Symbol Index" in ai_content
    assert "## Import Graph" in ai_content
    assert "## Call Graph" in ai_content
    assert "# Complete Source Export" not in ai_content

    captured = capsys.readouterr()
    assert f"Wrote {full_output_path}" in captured.out
    assert f"Wrote {ai_output_path}" in captured.out


def test_cli_full_command_creates_ai_export_together_with_full_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_full_ai_export")
    monkeypatch.chdir(repo_path)

    exit_code = main(["full"])

    assert exit_code == 0
    assert (repo_path / "full.txt").exists()
    assert (repo_path / "ai.txt").exists()
    assert (repo_path / "ai.txt").read_text(encoding="utf-8").startswith("# AI CONTEXT\n")


def test_cli_export_command_creates_ai_export_together_with_full_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_export_ai_export")
    monkeypatch.chdir(repo_path)

    exit_code = main(["export"])

    assert exit_code == 0
    assert (repo_path / "full.txt").exists()
    assert (repo_path / "ai.txt").exists()
    assert (repo_path / "ai.txt").read_text(encoding="utf-8").startswith("# AI CONTEXT\n")



def test_cli_export_ai_command_updates_gitignore_for_ai_txt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_export_ai_gitignore")
    gitignore_path = repo_path / ".gitignore"
    gitignore_path.write_text(
        "# RepoContext exports\n"
        "full.txt\n"
        "docs.txt\n"
        "changed.txt\n",
        encoding="utf-8",
    )
    run_git_command(repo_path, "add", ".gitignore")
    run_git_command(repo_path, "commit", "-m", "Add incomplete gitignore", env=COMMIT_ENV)
    monkeypatch.chdir(repo_path)

    exit_code = main(["export-ai"])

    assert exit_code == 0
    assert (repo_path / "ai.txt").exists()

    gitignore_content = gitignore_path.read_text(encoding="utf-8")
    assert gitignore_content.count("ai.txt") == 1
    assert "full.txt" in gitignore_content
    assert "docs.txt" in gitignore_content
    assert "changed.txt" in gitignore_content


def test_cli_default_export_keeps_ai_txt_untracked_after_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_default_ai_untracked")
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    assert (repo_path / "ai.txt").exists()

    status_output = run_git_command(repo_path, "status", "--short").stdout
    assert "ai.txt" not in status_output
    assert "full.txt" not in status_output


def test_cli_export_ai_command_creates_only_ai_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_path = setup_repository(tmp_path / "repo_export_ai_only")
    monkeypatch.chdir(repo_path)

    exit_code = main(["export-ai"])

    assert exit_code == 0

    ai_output_path = repo_path / "ai.txt"
    assert ai_output_path.exists()
    assert ai_output_path.read_text(encoding="utf-8").startswith("# AI CONTEXT\n")
    assert not (repo_path / "full.txt").exists()

    captured = capsys.readouterr()
    assert f"Wrote {ai_output_path}" in captured.out


def test_cli_default_command_creates_full_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo_path = setup_repository(tmp_path / "repo_default")
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    output_path = repo_path / "full.txt"
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# AI Quick Start" in content
    assert "# Repository Statistics" in content
    assert "# File Summary" in content
    assert "# Repository Tree" in content
    assert "# Complete Source Export" in content
    assert "# Warnings" in content

    captured = capsys.readouterr()
    assert f"Wrote {output_path}" in captured.out



def test_cli_default_command_creates_gitignore_entries_for_exports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_default_gitignore")
    monkeypatch.chdir(repo_path)

    assert not (repo_path / ".gitignore").exists()

    exit_code = main([])

    assert exit_code == 0
    gitignore_content = (repo_path / ".gitignore").read_text(encoding="utf-8")
    assert "# RepoContext exports" in gitignore_content
    assert "full.txt" in gitignore_content
    assert "ai.txt" in gitignore_content
    assert "docs.txt" in gitignore_content
    assert "changed.txt" in gitignore_content


def test_cli_default_command_preserves_existing_gitignore_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_existing_gitignore")
    gitignore_path = repo_path / ".gitignore"
    gitignore_path.write_text(".venv/\n__pycache__/\n", encoding="utf-8")
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    gitignore_content = gitignore_path.read_text(encoding="utf-8")
    assert ".venv/" in gitignore_content
    assert "__pycache__/" in gitignore_content
    assert "# RepoContext exports" in gitignore_content
    assert gitignore_content.count("full.txt") == 1


def test_cli_default_command_gitignore_prevents_full_txt_untracked_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_gitignore_status")
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    status_output = run_git_command(repo_path, "status", "--short").stdout
    assert "full.txt" not in status_output
    assert "ai.txt" not in status_output


def test_cli_default_command_writes_full_txt_to_repository_root_from_subdirectory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_from_subdir")
    nested_dir = repo_path / "nested" / "dir"
    nested_dir.mkdir(parents=True)
    monkeypatch.chdir(nested_dir)

    exit_code = main([])

    assert exit_code == 0
    assert (repo_path / "full.txt").exists()
    assert not (nested_dir / "full.txt").exists()
    assert (repo_path / ".gitignore").exists()
    assert not (nested_dir / ".gitignore").exists()


def test_cli_default_full_export_contains_tracked_text_file_in_all_mvp_sections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_full_export_text")
    docs_dir = repo_path / "docs"
    docs_dir.mkdir()
    notes_path = docs_dir / "notes.txt"
    notes_path.write_text("alpha\nbeta\n", encoding="utf-8")
    run_git_command(repo_path, "add", "docs/notes.txt")
    run_git_command(repo_path, "commit", "-m", "Add notes", env=COMMIT_ENV)
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    full_export = repo_path / "full.txt"
    content = full_export.read_text(encoding="utf-8")

    assert "# File Summary" in content
    assert "## Text (1 file)" in content
    assert "- `docs/notes.txt` — 2 lines, ~3 tokens" in content

    assert "# Repository Tree" in content
    assert "docs" in content
    assert "notes.txt" in content

    assert "# Complete Source Export" in content
    assert "## File: docs/notes.txt" in content
    assert "alpha\nbeta\n" in content

    assert "# Repository Statistics" in content
    assert "Total lines:" in content
    assert "Estimated tokens:" in content


def test_cli_default_full_export_excludes_binary_file_from_source_dump_and_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_full_export_binary")
    binary_path = repo_path / "binary.bin"
    binary_path.write_bytes(b"\x00\x01\x02")
    run_git_command(repo_path, "add", "binary.bin")
    run_git_command(repo_path, "commit", "-m", "Add binary file", env=COMMIT_ENV)
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    content = (repo_path / "full.txt").read_text(encoding="utf-8")

    assert "# Repository Tree" in content
    assert "binary.bin [binary skipped]" in content

    assert "# Complete Source Export" in content
    assert "## File: binary.bin" not in content

    assert "# Warnings" in content
    assert "- Skipped binary file: binary.bin" in content


def test_cli_default_full_export_preserves_known_text_line_and_token_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_path = setup_repository(tmp_path / "repo_full_export_counts")
    data_path = repo_path / "data.txt"
    data_path.write_text("abcd\nefgh\n", encoding="utf-8")
    run_git_command(repo_path, "add", "data.txt")
    run_git_command(repo_path, "commit", "-m", "Add data file", env=COMMIT_ENV)
    monkeypatch.chdir(repo_path)

    exit_code = main([])

    assert exit_code == 0
    content = (repo_path / "full.txt").read_text(encoding="utf-8")

    assert "- `data.txt` — 2 lines, ~3 tokens" in content
    assert "## File: data.txt" in content
    assert "abcd\nefgh\n" in content


def test_cli_info_command_outside_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    non_repo_path = tmp_path / "outside"
    non_repo_path.mkdir()
    monkeypatch.chdir(non_repo_path)

    exit_code = main(["info"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Could not determine the repository root." in captured.out


def test_cli_default_command_outside_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    non_repo_path = tmp_path / "outside_default"
    non_repo_path.mkdir()
    monkeypatch.chdir(non_repo_path)

    exit_code = main([])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Could not determine the repository root." in captured.out
