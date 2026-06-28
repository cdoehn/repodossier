from __future__ import annotations

from pathlib import Path
import subprocess

from repocontext.cli import main


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def init_repo(path: Path) -> Path:
    repo = path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "tester@example.com")
    run_git(repo, "config", "user.name", "Test User")
    return repo


def commit_file(repo: Path, relative_path: str, content: str) -> None:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    run_git(repo, "add", relative_path)
    run_git(repo, "commit", "-m", f"Add {relative_path}")


def test_changed_cli_end_to_end_writes_changed_txt_for_working_tree(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "app.py", "print('initial')\n")

    (repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    status = main(["changed", "--no-diff"])

    changed_txt = repo / "changed.txt"
    content = changed_txt.read_text(encoding="utf-8")
    gitignore = (repo / ".gitignore").read_text(encoding="utf-8")

    assert status == 0
    assert changed_txt.exists()
    assert "# Changed Export" in content
    assert "Compare Mode: Working tree" in content
    assert "# Changed Files Summary" in content
    assert "- `app.py` (modified)" in content
    assert "# Changed File Contents" in content
    assert "## app.py" in content
    assert "print('changed')" in content
    assert "# Git Diff" not in content
    assert "changed.txt" in gitignore


def test_changed_cli_end_to_end_writes_branch_comparison_export(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "app.py", "print('main')\n")
    run_git(repo, "branch", "-M", "main")
    run_git(repo, "checkout", "-b", "feature")

    (repo / "app.py").write_text("print('feature')\n", encoding="utf-8")
    run_git(repo, "add", "app.py")
    run_git(repo, "commit", "-m", "Change app on feature")

    monkeypatch.chdir(repo)

    status = main(["changed", "--branch", "main"])

    changed_txt = repo / "changed.txt"
    content = changed_txt.read_text(encoding="utf-8")

    assert status == 0
    assert changed_txt.exists()
    assert "Compare Mode: Against branch: main" in content
    assert "- `app.py` (modified)" in content
    assert "# Git Diff" in content
    assert "-print('main')" in content
    assert "+print('feature')" in content
    assert "# Changed File Contents" in content
    assert "## app.py" in content
    assert "print('feature')" in content


def test_changed_cli_from_subdirectory_writes_changed_txt_to_repository_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "app.py", "print('initial')\n")

    nested_dir = repo / "nested" / "dir"
    nested_dir.mkdir(parents=True)

    (repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
    monkeypatch.chdir(nested_dir)

    status = main(["changed", "--no-diff"])

    root_changed_txt = repo / "changed.txt"
    nested_changed_txt = nested_dir / "changed.txt"
    content = root_changed_txt.read_text(encoding="utf-8")
    gitignore = (repo / ".gitignore").read_text(encoding="utf-8")

    assert status == 0
    assert root_changed_txt.exists()
    assert not nested_changed_txt.exists()
    assert "Compare Mode: Working tree" in content
    assert "- `app.py` (modified)" in content
    assert "print('changed')" in content
    assert "changed.txt" in gitignore

