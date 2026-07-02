"""Mode-aware section helpers for structured export renderers."""

from __future__ import annotations

from repodossier.export_model import RepositoryExport
from repodossier.export_model_modes import (
    MODE_DEFAULT_SECTIONS,
    export_mode_default_sections,
    normalize_export_mode,
)


SECTION_TITLES: dict[str, str] = {
    "call_graph": "Call Graph",
    "changed_file_contents": "Changed File Contents",
    "changed_files_summary": "Changed Files Summary",
    "configuration": "Configuration",
    "database_schema": "Database Schema",
    "deleted_files": "Deleted Files",
    "dependencies": "Dependencies",
    "documentation_files": "Documentation Files",
    "file_summary": "File Summary",
    "git_diff": "Git Diff",
    "header": "Header",
    "important_files": "Important Files",
    "import_graph": "Import Graph",
    "project_summary": "Project Summary",
    "quick_start": "Quick Start",
    "recent_commits": "Recent Commits",
    "repository_metadata": "Repository Metadata",
    "repository_tree": "Repository Tree",
    "secret_detection": "Secret Detection",
    "source_export": "Source Export",
    "summary": "Summary",
    "symbol_index": "Symbol Index",
    "test_map": "Test Map",
    "warnings": "Warnings",
}


def normalize_export_section(section: str) -> str:
    """Normalize a renderer/export section identifier."""

    normalized = str(section).strip().lower()
    normalized = normalized.replace("-", "_").replace(" ", "_")

    while "__" in normalized:
        normalized = normalized.replace("__", "_")

    normalized = normalized.strip("_")

    if not normalized:
        raise ValueError("export section must not be empty")

    return normalized


def known_export_sections() -> tuple[str, ...]:
    """Return all currently known section identifiers."""

    mode_sections = {
        section
        for sections in MODE_DEFAULT_SECTIONS.values()
        for section in sections
    }
    return tuple(sorted(set(SECTION_TITLES) | mode_sections))


def export_section_title(section: str) -> str:
    """Return a human-readable title for an export section."""

    normalized = normalize_export_section(section)
    return SECTION_TITLES.get(
        normalized,
        normalized.replace("_", " ").title(),
    )


def export_mode_sections(mode: str) -> tuple[str, ...]:
    """Return the default section order for an export mode."""

    return export_mode_default_sections(normalize_export_mode(mode))


def repository_export_sections(export: RepositoryExport) -> tuple[str, ...]:
    """Return the default section order for a RepositoryExport."""

    return export_mode_sections(export.mode)


def repository_export_section_presence(
    export: RepositoryExport,
) -> dict[str, bool]:
    """Return whether each default section has data or should be rendered."""

    return {
        section: _section_has_content(export, section)
        for section in repository_export_sections(export)
    }


def repository_export_populated_sections(
    export: RepositoryExport,
) -> tuple[str, ...]:
    """Return default sections that are populated, preserving mode order."""

    presence = repository_export_section_presence(export)
    return tuple(
        section
        for section in repository_export_sections(export)
        if presence[section]
    )


def repository_export_has_section(
    export: RepositoryExport,
    section: str,
    *,
    require_populated: bool = True,
) -> bool:
    """Return whether an export contains a section in its mode definition."""

    normalized = normalize_export_section(section)
    sections = repository_export_sections(export)

    if normalized not in sections:
        return False

    if not require_populated:
        return True

    return repository_export_section_presence(export)[normalized]


def _section_has_content(export: RepositoryExport, section: str) -> bool:
    normalized = normalize_export_section(section)

    if normalized in {
        "header",
        "quick_start",
        "project_summary",
        "repository_metadata",
        "summary",
    }:
        return True

    if normalized == "configuration":
        return _has_configuration(export)

    if normalized in {
        "file_summary",
        "important_files",
        "documentation_files",
        "changed_files_summary",
    }:
        return _has_known_files(export)

    if normalized == "repository_tree":
        return bool(export.tree)

    if normalized in {
        "source_export",
        "document_export",
        "changed_file_contents",
    }:
        return bool(export.files)

    if normalized == "dependencies":
        return bool(export.dependencies.items)

    if normalized == "database_schema":
        return bool(export.database_schema.items)

    if normalized == "secret_detection":
        return bool(
            export.secret_detection.findings
            or export.secret_detection.masked_files
        )

    if normalized == "symbol_index":
        return bool(export.symbol_index.symbols)

    if normalized == "import_graph":
        return bool(export.import_graph.edges)

    if normalized == "call_graph":
        return bool(export.call_graph.edges)

    if normalized == "test_map":
        return bool(export.test_map.mappings)

    if normalized == "recent_commits":
        return bool(export.recent_commits.commits)

    if normalized == "warnings":
        return bool(export.warnings)

    if normalized in {"git_diff", "deleted_files"}:
        return False

    return False


def _has_configuration(export: RepositoryExport) -> bool:
    configuration = export.configuration
    return bool(
        configuration.config_active
        or configuration.config_path
        or configuration.include_paths
        or configuration.include_globs
        or configuration.exclude_paths
        or configuration.exclude_globs
        or configuration.limits
        or configuration.split_settings
    )


def _has_known_files(export: RepositoryExport) -> bool:
    return bool(
        export.files
        or export.omitted_files
        or export.truncated_files
    )
