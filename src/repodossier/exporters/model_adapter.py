"""Adapter helpers for building RepositoryExport models.

The functions in this module are intentionally model-only. They convert already
collected data into RepositoryExport instances and must not scan repositories,
inspect Git state, or run analyzers.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from repodossier.export_model import (
    ExportSummary,
    ExportWarning,
    FileEntry,
    FileTreeEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
)


def build_repository_export_from_entries(
    *,
    mode: str,
    root_path: str | Path,
    files: Iterable[FileEntry],
    root_name: str | None = None,
    omitted_files: Iterable[FileEntry] = (),
    truncated_files: Iterable[FileEntry] = (),
    warnings: Iterable[ExportWarning] = (),
    git_branch: str | None = None,
    git_commit: str | None = None,
    git_dirty: bool | None = None,
) -> RepositoryExport:
    """Build a RepositoryExport from already-collected FileEntry objects."""

    file_entries = tuple(files)
    omitted_entries = tuple(omitted_files)
    truncated_entries = tuple(truncated_files)
    warning_entries = tuple(warnings)
    root_path_text = str(root_path)
    resolved_root_name = root_name or Path(root_path_text).name or root_path_text

    included_entries = tuple(
        entry for entry in file_entries if entry.status == "included"
    )
    all_entries = file_entries + omitted_entries + truncated_entries

    summary = ExportSummary(
        total_tracked_files=len(all_entries),
        scanned_files=len(all_entries),
        exported_text_files=len(included_entries),
        skipped_binary_files=sum(
            1
            for entry in omitted_entries
            if entry.text_status == "binary" or entry.language == "unknown"
        ),
        errored_files=sum(1 for entry in all_entries if entry.status == "error"),
        total_lines=sum(entry.line_count for entry in included_entries),
        estimated_tokens=sum(entry.estimated_tokens for entry in included_entries),
        file_type_statistics=_file_type_statistics(all_entries),
        language_statistics=LanguageStatistics(_language_statistics(included_entries)),
    )

    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(
            root_path=root_path_text,
            root_name=resolved_root_name,
            git_branch=git_branch,
            git_commit=git_commit,
            git_dirty=git_dirty,
        ),
        summary=summary,
        files=file_entries,
        omitted_files=omitted_entries,
        truncated_files=truncated_entries,
        warnings=warning_entries,
        tree=build_file_tree_from_entries(all_entries),
    )



def build_file_tree_from_entries(entries: Iterable[FileEntry]) -> tuple[FileTreeEntry, ...]:
    """Build a deterministic FileTreeEntry tree from FileEntry paths."""

    root: dict[str, dict[str, object]] = {}

    for entry in entries:
        parts = tuple(part for part in Path(entry.path).parts if part not in {"", "."})
        if not parts:
            continue

        node = root
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child

        node.setdefault(parts[-1], None)

    return _tree_nodes_from_mapping(root, prefix="")


def _tree_nodes_from_mapping(
    mapping: Mapping[str, object],
    *,
    prefix: str,
) -> tuple[FileTreeEntry, ...]:
    nodes: list[FileTreeEntry] = []

    for name in sorted(mapping):
        value = mapping[name]
        path = f"{prefix}/{name}" if prefix else name

        if isinstance(value, Mapping):
            nodes.append(
                FileTreeEntry(
                    path=path,
                    entry_type="directory",
                    children=_tree_nodes_from_mapping(value, prefix=path),
                )
            )
        else:
            nodes.append(FileTreeEntry(path=path, entry_type="file"))

    return tuple(nodes)


def file_entry_from_mapping(data: Mapping[str, Any]) -> FileEntry:
    """Create a FileEntry from a mapping produced by an existing collector."""

    return FileEntry(
        path=str(data["path"]),
        language=str(data.get("language") or "unknown"),
        size_bytes=int(data.get("size_bytes") or 0),
        line_count=int(data.get("line_count") or 0),
        estimated_tokens=int(data.get("estimated_tokens") or 0),
        text_status=str(data.get("text_status") or "text"),
        status=str(data.get("status") or "included"),
        content=data.get("content"),
        masked_content=data.get("masked_content"),
        reason=data.get("reason"),
    )


def file_entry_from_object(value: object) -> FileEntry:
    """Create a FileEntry from an object with FileEntry-like attributes."""

    if isinstance(value, FileEntry):
        return value

    if isinstance(value, Mapping):
        return file_entry_from_mapping(value)

    return FileEntry(
        path=str(_get_value(value, "path")),
        language=str(_get_value(value, "language", "unknown") or "unknown"),
        size_bytes=int(_get_value(value, "size_bytes", 0) or 0),
        line_count=int(_get_value(value, "line_count", 0) or 0),
        estimated_tokens=int(_get_value(value, "estimated_tokens", 0) or 0),
        text_status=str(_get_value(value, "text_status", "text") or "text"),
        status=str(_get_value(value, "status", "included") or "included"),
        content=_get_value(value, "content", None),
        masked_content=_get_value(value, "masked_content", None),
        reason=_get_value(value, "reason", None),
    )


def file_entries_from_objects(values: Iterable[object]) -> tuple[FileEntry, ...]:
    """Convert an iterable of legacy scan objects or mappings into FileEntry objects."""

    return tuple(file_entry_from_object(value) for value in values)


def export_warning_from_mapping(data: Mapping[str, Any]) -> ExportWarning:
    """Create an ExportWarning from a mapping."""

    return ExportWarning(
        message=str(data["message"]),
        path=data.get("path"),
        code=data.get("code"),
    )


def export_warning_from_object(value: object) -> ExportWarning:
    """Create an ExportWarning from an object with warning-like attributes."""

    if isinstance(value, ExportWarning):
        return value

    if isinstance(value, Mapping):
        return export_warning_from_mapping(value)

    return ExportWarning(
        message=str(_get_value(value, "message")),
        path=_get_value(value, "path", None),
        code=_get_value(value, "code", None),
    )


def export_warnings_from_objects(values: Iterable[object]) -> tuple[ExportWarning, ...]:
    """Convert warning-like objects or mappings into ExportWarning objects."""

    return tuple(export_warning_from_object(value) for value in values)


def _get_value(value: object, name: str, default: object = None) -> object:
    return getattr(value, name, default)


def _file_type_statistics(entries: Iterable[FileEntry]) -> dict[str, int]:
    statistics: dict[str, int] = {}

    for entry in entries:
        suffix = Path(entry.path).suffix
        statistics[suffix] = statistics.get(suffix, 0) + 1

    return statistics


def _language_statistics(entries: Iterable[FileEntry]) -> dict[str, int]:
    statistics: dict[str, int] = {}

    for entry in entries:
        language = entry.language or "unknown"
        statistics[language] = statistics.get(language, 0) + 1

    return statistics
