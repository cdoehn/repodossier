"""File inventory helpers for RepositoryExport models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from repodossier.export_model import FileEntry, RepositoryExport


FileInventoryGroup = Literal["files", "omitted_files", "truncated_files"]


@dataclass(frozen=True)
class FileInventoryEntry:
    """Compact file metadata for summaries and renderers."""

    path: str
    group: FileInventoryGroup
    language: str
    status: str
    text_status: str
    size_bytes: int
    line_count: int
    estimated_tokens: int
    reason: str | None = None


def repository_export_file_inventory(
    export: RepositoryExport,
) -> tuple[FileInventoryEntry, ...]:
    """Return a deterministic inventory of all known export files."""

    entries = (
        _inventory_entries_for_group(export.files, "files")
        + _inventory_entries_for_group(export.omitted_files, "omitted_files")
        + _inventory_entries_for_group(
            export.truncated_files,
            "truncated_files",
        )
    )

    return tuple(sorted(entries, key=lambda item: (item.path, item.group)))


def repository_export_file_inventory_by_group(
    export: RepositoryExport,
) -> dict[FileInventoryGroup, tuple[FileInventoryEntry, ...]]:
    """Return file inventory entries grouped by export file group."""

    inventory = repository_export_file_inventory(export)

    return {
        "files": tuple(entry for entry in inventory if entry.group == "files"),
        "omitted_files": tuple(
            entry for entry in inventory if entry.group == "omitted_files"
        ),
        "truncated_files": tuple(
            entry for entry in inventory if entry.group == "truncated_files"
        ),
    }


def repository_export_file_inventory_to_dicts(
    export: RepositoryExport,
) -> tuple[dict[str, object], ...]:
    """Return the file inventory as plain JSON-ready dictionaries."""

    return tuple(
        asdict(entry)
        for entry in repository_export_file_inventory(export)
    )


def repository_export_file_inventory_lines(
    export: RepositoryExport,
) -> tuple[str, ...]:
    """Return a stable, human-readable file inventory."""

    return tuple(
        _inventory_entry_to_line(entry)
        for entry in repository_export_file_inventory(export)
    )


def _inventory_entries_for_group(
    entries: tuple[FileEntry, ...],
    group: FileInventoryGroup,
) -> tuple[FileInventoryEntry, ...]:
    return tuple(
        FileInventoryEntry(
            path=entry.path,
            group=group,
            language=entry.language,
            status=entry.status,
            text_status=entry.text_status,
            size_bytes=entry.size_bytes,
            line_count=entry.line_count,
            estimated_tokens=entry.estimated_tokens,
            reason=entry.reason,
        )
        for entry in entries
    )


def _inventory_entry_to_line(entry: FileInventoryEntry) -> str:
    parts = [
        entry.path,
        f"group={entry.group}",
        f"language={entry.language}",
        f"status={entry.status}",
        f"text={entry.text_status}",
        f"lines={entry.line_count}",
        f"tokens={entry.estimated_tokens}",
        f"bytes={entry.size_bytes}",
    ]

    if entry.reason:
        parts.append(f"reason={entry.reason}")

    return " | ".join(parts)
