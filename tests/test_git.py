import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from repocontext.git import (
    TrackedFile,
    find_repository_root,
    get_current_branch,
    get_current_commit_hash,
    get_current_commit_metadata,
    get_current_short_commit_hash,
    get_origin_remote_url,
    get_repository_name,
    is_working_tree_dirty,
    list_tracked_files,
)

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


def test_repository_root_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    nested_dir = repo_path / "nested" / "dir"
    nested_dir.mkdir(parents=True)
    discovered_root = find_repository_root(nested_dir)
    assert discovered_root == repo_path.resolve()


def test_missing_repository_root_detection(tmp_path: Path) -> None:
    non_repo_path = tmp_path / "not_a_repo"
    non_repo_path.mkdir()
    assert find_repository_root(non_repo_path) is None


def test_repository_name_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "sample-repo")
    name = get_repository_name(repo_path.resolve())
    assert name == "sample-repo"


def test_tracked_file_discovery(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    src_dir = repo_path / "src"
    src_dir.mkdir()
    module_path = src_dir / "module.py"
    module_path.write_text("print('hello world')\n", encoding="utf-8")
    run_git_command(repo_path, "add", str(module_path.relative_to(repo_path)))
    run_git_command(repo_path, "commit", "-m", "Add module", env=COMMIT_ENV)

    tracked_files = list_tracked_files(repo_path)
    tracked_paths = sorted(tracked_file.path.as_posix() for tracked_file in tracked_files)
    assert tracked_paths == ["README.md", "src/module.py"]
    assert all(isinstance(tracked_file, TrackedFile) for tracked_file in tracked_files)


def test_missing_tracked_files_are_ignored(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    (repo_path / "README.md").unlink()

    tracked_files = list_tracked_files(repo_path)
    assert tracked_files == []


def test_current_branch_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    branch_name = "feature/test-branch"
    run_git_command(repo_path, "checkout", "-b", branch_name)

    branch = get_current_branch(repo_path)
    assert branch == branch_name


def test_current_commit_hash_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    expected_hash = run_git_command(repo_path, "rev-parse", "HEAD").stdout.strip()
    commit_hash = get_current_commit_hash(repo_path)
    assert commit_hash is not None
    assert len(commit_hash) == 40
    assert commit_hash == expected_hash


def test_current_short_commit_hash_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    expected_short_hash = run_git_command(repo_path, "rev-parse", "--short", "HEAD").stdout.strip()
    short_hash = get_current_short_commit_hash(repo_path)
    assert short_hash is not None
    assert 4 <= len(short_hash) <= 40
    assert short_hash == expected_short_hash


def test_commit_metadata_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    metadata = get_current_commit_metadata(repo_path)

    assert metadata is not None
    assert metadata.author_name == AUTHOR_NAME
    assert metadata.author_email == AUTHOR_EMAIL
    assert metadata.commit_date == COMMIT_ENV["GIT_AUTHOR_DATE"]
    assert metadata.subject == "Initial commit"


def test_origin_remote_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    remote_url = "https://example.com/example/repo.git"
    run_git_command(repo_path, "remote", "add", "origin", remote_url)

    assert get_origin_remote_url(repo_path) == remote_url


def test_working_tree_clean_and_dirty_detection(tmp_path: Path) -> None:
    repo_path = setup_repository(tmp_path / "repo")
    assert is_working_tree_dirty(repo_path) is False

    readme_path = repo_path / "README.md"
    readme_path.write_text("Initial content\nModified line\n", encoding="utf-8")
    assert is_working_tree_dirty(repo_path) is True
