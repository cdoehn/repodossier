"""Export mode helpers for RepoDossier's structured export model."""

from __future__ import annotations

from repodossier.export_model import ExportMode, RepositoryExport


VALID_EXPORT_MODES: tuple[ExportMode, ...] = (
    "full",
    "ai",
    "docs",
    "changed",
)

MODE_TITLES: dict[ExportMode, str] = {
    "full": "Full Repository Export",
    "ai": "AI Repository Export",
    "docs": "Documentation Export",
    "changed": "Changed Files Export",
}

MODE_DEFAULT_SECTIONS: dict[ExportMode, tuple[str, ...]] = {
    "full": (
        "quick_start",
        "repository_metadata",
        "configuration",
        "summary",
        "file_summary",
        "repository_tree",
        "dependencies",
        "database_schema",
        "secret_detection",
        "symbol_index",
        "import_graph",
        "call_graph",
        "warnings",
        "source_export",
    ),
    "ai": (
        "project_summary",
        "repository_metadata",
        "summary",
        "important_files",
        "dependencies",
        "database_schema",
        "symbol_index",
        "import_graph",
        "call_graph",
        "warnings",
    ),
    "docs": (
        "documentation_quick_start",
        "repository_metadata",
        "summary",
        "documentation_files",
        "warnings",
        "document_export",
    ),
    "changed": (
        "changed_export_header",
        "repository_metadata",
        "summary",
        "changed_files_summary",
        "git_diff",
        "changed_file_contents",
        "deleted_files",
        "warnings",
    ),
}


def normalize_export_mode(mode: str) -> ExportMode:
    """Normalize and validate an export mode string."""

    normalized = str(mode).strip().lower().replace("-", "_")

    if normalized not in VALID_EXPORT_MODES:
        valid = ", ".join(VALID_EXPORT_MODES)
        raise ValueError(f"unknown export mode {mode!r}; expected one of: {valid}")

    return normalized  # type: ignore[return-value]


def is_valid_export_mode(mode: str) -> bool:
    """Return whether mode is a known export mode."""

    try:
        normalize_export_mode(mode)
    except ValueError:
        return False

    return True


def export_mode_title(mode: str) -> str:
    """Return a stable human-readable title for an export mode."""

    return MODE_TITLES[normalize_export_mode(mode)]


def export_mode_default_sections(mode: str) -> tuple[str, ...]:
    """Return default section identifiers for an export mode."""

    return MODE_DEFAULT_SECTIONS[normalize_export_mode(mode)]


def export_mode_includes_source_content(mode: str) -> bool:
    """Return whether a mode normally includes source/document content."""

    return normalize_export_mode(mode) in {"full", "docs", "changed"}


def export_mode_is_review_focused(mode: str) -> bool:
    """Return whether a mode is primarily intended for change review."""

    return normalize_export_mode(mode) == "changed"


def repository_export_title(export: RepositoryExport) -> str:
    """Return the title for a RepositoryExport's mode."""

    return export_mode_title(export.mode)


def repository_export_default_sections(export: RepositoryExport) -> tuple[str, ...]:
    """Return default section identifiers for a RepositoryExport."""

    return export_mode_default_sections(export.mode)
