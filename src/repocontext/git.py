"""Git repository discovery helpers."""

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
