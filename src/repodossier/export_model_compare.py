"""Comparison helpers for structured RepositoryExport models."""

from __future__ import annotations

from dataclasses import dataclass

from repodossier.export_model import FileEntry, RepositoryExport
from repodossier.export_model_index import file_index_by_path
from repodossier.export_model_snapshot import repository_export_fingerprint


@dataclass(frozen=True)
class FileEntryChange:
    """A changed file entry between two RepositoryExport models."""

    path: str
    changed_fields: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryExportComparison:
    """Deterministic comparison result for two RepositoryExport models."""

    same: bool
    same_fingerprint: bool
    before_fingerprint: str
    after_fingerprint: str
    added_paths: tuple[str, ...]
    removed_paths: tuple[str, ...]
    changed_files: tuple[FileEntryChange, ...]
    mode_changed: bool
    repository_changed: bool
    warning_count_changed: bool

    def changed_paths(self) -> tuple[str, ...]:
        """Return all paths that were added, removed or changed."""

        return tuple(
            sorted(
                set(self.added_paths)
                | set(self.removed_paths)
                | {change.path for change in self.changed_files}
            )
        )


FILE_COMPARE_FIELDS: tuple[str, ...] = (
    "language",
    "size_bytes",
    "line_count",
    "estimated_tokens",
    "text_status",
    "status",
    "content",
    "masked_content",
    "reason",
)


def compare_repository_exports(
    before: RepositoryExport,
    after: RepositoryExport,
    *,
    include_content: bool = True,
) -> RepositoryExportComparison:
    """Compare two RepositoryExport models deterministically."""

    before_fingerprint = repository_export_fingerprint(
        before,
        include_content=include_content,
    )
    after_fingerprint = repository_export_fingerprint(
        after,
        include_content=include_content,
    )

    before_files = file_index_by_path(before)
    after_files = file_index_by_path(after)

    before_paths = set(before_files)
    after_paths = set(after_files)

    added_paths = tuple(sorted(after_paths - before_paths))
    removed_paths = tuple(sorted(before_paths - after_paths))
    changed_files = tuple(
        FileEntryChange(path=path, changed_fields=fields)
        for path, fields in (
            (
                path,
                compare_file_entries(
                    before_files[path],
                    after_files[path],
                    include_content=include_content,
                ),
            )
            for path in sorted(before_paths & after_paths)
        )
        if fields
    )

    mode_changed = before.mode != after.mode
    repository_changed = before.repository != after.repository
    warning_count_changed = len(before.warnings) != len(after.warnings)
    same_fingerprint = before_fingerprint == after_fingerprint

    same = (
        same_fingerprint
        and not added_paths
        and not removed_paths
        and not changed_files
        and not mode_changed
        and not repository_changed
        and not warning_count_changed
    )

    return RepositoryExportComparison(
        same=same,
        same_fingerprint=same_fingerprint,
        before_fingerprint=before_fingerprint,
        after_fingerprint=after_fingerprint,
        added_paths=added_paths,
        removed_paths=removed_paths,
        changed_files=changed_files,
        mode_changed=mode_changed,
        repository_changed=repository_changed,
        warning_count_changed=warning_count_changed,
    )


def compare_file_entries(
    before: FileEntry,
    after: FileEntry,
    *,
    include_content: bool = True,
) -> tuple[str, ...]:
    """Return FileEntry fields that differ."""

    changed_fields: list[str] = []

    for field_name in FILE_COMPARE_FIELDS:
        if not include_content and field_name in {"content", "masked_content"}:
            continue

        if getattr(before, field_name) != getattr(after, field_name):
            changed_fields.append(field_name)

    return tuple(changed_fields)


def repository_exports_have_same_paths(
    before: RepositoryExport,
    after: RepositoryExport,
) -> bool:
    """Return whether two exports know the same file paths."""

    return set(file_index_by_path(before)) == set(file_index_by_path(after))


def repository_export_path_delta(
    before: RepositoryExport,
    after: RepositoryExport,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return added and removed paths between two exports."""

    before_paths = set(file_index_by_path(before))
    after_paths = set(file_index_by_path(after))

    return (
        tuple(sorted(after_paths - before_paths)),
        tuple(sorted(before_paths - after_paths)),
    )
