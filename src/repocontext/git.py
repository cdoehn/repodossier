"""Git repository discovery helpers."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TrackedFile:
    """Minimal representation of a Git-tracked file."""
    path: Path


@dataclass
class CommitMetadata:
    """Metadata about a Git commit."""
    author_name: str
    author_email: str
    commit_date: str
    subject: str


@dataclass
class RepositoryInfo:
    """Aggregated information about a Git repository."""
    name: Optional[str]
    root_path: Path
    is_current_directory_root: bool
    branch: Optional[str]
    commit_hash: Optional[str]
    short_commit_hash: Optional[str]
    remote_url: Optional[str]
    is_dirty: Optional[bool]
    tracked_files: list[TrackedFile]
    commit_metadata: Optional[CommitMetadata]


def is_current_directory_git_repository() -> bool:
    """Return True if the current working directory contains a .git directory."""
    return (Path.cwd() / ".git").is_dir()


def find_repository_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Return the repository root by searching upward for a .git directory."""
    current_path = Path(start_path) if start_path is not None else Path.cwd()
    current_path = current_path.resolve()

    while True:
        if (current_path / ".git").is_dir():
            return current_path
        if current_path.parent == current_path:
            return None
        current_path = current_path.parent


def get_repository_name(repository_root: Path) -> Optional[str]:
    """Return the repository name derived from the repository root path."""
    if repository_root is None:
        return None

    name = repository_root.name
    return name or None


def is_working_tree_dirty(repository_root: Path) -> Optional[bool]:
    """Return True if the working tree has uncommitted changes, False if clean, or None if unknown."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repository_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None

    output = result.stdout.strip()
    if output:
        return True
    return False


def list_tracked_files(repository_root: Path) -> list[TrackedFile]:
    """Return a list of Git-tracked file paths relative to the repository root."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    tracked_paths = [Path(path) for path in result.stdout.splitlines() if path]
    return [
        TrackedFile(path=relative_path)
        for relative_path in tracked_paths
        if (repository_root / relative_path).exists()
    ]


def get_current_branch(repository_root: Path) -> Optional[str]:
    """Return the current Git branch name or a detached HEAD state string."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    branch_name = result.stdout.strip()
    if branch_name:
        return branch_name

    try:
        detached_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repository_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    commit_hash = detached_result.stdout.strip()
    if commit_hash:
        return f"detached at {commit_hash}"
    return None


def get_origin_remote_url(repository_root: Path) -> Optional[str]:
    """Return the origin remote URL for the repository or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repository_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None

    url = result.stdout.strip()
    return url if url else None


def get_current_commit_metadata(repository_root: Path) -> Optional[CommitMetadata]:
    """Return metadata for the current HEAD commit or None."""
    try:
        result = subprocess.run(
            ["git", "show", "-s", "--format=%an%n%ae%n%cI%n%s", "HEAD"],
            cwd=repository_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None

    lines = result.stdout.splitlines()
    if len(lines) < 4:
        return None

    author_name, author_email, commit_date, subject = (line.strip() for line in lines[:4])

    return CommitMetadata(
        author_name=author_name,
        author_email=author_email,
        commit_date=commit_date,
        subject=subject,
    )


def get_current_commit_hash(repository_root: Path) -> Optional[str]:
    """Return the current full Git commit hash for the repository or None."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    commit_hash = result.stdout.strip()
    return commit_hash if commit_hash else None


def get_current_short_commit_hash(repository_root: Path) -> Optional[str]:
    """Return the current short Git commit hash for the repository or None."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repository_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    short_hash = result.stdout.strip()
    return short_hash if short_hash else None


def get_repository_info(repository_root: Path) -> RepositoryInfo:
    """Return aggregated information about the repository rooted at repository_root."""
    resolved_repository_root = repository_root.resolve()
    is_current_directory_root = Path.cwd().resolve() == resolved_repository_root

    return RepositoryInfo(
        name=get_repository_name(resolved_repository_root),
        root_path=resolved_repository_root,
        is_current_directory_root=is_current_directory_root,
        branch=get_current_branch(resolved_repository_root),
        commit_hash=get_current_commit_hash(resolved_repository_root),
        short_commit_hash=get_current_short_commit_hash(resolved_repository_root),
        remote_url=get_origin_remote_url(resolved_repository_root),
        is_dirty=is_working_tree_dirty(resolved_repository_root),
        tracked_files=list_tracked_files(resolved_repository_root),
        commit_metadata=get_current_commit_metadata(resolved_repository_root),
    )

# Changed export git support

from dataclasses import dataclass


@dataclass(frozen=True)
class ChangedFile:
    """A file changed relative to the current git working tree state."""

    path: str
    status: str
    is_tracked: bool = True
    is_untracked: bool = False
    is_deleted: bool = False


def _run_git_output(repo_path: str | Path, args: list[str]) -> str:
    """Run a git command and return stdout as text."""
    result = subprocess.run(
        ["git", *args],
        cwd=Path(repo_path),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _parse_porcelain_changed_file(line: str) -> ChangedFile | None:
    """Parse one git status --porcelain=v1 line."""
    if not line:
        return None

    if line.startswith("?? "):
        path = line[3:].strip()
        if not path:
            return None
        return ChangedFile(
            path=path,
            status="untracked",
            is_tracked=False,
            is_untracked=True,
            is_deleted=False,
        )

    if len(line) < 4:
        return None

    index_status = line[0]
    working_tree_status = line[1]
    raw_path = line[3:].strip()

    if " -> " in raw_path:
        raw_path = raw_path.split(" -> ", 1)[1].strip()

    if not raw_path:
        return None

    status_pair = index_status + working_tree_status

    if "D" in status_pair:
        status = "deleted"
    elif "R" in status_pair:
        status = "renamed"
    elif "A" in status_pair:
        status = "added"
    else:
        status = "modified"

    return ChangedFile(
        path=raw_path,
        status=status,
        is_tracked=True,
        is_untracked=False,
        is_deleted=status == "deleted",
    )


def get_changed_files(repo_path: str | Path = ".") -> list[ChangedFile]:
    """Return changed, staged, unstaged, deleted, and untracked files.

    Ignored files are excluded by git via --untracked-files=all and the
    repository's standard ignore rules.
    """
    output = _run_git_output(
        repo_path,
        ["status", "--porcelain=v1", "--untracked-files=all"],
    )

    by_path: dict[str, ChangedFile] = {}
    for line in output.splitlines():
        changed_file = _parse_porcelain_changed_file(line)
        if changed_file is None:
            continue
        by_path[changed_file.path] = changed_file

    return [by_path[path] for path in sorted(by_path)]

