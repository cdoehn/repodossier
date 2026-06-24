"""Command-line interface entrypoint for RepoContext."""

from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
from typing import Iterable, Optional

from .git import find_repository_root, get_current_branch, list_tracked_files


_FALLBACK_VERSION = "0.1.0.dev0"


def _determine_version() -> str:
    """Return the installed package version or a fallback value."""
    try:
        return metadata.version("repocontext")
    except metadata.PackageNotFoundError:
        return _FALLBACK_VERSION


def _print_repository_info(repository_root: Path) -> None:
    """Display repository information for the CLI."""
    print("Repository info:")
    print(f"  Root: {repository_root}")
    is_root = Path.cwd().resolve() == repository_root
    print(f"  Current directory is root: {'yes' if is_root else 'no'}")
    current_branch = get_current_branch(repository_root)
    branch_display = current_branch if current_branch is not None else "unknown"
    print(f"  Branch: {branch_display}")
    tracked_files = list_tracked_files(repository_root)
    print(f"  Tracked files: {len(tracked_files)}")


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Run the RepoContext command-line interface.

    Args:
        argv: Optional iterable of argument strings. Defaults to ``None`` to use
            :data:`sys.argv`.

    Returns:
        An integer process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="repocontext",
        description=(
            "RepoContext prepares AI-friendly exports of Git repositories, "
            "tailored for large language models."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_determine_version()}")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("info", help="Show repository discovery information.")

    args = parser.parse_args(argv)

    if args.command == "info":
        repository_root = find_repository_root()
        if repository_root is None:
            print("No Git repository found.")
            return 1
        _print_repository_info(repository_root)
        return 0

    repository_root = find_repository_root()
    if repository_root is not None:
        print("Repository root:\n ", repository_root, sep="")
        return 0

    print("No Git repository found.")
    return 1
