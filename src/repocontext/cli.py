"""Command-line interface entrypoint for RepoContext."""

from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
from typing import Iterable, Optional

from .git import (
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
    repository_name = get_repository_name(repository_root)
    name_display = repository_name if repository_name is not None else "unknown"
    print(f"  Name: {name_display}")
    print(f"  Root: {repository_root}")
    is_root = Path.cwd().resolve() == repository_root
    print(f"  Current directory is root: {'yes' if is_root else 'no'}")
    current_branch = get_current_branch(repository_root)
    branch_display = current_branch if current_branch is not None else "unknown"
    print(f"  Branch: {branch_display}")
    current_commit = get_current_commit_hash(repository_root)
    commit_display = current_commit if current_commit is not None else "unknown"
    print(f"  Commit: {commit_display}")
    current_short_commit = get_current_short_commit_hash(repository_root)
    short_commit_display = current_short_commit if current_short_commit is not None else "unknown"
    print(f"  Short commit: {short_commit_display}")
    origin_remote_url = get_origin_remote_url(repository_root)
    remote_display = origin_remote_url if origin_remote_url is not None else "none"
    print(f"  Remote: {remote_display}")
    dirty_status = is_working_tree_dirty(repository_root)
    if dirty_status is None:
        print("  Dirty: unknown")
    else:
        print(f"  Dirty: {'yes' if dirty_status else 'no'}")
    commit_metadata = get_current_commit_metadata(repository_root)
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
    tracked_files = list_tracked_files(repository_root)
    print(f"  Tracked files: {len(tracked_files)}")
