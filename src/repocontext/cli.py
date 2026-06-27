"""Command-line interface entrypoint for RepoContext."""

from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
from typing import Iterable, Optional

from .exporters import generate_full_export
from .git import RepositoryInfo, find_repository_root, get_repository_info


_FALLBACK_VERSION = "0.1.0.dev0"


def _determine_version() -> str:
    """Return the installed package version or a fallback value."""
    try:
        return metadata.version("repocontext")
    except metadata.PackageNotFoundError:
        return _FALLBACK_VERSION


def _print_repository_info(repository_info: RepositoryInfo) -> None:
    """Display repository information for the CLI."""
    print("Repository info:")
    name_display = repository_info.name if repository_info.name is not None else "unknown"
    print(f"  Name: {name_display}")
    print(f"  Root: {repository_info.root_path}")
    print(f"  Current directory is root: {'yes' if repository_info.is_current_directory_root else 'no'}")
    branch_display = repository_info.branch if repository_info.branch is not None else "unknown"
    print(f"  Branch: {branch_display}")
    commit_display = repository_info.commit_hash if repository_info.commit_hash is not None else "unknown"
    print(f"  Commit: {commit_display}")
    short_commit_display = repository_info.short_commit_hash if repository_info.short_commit_hash is not None else "unknown"
    print(f"  Short commit: {short_commit_display}")
    remote_display = repository_info.remote_url if repository_info.remote_url is not None else "none"
    print(f"  Remote: {remote_display}")
    dirty_status = repository_info.is_dirty
    if dirty_status is None:
        print("  Dirty: unknown")
    else:
        print(f"  Dirty: {'yes' if dirty_status else 'no'}")
    commit_metadata = repository_info.commit_metadata
    if commit_metadata is None:
        print("  Commit author: unknown")
        print("  Commit date: unknown")
        print("  Commit subject: unknown")
    else:
        author_name = commit_metadata.author_name or "unknown"
        author_email = commit_metadata.author_email or "unknown"
        commit_date = commit_metadata.commit_date or "unknown"
        subject = commit_metadata.subject or "unknown"
        print(f"  Commit author: {author_name} <{author_email}>")
        print(f"  Commit date: {commit_date}")
        print(f"  Commit subject: {subject}")
    print(f"  Tracked files: {len(repository_info.tracked_files)}")


def _find_repository_root_or_report_error() -> Optional[Path]:
    repository_root = find_repository_root()
    if repository_root is None:
        print("Error: Could not determine the repository root.")
        return None
    return repository_root


def _handle_full_export_command(_args: argparse.Namespace) -> int:
    """Run the default Full Export command."""
    repository_root = _find_repository_root_or_report_error()
    if repository_root is None:
        return 1

    try:
        output_path = generate_full_export(repository_root)
    except OSError as exc:
        print(f"Error: Could not write full.txt: {exc}")
        return 1

    print(f"Wrote {output_path}")
    return 0


def _handle_info_command(_args: argparse.Namespace) -> int:
    """Run the repository info command."""
    repository_root = _find_repository_root_or_report_error()
    if repository_root is None:
        return 1

    repository_info = get_repository_info(repository_root)
    _print_repository_info(repository_info)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(prog="repocontext")
    parser.add_argument("--version", action="version", version=_determine_version())

    subparsers = parser.add_subparsers(dest="command")

    info_parser = subparsers.add_parser("info", help="Show repository info")
    info_parser.set_defaults(handler=_handle_info_command)

    parser.set_defaults(handler=_handle_full_export_command)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    return arguments.handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
