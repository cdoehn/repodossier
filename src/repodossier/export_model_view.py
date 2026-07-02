"""Renderer-facing view helpers for RepositoryExport models."""

from __future__ import annotations

from dataclasses import dataclass

from repodossier.export_model import ExportWarning, FileEntry, RepositoryExport
from repodossier.export_model_index import iter_known_files
from repodossier.export_model_manifest import (
    RepositoryExportManifest,
    repository_export_manifest,
)
from repodossier.export_model_sections import (
    export_section_title,
    repository_export_populated_sections,
    repository_export_section_presence,
    repository_export_sections,
)


@dataclass(frozen=True)
class RepositoryExportView:
    """Renderer-friendly view of a RepositoryExport."""

    export: RepositoryExport
    manifest: RepositoryExportManifest
    sections: tuple[str, ...]
    populated_sections: tuple[str, ...]
    section_presence: dict[str, bool]

    def section_title(self, section: str) -> str:
        """Return a human-readable title for a section identifier."""

        return export_section_title(section)

    def files_for_section(self, section: str) -> tuple[FileEntry, ...]:
        """Return files relevant for a renderer section."""

        return repository_export_files_for_section(self.export, section)

    def warning_lines(self) -> tuple[str, ...]:
        """Return warnings as compact renderer-ready lines."""

        return repository_export_warning_lines(self.export)


def repository_export_view(
    export: RepositoryExport,
    *,
    include_content_in_fingerprint: bool = False,
) -> RepositoryExportView:
    """Build a renderer-facing view of a RepositoryExport."""

    return RepositoryExportView(
        export=export,
        manifest=repository_export_manifest(
            export,
            include_content_in_fingerprint=include_content_in_fingerprint,
        ),
        sections=repository_export_sections(export),
        populated_sections=repository_export_populated_sections(export),
        section_presence=repository_export_section_presence(export),
    )


def repository_export_files_for_section(
    export: RepositoryExport,
    section: str,
) -> tuple[FileEntry, ...]:
    """Return the file entries relevant for a renderer section."""

    normalized = str(section).strip().lower().replace("-", "_").replace(" ", "_")

    if normalized in {
        "source_export",
        "document_export",
        "important_files",
        "documentation_files",
        "changed_file_contents",
    }:
        return export.files

    if normalized in {
        "file_summary",
        "changed_files_summary",
    }:
        return tuple(iter_known_files(export))

    if normalized == "truncated_files":
        return export.truncated_files

    if normalized in {
        "omitted_files",
        "deleted_files",
    }:
        return export.omitted_files

    return ()


def repository_export_warning_lines(
    export: RepositoryExport,
) -> tuple[str, ...]:
    """Return warnings as stable human-readable lines."""

    return tuple(
        _warning_to_line(warning)
        for warning in sorted(
            export.warnings,
            key=lambda item: (
                item.path or "",
                item.code or "",
                item.message,
            ),
        )
    )


def repository_export_section_titles(
    export: RepositoryExport,
) -> tuple[tuple[str, str], ...]:
    """Return section id/title pairs in export mode order."""

    return tuple(
        (section, export_section_title(section))
        for section in repository_export_sections(export)
    )


def _warning_to_line(warning: ExportWarning) -> str:
    parts: list[str] = []

    if warning.path:
        parts.append(warning.path)

    if warning.code:
        parts.append(f"[{warning.code}]")

    parts.append(warning.message)

    return " ".join(parts)
