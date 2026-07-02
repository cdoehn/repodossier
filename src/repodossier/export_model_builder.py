"""Helpers for assembling the structured RepoDossier export model.

This module intentionally stays renderer-independent. It only transforms
already-collected file metadata into model objects that Markdown/XML
renderers can consume later.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from repodossier.export_model import (
    ExportConfigurationSummary,
    ExportMode,
    ExportSummary,
    FileEntry,
    FileTreeEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
)


NO_EXTENSION_LABEL = "[no extension]"


@dataclass
class _MutableTreeNode:
    """Small internal tree node used before creating frozen model entries."""

    children: dict[str, "_MutableTreeNode"] = field(default_factory=dict)
    is_file: bool = False


def _normalize_export_path(path: str) -> str:
    """Normalize a repository-relative path for deterministic exports."""

    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def _file_type_label(path: str) -> str:
    suffix = PurePosixPath(path).suffix
    return suffix if suffix else NO_EXTENSION_LABEL


def summarize_file_entries(files: Iterable[FileEntry]) -> ExportSummary:
    """Build deterministic aggregate statistics from file entries."""

    entries = tuple(files)
    file_type_statistics: dict[str, int] = {}
    language_statistics = LanguageStatistics()

    for entry in entries:
        file_type = _file_type_label(entry.path)
        file_type_statistics[file_type] = file_type_statistics.get(file_type, 0) + 1
        language_statistics = language_statistics.increment(entry.language)

    return ExportSummary(
        total_tracked_files=len(entries),
        scanned_files=len(entries),
        exported_text_files=sum(
            1
            for entry in entries
            if entry.status == "included" and entry.text_status == "text"
        ),
        skipped_binary_files=sum(
            1
            for entry in entries
            if entry.status == "skipped" and entry.text_status == "binary"
        ),
        errored_files=sum(1 for entry in entries if entry.status == "error"),
        total_lines=sum(entry.line_count for entry in entries),
        estimated_tokens=sum(entry.estimated_tokens for entry in entries),
        file_type_statistics=dict(sorted(file_type_statistics.items())),
        language_statistics=language_statistics,
    )


def build_file_tree_entries(paths: Iterable[str]) -> tuple[FileTreeEntry, ...]:
    """Create a deterministic repository tree from relative file paths."""

    root = _MutableTreeNode()

    for raw_path in paths:
        normalized = _normalize_export_path(raw_path)
        if not normalized:
            continue

        parts = normalized.split("/")
        node = root
        for part in parts[:-1]:
            node = node.children.setdefault(part, _MutableTreeNode())
        node.children.setdefault(parts[-1], _MutableTreeNode()).is_file = True

    return _freeze_children("", root)


def _freeze_children(parent_path: str, node: _MutableTreeNode) -> tuple[FileTreeEntry, ...]:
    entries: list[FileTreeEntry] = []

    def sort_key(item: tuple[str, _MutableTreeNode]) -> tuple[int, str, str]:
        name, child = item
        return (1 if child.is_file else 0, name.lower(), name)

    for name, child in sorted(node.children.items(), key=sort_key):
        path = f"{parent_path}/{name}" if parent_path else name
        if child.is_file:
            entries.append(FileTreeEntry(path=path, entry_type="file"))
        else:
            entries.append(
                FileTreeEntry(
                    path=path,
                    entry_type="directory",
                    children=_freeze_children(path, child),
                )
            )

    return tuple(entries)


def create_repository_export(
    *,
    mode: ExportMode,
    root_path: str,
    root_name: str,
    files: Iterable[FileEntry] = (),
    configuration: ExportConfigurationSummary | None = None,
    git_branch: str | None = None,
    git_commit: str | None = None,
    git_dirty: bool | None = None,
) -> RepositoryExport:
    """Assemble a structured export from already collected file entries."""

    sorted_files = tuple(sorted(files, key=lambda entry: entry.path))
    included_files = tuple(entry for entry in sorted_files if entry.status == "included")
    omitted_files = tuple(
        entry for entry in sorted_files if entry.status in {"skipped", "error"}
    )
    truncated_files = tuple(entry for entry in sorted_files if entry.status == "truncated")

    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(
            root_path=root_path,
            root_name=root_name,
            git_branch=git_branch,
            git_commit=git_commit,
            git_dirty=git_dirty,
        ),
        configuration=configuration or ExportConfigurationSummary(),
        summary=summarize_file_entries(sorted_files),
        tree=build_file_tree_entries(entry.path for entry in sorted_files),
        files=included_files,
        omitted_files=omitted_files,
        truncated_files=truncated_files,
    )
