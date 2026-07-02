"""Path normalization helpers for RepoDossier's structured export model."""

from __future__ import annotations

from pathlib import PurePosixPath


def normalize_export_path(path: str) -> str:
    """Normalize a repository-relative export path.

    Export model paths are always POSIX-style and repository-relative.
    This helper is intentionally conservative: absolute paths and paths
    escaping the repository are rejected.
    """

    raw_path = str(path).strip().replace("\\", "/")

    if not raw_path:
        raise ValueError("export path must not be empty")

    if raw_path.startswith("/"):
        raise ValueError(f"export path must be relative: {path!r}")

    normalized_parts: list[str] = []

    for part in PurePosixPath(raw_path).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError(f"export path must not escape repository: {path!r}")
        normalized_parts.append(part)

    if not normalized_parts:
        raise ValueError("export path must not be empty")

    return "/".join(normalized_parts)


def normalize_export_paths(paths: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    """Normalize, deduplicate and sort export paths deterministically."""

    return tuple(sorted({normalize_export_path(path) for path in paths}))


def export_path_parent(path: str) -> str | None:
    """Return the normalized parent path or None for root-level files."""

    normalized = normalize_export_path(path)
    parent = PurePosixPath(normalized).parent

    if str(parent) == ".":
        return None

    return str(parent)


def export_path_name(path: str) -> str:
    """Return the final name component of a normalized export path."""

    return PurePosixPath(normalize_export_path(path)).name


def export_path_depth(path: str) -> int:
    """Return the number of path components in a normalized export path."""

    return len(PurePosixPath(normalize_export_path(path)).parts)


def export_path_sort_key(path: str) -> tuple[int, str]:
    """Return a deterministic sort key for export paths.

    Shallower paths sort before deeper paths. Paths at the same depth sort
    alphabetically.
    """

    normalized = normalize_export_path(path)
    return (export_path_depth(normalized), normalized)


def sort_export_paths(paths: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    """Normalize and sort export paths by depth and then alphabetically."""

    return tuple(sorted({normalize_export_path(path) for path in paths}, key=export_path_sort_key))


def ancestor_export_paths(path: str) -> tuple[str, ...]:
    """Return repository-relative ancestor directories for an export path."""

    normalized = normalize_export_path(path)
    parts = PurePosixPath(normalized).parts

    ancestors: list[str] = []
    for index in range(1, len(parts)):
        ancestors.append("/".join(parts[:index]))

    return tuple(ancestors)
