"""Summary builders for RepoDossier's structured export model."""

from __future__ import annotations

from pathlib import PurePosixPath

from repodossier.export_model import ExportSummary, FileEntry, LanguageStatistics, RepositoryExport
from repodossier.export_model_index import iter_known_files


def build_export_summary_from_export(export: RepositoryExport) -> ExportSummary:
    """Build deterministic export summary statistics from a RepositoryExport."""

    return build_export_summary(iter_known_files(export))


def build_export_summary(files: tuple[FileEntry, ...]) -> ExportSummary:
    """Build deterministic summary statistics from file entries."""

    language_counts = language_statistics_from_files(files)
    file_type_counts = file_type_statistics_from_files(files)

    return ExportSummary(
        total_tracked_files=len(files),
        scanned_files=len(files),
        exported_text_files=count_files_by_status(files, "included"),
        skipped_binary_files=sum(
            1
            for entry in files
            if entry.text_status == "binary" or entry.status == "skipped"
        ),
        errored_files=count_files_by_status(files, "error"),
        total_lines=sum(entry.line_count for entry in files),
        estimated_tokens=sum(entry.estimated_tokens for entry in files),
        file_type_statistics=file_type_counts,
        language_statistics=LanguageStatistics(counts=language_counts),
    )


def language_statistics_from_files(files: tuple[FileEntry, ...]) -> dict[str, int]:
    """Return deterministic language counts from file entries."""

    counts: dict[str, int] = {}

    for entry in files:
        language = entry.language or "unknown"
        counts[language] = counts.get(language, 0) + 1

    return dict(sorted(counts.items()))


def file_type_statistics_from_files(files: tuple[FileEntry, ...]) -> dict[str, int]:
    """Return deterministic file type counts from file entries."""

    counts: dict[str, int] = {}

    for entry in files:
        suffix = _file_type_label(entry.path)
        counts[suffix] = counts.get(suffix, 0) + 1

    return dict(sorted(counts.items()))


def count_files_by_status(files: tuple[FileEntry, ...], status: str) -> int:
    """Count files with a specific export status."""

    return sum(1 for entry in files if entry.status == status)


def count_files_by_language(files: tuple[FileEntry, ...], language: str) -> int:
    """Count files with a specific language label."""

    return sum(1 for entry in files if entry.language == language)


def _file_type_label(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()

    if suffix:
        return suffix

    name = PurePosixPath(path).name
    return name if name else "<unknown>"
