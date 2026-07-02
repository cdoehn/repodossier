"""Tree builders for RepoDossier's structured export model."""

from __future__ import annotations

from collections.abc import Iterable

from repodossier.export_model import FileEntry, FileTreeEntry, RepositoryExport
from repodossier.export_model_index import iter_known_files
from repodossier.export_model_paths import (
    ancestor_export_paths,
    export_path_parent,
    normalize_export_path,
)


def build_file_tree_from_export(export: RepositoryExport) -> tuple[FileTreeEntry, ...]:
    """Build a deterministic repository tree from all known export files."""

    return build_file_tree(entry.path for entry in iter_known_files(export))


def build_file_tree_from_entries(
    entries: Iterable[FileEntry],
) -> tuple[FileTreeEntry, ...]:
    """Build a deterministic repository tree from file entries."""

    return build_file_tree(entry.path for entry in entries)


def build_file_tree(paths: Iterable[str]) -> tuple[FileTreeEntry, ...]:
    """Build a deterministic FileTreeEntry tree from repository-relative paths."""

    normalized_paths = tuple(sorted({normalize_export_path(path) for path in paths}))

    if not normalized_paths:
        return ()

    directory_paths = {
        ancestor
        for path in normalized_paths
        for ancestor in ancestor_export_paths(path)
    }

    conflicting_paths = sorted(set(normalized_paths) & directory_paths)
    if conflicting_paths:
        joined = ", ".join(conflicting_paths)
        raise ValueError(
            "export paths cannot be both files and directories: "
            f"{joined}"
        )

    return _build_children(
        parent=None,
        file_paths=set(normalized_paths),
        directory_paths=directory_paths,
    )


def flatten_file_tree(entries: Iterable[FileTreeEntry]) -> tuple[FileTreeEntry, ...]:
    """Return tree entries in deterministic pre-order traversal."""

    flattened: list[FileTreeEntry] = []

    for entry in entries:
        flattened.append(entry)
        flattened.extend(flatten_file_tree(entry.children))

    return tuple(flattened)


def tree_paths(entries: Iterable[FileTreeEntry]) -> tuple[str, ...]:
    """Return paths from a tree in deterministic pre-order traversal."""

    return tuple(entry.path for entry in flatten_file_tree(entries))


def _build_children(
    *,
    parent: str | None,
    file_paths: set[str],
    directory_paths: set[str],
) -> tuple[FileTreeEntry, ...]:
    child_directories = [
        path
        for path in directory_paths
        if export_path_parent(path) == parent
    ]
    child_files = [
        path
        for path in file_paths
        if export_path_parent(path) == parent
    ]

    entries: list[FileTreeEntry] = []

    for path in child_directories:
        entries.append(
            FileTreeEntry(
                path=path,
                entry_type="directory",
                children=_build_children(
                    parent=path,
                    file_paths=file_paths,
                    directory_paths=directory_paths,
                ),
            )
        )

    for path in child_files:
        entries.append(FileTreeEntry(path=path, entry_type="file"))

    return tuple(sorted(entries, key=lambda entry: entry.path))
