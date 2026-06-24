"""Git repository discovery helpers."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TrackedFile:
    """Minimal representation of a Git-tracked file."""
    path: Path


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
    """Return the current Git branch name or None if it cannot be determined."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    branch_name = result.stdout.strip()
    return branch_name or None
