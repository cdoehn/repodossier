"""Helpers for assembling the structured RepoDossier export model.

This module intentionally stays renderer-independent. It only transforms
already-collected file metadata into model objects that Markdown/XML
renderers can consume later.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from repodossier.export_model import (
    ExportConfigurationSummary,
    ExportMode,
    ExportSummary,
    ExportWarning,
    FileEntry,
    FileStatus,
    FileTreeEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
    TextStatus,
)
from repodossier.export_model_factory import make_repository_export
from repodossier.git import (
    get_current_branch,
    get_current_commit_hash,
    get_repository_name,
    is_working_tree_dirty,
)
from repodossier.models import FileInfo
from repodossier.scanner import RepositoryScanner


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



def file_entry_from_scan_info(
    file_info: FileInfo,
    *,
    include_content: bool = True,
) -> FileEntry:
    """Convert a real scanner FileInfo object into a structured FileEntry."""

    path = _normalize_export_path(str(file_info.relative_path))
    language = (file_info.language or "unknown").strip() or "unknown"
    status = _file_status_from_scan_info(file_info)
    text_status = _text_status_from_scan_info(file_info)
    reason = _reason_from_scan_info(file_info)

    content = None
    if include_content and status == "included" and text_status == "text":
        content = file_info.content

    return FileEntry(
        path=path,
        language=language,
        size_bytes=_non_negative_int(file_info.size_bytes),
        line_count=_non_negative_int(file_info.line_count),
        estimated_tokens=_non_negative_int(file_info.estimated_tokens),
        text_status=text_status,
        status=status,
        content=content,
        reason=reason,
    )


def file_entries_from_scan_infos(
    file_infos: Iterable[FileInfo],
    *,
    include_content: bool = True,
) -> tuple[FileEntry, ...]:
    """Build deterministic FileEntry objects from scanner results."""

    entries = tuple(
        file_entry_from_scan_info(
            file_info,
            include_content=include_content,
        )
        for file_info in file_infos
    )

    return tuple(sorted(entries, key=lambda entry: entry.path))


def build_repository_export_from_scan(
    root_path: Path | str,
    *,
    mode: ExportMode = "full",
    scanner: RepositoryScanner | None = None,
    file_infos: Iterable[FileInfo] | None = None,
    configuration: ExportConfigurationSummary | None = None,
    include_content: bool = True,
    include_git_metadata: bool = True,
    validate: bool = True,
) -> RepositoryExport:
    """Scan a repository and assemble a finalized RepositoryExport model.

    This is the first real bridge from the existing scanner layer into the
    structured Milestone 3 export model. It intentionally does not render
    Markdown, XML or any other output format.
    """

    resolved_root = Path(root_path).resolve()

    if file_infos is None:
        active_scanner = scanner or RepositoryScanner()
        scanned_infos = tuple(active_scanner.scan(resolved_root))
    else:
        scanned_infos = tuple(file_infos)

    entries = file_entries_from_scan_infos(
        scanned_infos,
        include_content=include_content,
    )

    git_branch: str | None = None
    git_commit: str | None = None
    git_dirty: bool | None = None

    if include_git_metadata:
        git_branch = _safe_git_value(get_current_branch, resolved_root)
        git_commit = _safe_git_value(get_current_commit_hash, resolved_root)
        git_dirty = _safe_git_value(is_working_tree_dirty, resolved_root)

    return make_repository_export(
        mode=mode,
        root_path=str(resolved_root),
        root_name=get_repository_name(resolved_root) or resolved_root.name or ".",
        git_branch=git_branch,
        git_commit=git_commit,
        git_dirty=git_dirty,
        configuration=configuration,
        files=tuple(entry for entry in entries if entry.status == "included"),
        omitted_files=tuple(
            entry
            for entry in entries
            if entry.status in {"skipped", "error"}
            or entry.text_status == "binary"
        ),
        truncated_files=tuple(
            entry for entry in entries if entry.status == "truncated"
        ),
        warnings=_warnings_from_scan_infos(scanned_infos),
        validate=validate,
    )


def _file_status_from_scan_info(file_info: FileInfo) -> FileStatus:
    if file_info.error:
        return "error"

    if file_info.is_binary:
        return "skipped"

    if file_info.is_text is False:
        return "skipped"

    return "included"


def _text_status_from_scan_info(file_info: FileInfo) -> TextStatus:
    if file_info.is_binary:
        return "binary"

    return "text"


def _reason_from_scan_info(file_info: FileInfo) -> str | None:
    if file_info.error:
        return str(file_info.error)

    if file_info.is_binary:
        return "binary file"

    if file_info.is_text is False:
        return "non-text file"

    return None


def _warnings_from_scan_infos(
    file_infos: Iterable[FileInfo],
) -> tuple[ExportWarning, ...]:
    warnings = [
        ExportWarning(
            path=_normalize_export_path(str(file_info.relative_path)),
            code="scan-error",
            message=str(file_info.error),
        )
        for file_info in file_infos
        if file_info.error
    ]

    return tuple(sorted(warnings, key=lambda warning: warning.path or ""))


def _non_negative_int(value: int | None) -> int:
    if value is None:
        return 0

    return max(0, int(value))


def _safe_git_value(callback, root_path: Path):
    try:
        return callback(root_path)
    except Exception:
        return None


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
