"""AI-focused export generation for RepoContext.

The AI export is intentionally compact. It provides stable, high-level
sections for language models without embedding complete source dumps.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repocontext.gitignore import ensure_repocontext_gitignore_entries

from .full import FullExportContext, build_full_export_context


AI_EXPORT_FILENAME = "ai.txt"
AI_EXPORT_DOCUMENT_HEADING = "# AI CONTEXT"

AI_EXPORT_SECTION_ORDER: tuple[str, ...] = (
    "project",
    "architecture_summary",
    "important_files",
    "symbol_index",
    "import_graph",
    "call_graph",
    "notes",
)

AI_EXPORT_SECTION_HEADINGS: dict[str, str] = {
    "project": "## Project",
    "architecture_summary": "## Architecture Summary",
    "important_files": "## Important Files",
    "symbol_index": "## Symbol Index",
    "import_graph": "## Import Graph",
    "call_graph": "## Call Graph",
    "notes": "## Notes",
}


@dataclass(frozen=True)
class AIExportContext:
    """Data required to render the compact AI export."""

    full_context: FullExportContext

    @property
    def repository_root(self) -> Path:
        """Return the repository root path."""

        return self.full_context.repository_root


def iter_ai_export_headings() -> tuple[str, ...]:
    """Return AI export headings in stable render order."""

    return (
        AI_EXPORT_DOCUMENT_HEADING,
        *(
            AI_EXPORT_SECTION_HEADINGS[section_name]
            for section_name in AI_EXPORT_SECTION_ORDER
        ),
    )


def create_ai_export_context(full_context: FullExportContext) -> AIExportContext:
    """Create an AI export context from an existing Full Export context."""

    return AIExportContext(full_context=full_context)


def build_ai_export_context(repository_root: Path | str) -> AIExportContext:
    """Build the AI export context for a Git repository."""

    return create_ai_export_context(build_full_export_context(repository_root))


def render_ai_export(context: AIExportContext) -> str:
    """Render the compact AI export text."""

    sections = [
        AI_EXPORT_DOCUMENT_HEADING,
        _render_project_section(context),
        _render_architecture_summary_section(),
        _render_important_files_section(),
        _render_symbol_index_section(),
        _render_import_graph_section(),
        _render_call_graph_section(),
        _render_notes_section(),
    ]

    return "\n\n".join(section.rstrip() for section in sections).rstrip() + "\n"


def write_ai_export(
    context: AIExportContext,
    output_path: Path | str | None = None,
) -> Path:
    """Write the rendered AI export atomically and return its path."""

    resolved_output_path = _resolve_ai_export_output_path(context, output_path)
    temporary_output_path = _temporary_ai_export_output_path(resolved_output_path)
    rendered_export = render_ai_export(context)

    try:
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_output_path.write_text(rendered_export, encoding="utf-8")
        temporary_output_path.replace(resolved_output_path)
    except OSError:
        _remove_temporary_output_file(temporary_output_path)
        raise

    return resolved_output_path


def generate_ai_export(repository_root: Path | str) -> Path:
    """Build, render, and write ai.txt for a repository."""

    resolved_repository_root = Path(repository_root).resolve()
    ensure_repocontext_gitignore_entries(resolved_repository_root)
    context = build_ai_export_context(resolved_repository_root)
    return write_ai_export(context)


def _resolve_ai_export_output_path(
    context: AIExportContext,
    output_path: Path | str | None,
) -> Path:
    """Resolve the final AI export output path."""

    if output_path is not None:
        return Path(output_path).resolve()

    return context.repository_root / AI_EXPORT_FILENAME


def _temporary_ai_export_output_path(output_path: Path) -> Path:
    """Return the temporary path used for atomic AI export writes."""

    return output_path.with_name(f".{output_path.name}.tmp")


def _remove_temporary_output_file(temporary_output_path: Path) -> None:
    """Best-effort cleanup for a failed temporary export write."""

    try:
        temporary_output_path.unlink(missing_ok=True)
    except OSError:
        pass


def _render_project_section(context: AIExportContext) -> str:
    """Render compact repository facts for the AI export."""

    full_context = context.full_context
    repository_info = full_context.repository_info
    repository_name = repository_info.name or "unknown"

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["project"],
            "",
            f"Repository: {repository_name}",
            f"Tracked files: {full_context.tracked_file_count}",
            f"Scanned files: {len(full_context.scanned_files)}",
            f"Exported text files: {len(full_context.exported_text_files)}",
            f"Skipped binary files: {len(full_context.skipped_binary_files)}",
            f"Errored files: {len(full_context.errored_files)}",
            f"Total lines: {full_context.total_line_count}",
            f"Estimated tokens: {full_context.total_estimated_tokens}",
        ]
    )


def _render_architecture_summary_section() -> str:
    """Render the placeholder Architecture Summary section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["architecture_summary"],
            "",
            "Architecture summary generation is not implemented yet.",
        ]
    )


def _render_important_files_section() -> str:
    """Render the placeholder Important Files section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["important_files"],
            "",
            "Important file ranking is not implemented yet.",
        ]
    )


def _render_symbol_index_section() -> str:
    """Render the placeholder Symbol Index section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["symbol_index"],
            "",
            "Symbol index rendering is not implemented yet.",
        ]
    )


def _render_import_graph_section() -> str:
    """Render the placeholder Import Graph section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["import_graph"],
            "",
            "Import graph rendering is not implemented yet.",
        ]
    )


def _render_call_graph_section() -> str:
    """Render the placeholder Call Graph section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["call_graph"],
            "",
            "Call graph rendering is not implemented yet.",
        ]
    )


def _render_notes_section() -> str:
    """Render compact AI export notes."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["notes"],
            "",
            "- This export intentionally excludes complete source dumps.",
            "- Detailed section content will be expanded in later Milestone 8 steps.",
        ]
    )


__all__ = [
    "AI_EXPORT_DOCUMENT_HEADING",
    "AI_EXPORT_FILENAME",
    "AI_EXPORT_SECTION_HEADINGS",
    "AI_EXPORT_SECTION_ORDER",
    "AIExportContext",
    "build_ai_export_context",
    "create_ai_export_context",
    "generate_ai_export",
    "iter_ai_export_headings",
    "render_ai_export",
    "write_ai_export",
]
