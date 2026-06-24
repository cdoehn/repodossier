"""Git repository discovery helpers."""

from pathlib import Path


def is_current_directory_git_repository() -> bool:
    """Return True if the current working directory contains a .git directory."""
    return (Path.cwd() / ".git").is_dir()
