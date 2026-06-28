from __future__ import annotations

import subprocess
from pathlib import Path

from repocontext.git import ChangedFile, get_changed_files


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "tests@example.invalid")
    run_git(repo, "config", "user.name", "RepoContext Tests")
    return repo


def commit_file(repo: Path, relative_path: str, content: str = "initial\n") -> None:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    run_git(repo, "add", relative_path)
    run_git(repo, "commit", "-m", f"Add {relative_path}")


def changed_by_path(repo: Path) -> dict[str, ChangedFile]:
    return {item.path: item for item in get_changed_files(repo)}


def test_get_changed_files_returns_empty_list_for_clean_repo(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md")

    assert get_changed_files(repo) == []


def test_get_changed_files_detects_unstaged_modified_file(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "src/app.py", "print('old')\n")

    (repo / "src/app.py").write_text("print('new')\n", encoding="utf-8")

    changed = changed_by_path(repo)

    assert changed["src/app.py"].status == "modified"
    assert changed["src/app.py"].is_tracked is True
    assert changed["src/app.py"].is_deleted is False


def test_get_changed_files_detects_staged_modified_file(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "src/app.py", "print('old')\n")

    (repo / "src/app.py").write_text("print('new')\n", encoding="utf-8")
    run_git(repo, "add", "src/app.py")

    changed = changed_by_path(repo)

    assert changed["src/app.py"].status == "modified"
    assert changed["src/app.py"].is_tracked is True


def test_get_changed_files_deduplicates_staged_and_unstaged_same_file(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "src/app.py", "print('old')\n")

    (repo / "src/app.py").write_text("print('staged')\n", encoding="utf-8")
    run_git(repo, "add", "src/app.py")
    (repo / "src/app.py").write_text("print('unstaged')\n", encoding="utf-8")

    changed = get_changed_files(repo)

    assert [item.path for item in changed] == ["src/app.py"]
    assert changed[0].status == "modified"


def test_get_changed_files_detects_untracked_files_and_respects_gitignore(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, ".gitignore", "*.log\n")

    (repo / "notes.txt").write_text("new\n", encoding="utf-8")
    (repo / "ignored.log").write_text("ignored\n", encoding="utf-8")

    changed = changed_by_path(repo)

    assert changed["notes.txt"].status == "untracked"
    assert changed["notes.txt"].is_tracked is False
    assert changed["notes.txt"].is_untracked is True
    assert "ignored.log" not in changed


def test_get_changed_files_detects_deleted_files(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "obsolete.txt")

    (repo / "obsolete.txt").unlink()

    changed = changed_by_path(repo)

    assert changed["obsolete.txt"].status == "deleted"
    assert changed["obsolete.txt"].is_deleted is True
    assert changed["obsolete.txt"].is_tracked is True


def test_get_changed_files_returns_stable_sorted_output(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md")

    (repo / "z.txt").write_text("z\n", encoding="utf-8")
    (repo / "a.txt").write_text("a\n", encoding="utf-8")

    assert [item.path for item in get_changed_files(repo)] == ["a.txt", "z.txt"]
