from __future__ import annotations

import subprocess
from pathlib import Path

from repocontext.git import (ChangedFile, GitBranchComparisonError, get_changed_files, get_changed_files_against_branch, get_diff, get_diff_against_branch)


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


def checkout_feature_branch_from_main(repo: Path) -> None:
    """Normalize the initial branch to main and create a feature branch."""
    run_git(repo, "branch", "-M", "main")
    run_git(repo, "checkout", "-b", "feature")


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


def test_get_diff_returns_unified_diff_for_unstaged_modified_file(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "src/app.py", "print('old')\n")

    (repo / "src/app.py").write_text("print('new')\n", encoding="utf-8")

    diff = get_diff(repo, "src/app.py")

    assert "diff --git" in diff
    assert "-print('old')" in diff
    assert "+print('new')" in diff


def test_get_diff_returns_unified_diff_for_staged_modified_file(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "src/app.py", "print('old')\n")

    (repo / "src/app.py").write_text("print('new')\n", encoding="utf-8")
    run_git(repo, "add", "src/app.py")

    diff = get_diff(repo, "src/app.py")

    assert "diff --git" in diff
    assert "-print('old')" in diff
    assert "+print('new')" in diff


def test_get_diff_returns_empty_string_for_untracked_file(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md")

    (repo / "notes.txt").write_text("new file\n", encoding="utf-8")

    assert get_diff(repo, "notes.txt") == ""


def test_get_diff_returns_empty_string_outside_git_repo(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('changed')\n", encoding="utf-8")

    assert get_diff(tmp_path, "app.py") == ""


def test_get_changed_files_against_branch_detects_committed_change(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "app.py", "print('main')\n")
    checkout_feature_branch_from_main(repo)

    (repo / "app.py").write_text("print('feature')\n", encoding="utf-8")
    run_git(repo, "add", "app.py")
    run_git(repo, "commit", "-m", "Change app")

    changed = changed_by_path_for_branch(repo, "main")

    assert changed["app.py"].status == "modified"
    assert changed["app.py"].is_deleted is False


def test_get_changed_files_against_branch_detects_added_deleted_and_renamed_files(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "keep.py", "keep\n")
    commit_file(repo, "obsolete.py", "obsolete\n")
    commit_file(repo, "old_name.py", "renamed\n")
    checkout_feature_branch_from_main(repo)

    (repo / "added.py").write_text("added\n", encoding="utf-8")
    run_git(repo, "add", "added.py")
    (repo / "obsolete.py").unlink()
    run_git(repo, "rm", "obsolete.py")
    run_git(repo, "mv", "old_name.py", "new_name.py")
    run_git(repo, "commit", "-m", "Add delete rename")

    changed = changed_by_path_for_branch(repo, "main")

    assert changed["added.py"].status == "added"
    assert changed["obsolete.py"].status == "deleted"
    assert changed["obsolete.py"].is_deleted is True
    assert changed["new_name.py"].status == "renamed"


def test_get_changed_files_against_branch_returns_empty_list_for_no_changes(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md")
    checkout_feature_branch_from_main(repo)

    assert get_changed_files_against_branch(repo, "main") == []


def test_get_changed_files_against_branch_raises_clear_error_for_missing_branch(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md")

    try:
        get_changed_files_against_branch(repo, "does-not-exist")
    except GitBranchComparisonError as exc:
        assert "does-not-exist" in str(exc)
    else:
        raise AssertionError("Expected GitBranchComparisonError")


def test_get_diff_against_branch_contains_committed_changes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "app.py", "print('main')\n")
    checkout_feature_branch_from_main(repo)

    (repo / "app.py").write_text("print('feature')\n", encoding="utf-8")
    run_git(repo, "add", "app.py")
    run_git(repo, "commit", "-m", "Change app")

    diff = get_diff_against_branch(repo, "main", "app.py")

    assert "diff --git" in diff
    assert "-print('main')" in diff
    assert "+print('feature')" in diff


def test_get_diff_against_branch_returns_empty_string_for_no_changes(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md")
    checkout_feature_branch_from_main(repo)

    assert get_diff_against_branch(repo, "main") == ""


def test_get_diff_against_branch_raises_clear_error_for_missing_branch(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    commit_file(repo, "README.md")

    try:
        get_diff_against_branch(repo, "does-not-exist")
    except GitBranchComparisonError as exc:
        assert "does-not-exist" in str(exc)
    else:
        raise AssertionError("Expected GitBranchComparisonError")


def changed_by_path_for_branch(repo: Path, branch: str) -> dict[str, ChangedFile]:
    return {
        item.path: item
        for item in get_changed_files_against_branch(repo, branch)
    }

