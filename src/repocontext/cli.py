"""Command-line interface entrypoint for RepoContext."""

from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
from typing import Iterable, Optional

from .git import (
    find_repository_root,
    get_repository_info,
    get_current_branch,
    get_current_commit_hash,
    get_current_commit_metadata,
    get_current_short_commit_hash,
    get_origin_remote_url,
    get_repository_name,
    is_working_tree_dirty,
    list_tracked_files,
)


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
    repository_info = get_repository_info(repository_root)
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
