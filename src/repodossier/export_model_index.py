"""Deterministic query helpers for RepoDossier's structured export model."""

from __future__ import annotations

from collections.abc import Iterable

from repodossier.export_model import FileEntry, FileStatus, RepositoryExport


def iter_known_files(export: RepositoryExport) -> tuple[FileEntry, ...]:
    """Return all known files in deterministic path order.

    The returned tuple combines included, omitted and truncated file groups.
    Duplicate paths are collapsed with this precedence:

    1. files
    2. truncated_files
    3. omitted_files

    That mirrors the model's primary-to-secondary file groups while still
    giving renderers a stable one-file-per-path view.
    """

    by_path: dict[str, FileEntry] = {}

    for group in (export.omitted_files, export.truncated_files, export.files):
        for entry in group:
            by_path[entry.path] = entry

    return tuple(by_path[path] for path in sorted(by_path))


def file_index_by_path(export: RepositoryExport) -> dict[str, FileEntry]:
    """Return a deterministic mapping from path to file entry."""

    return {entry.path: entry for entry in iter_known_files(export)}


def get_file_entry(export: RepositoryExport, path: str) -> FileEntry | None:
    """Return a file entry by path, or None when the path is unknown."""

    return file_index_by_path(export).get(path)


def files_by_language(export: RepositoryExport) -> dict[str, tuple[FileEntry, ...]]:
    """Group known files by language label using deterministic ordering."""

    grouped: dict[str, list[FileEntry]] = {}

    for entry in iter_known_files(export):
        grouped.setdefault(entry.language, []).append(entry)

    return {
        language: tuple(sorted(entries, key=lambda item: item.path))
        for language, entries in sorted(grouped.items())
    }


def files_by_status(export: RepositoryExport) -> dict[FileStatus, tuple[FileEntry, ...]]:
    """Group known files by export status using deterministic ordering."""

    grouped: dict[FileStatus, list[FileEntry]] = {}

    for entry in iter_known_files(export):
        grouped.setdefault(entry.status, []).append(entry)

    return {
        status: tuple(sorted(entries, key=lambda item: item.path))
        for status, entries in sorted(grouped.items())
    }


def filter_files_by_status(
    export: RepositoryExport,
    statuses: Iterable[FileStatus],
) -> tuple[FileEntry, ...]:
    """Return files whose status is in statuses, sorted by path."""

    wanted = set(statuses)
    return tuple(
        entry
        for entry in iter_known_files(export)
        if entry.status in wanted
    )


def filter_files_by_language(
    export: RepositoryExport,
    languages: Iterable[str],
) -> tuple[FileEntry, ...]:
    """Return files whose language is in languages, sorted by path."""

    wanted = set(languages)
    return tuple(
        entry
        for entry in iter_known_files(export)
        if entry.language in wanted
    )


def language_counts_from_export(export: RepositoryExport) -> dict[str, int]:
    """Return language counts derived from known files."""

    counts: dict[str, int] = {}

    for entry in iter_known_files(export):
        counts[entry.language] = counts.get(entry.language, 0) + 1

    return dict(sorted(counts.items()))


def status_counts_from_export(export: RepositoryExport) -> dict[str, int]:
    """Return export status counts derived from known files."""

    counts: dict[str, int] = {}

    for entry in iter_known_files(export):
        counts[entry.status] = counts.get(entry.status, 0) + 1

    return dict(sorted(counts.items()))
