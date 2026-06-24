"""Git repository discovery helpers."""

import subprocess
from pathlib import Path
from typing import Optional


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


def list_tracked_files(repository_root: Path) -> list[Path]:
    """Return a list of Git-tracked file paths relative to the repository root."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return [Path(path) for path in result.stdout.splitlines() if path]
