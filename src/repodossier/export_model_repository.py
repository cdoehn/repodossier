"""Repository metadata helpers for RepoDossier's structured export model."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from repodossier.export_model import RepositoryMetadata


def make_repository_metadata(
    *,
    root_path: str,
    root_name: str | None = None,
    git_branch: str | None = None,
    git_commit: str | None = None,
    git_dirty: bool | None = None,
) -> RepositoryMetadata:
    """Create normalized repository metadata for an export model."""

    normalized_root_path = normalize_repository_root_path(root_path)
    normalized_root_name = (
        normalize_repository_root_name(root_name)
        if root_name is not None
        else repository_name_from_root_path(normalized_root_path)
    )

    return RepositoryMetadata(
        root_path=normalized_root_path,
        root_name=normalized_root_name,
        git_branch=normalize_optional_text(git_branch),
        git_commit=normalize_optional_text(git_commit),
        git_dirty=git_dirty,
    )


def update_repository_git_metadata(
    metadata: RepositoryMetadata,
    *,
    git_branch: str | None = None,
    git_commit: str | None = None,
    git_dirty: bool | None = None,
) -> RepositoryMetadata:
    """Return a metadata copy with updated Git fields."""

    return replace(
        metadata,
        git_branch=(
            metadata.git_branch
            if git_branch is None
            else normalize_optional_text(git_branch)
        ),
        git_commit=(
            metadata.git_commit
            if git_commit is None
            else normalize_optional_text(git_commit)
        ),
        git_dirty=metadata.git_dirty if git_dirty is None else git_dirty,
    )


def repository_metadata_has_git(metadata: RepositoryMetadata) -> bool:
    """Return whether metadata contains any Git information."""

    return any(
        value is not None
        for value in (
            metadata.git_branch,
            metadata.git_commit,
            metadata.git_dirty,
        )
    )


def repository_metadata_display_name(metadata: RepositoryMetadata) -> str:
    """Return a stable human-readable repository name."""

    if metadata.git_branch:
        return f"{metadata.root_name} ({metadata.git_branch})"

    return metadata.root_name


def normalize_repository_root_path(root_path: str) -> str:
    """Normalize repository root path text without touching the filesystem."""

    normalized = str(root_path).strip().replace("\\", "/").rstrip("/")

    if not normalized:
        raise ValueError("repository root_path must not be empty")

    return normalized


def normalize_repository_root_name(root_name: str) -> str:
    """Normalize repository root name text."""

    normalized = str(root_name).strip().strip("/")

    if not normalized:
        raise ValueError("repository root_name must not be empty")

    return normalized


def repository_name_from_root_path(root_path: str) -> str:
    """Derive a repository name from a normalized root path."""

    normalized_root_path = normalize_repository_root_path(root_path)
    name = Path(normalized_root_path).name

    if not name:
        raise ValueError(
            "repository root_name could not be derived from root_path"
        )

    return normalize_repository_root_name(name)


def normalize_optional_text(value: str | None) -> str | None:
    """Normalize optional metadata text fields."""

    if value is None:
        return None

    stripped = str(value).strip()
    return stripped or None
