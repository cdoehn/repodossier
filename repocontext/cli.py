from typing import Iterable, Optional

from .git import is_current_directory_git_repository


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Entry point for the RepoContext CLI."""
    is_repo = is_current_directory_git_repository()

    if is_repo:
        print("Current directory is a Git repository.")
        return 0

    print("Current directory is not a Git repository.")
    return 1
