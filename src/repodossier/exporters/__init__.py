"""Export generation helpers for RepoDossier."""

from .ai import (
    AI_EXPORT_DOCUMENT_HEADING,
    AI_EXPORT_FILENAME,
    AI_EXPORT_SECTION_HEADINGS,
    AI_EXPORT_SECTION_ORDER,
    AIExportContext,
    build_ai_export_context,
    create_ai_export_context,
    generate_ai_export,
    iter_ai_export_headings,
    render_ai_export,
    write_ai_export,
)
from .docs import (
    DOCS_EXPORT_DOCUMENT_HEADING,
    DOCS_EXPORT_FILENAME,
    DOCS_EXPORT_SECTION_HEADINGS,
    DOCS_EXPORT_SECTION_ORDER,
    DocumentationExportContext,
    DocumentationFile,
    build_docs_export_context,
    create_docs_export_context,
    generate_docs_export,
    iter_docs_export_headings,
    render_docs_export,
    write_docs_export,
)
from .full import (
    FULL_EXPORT_SECTION_HEADINGS,
    FULL_EXPORT_SECTION_ORDER,
    FullExportContext,
    build_full_export_context,
    create_full_export_context,
    generate_full_export,
    iter_full_export_headings,
    render_full_export,
    write_full_export,
)

__all__ = [
    "DOCS_EXPORT_DOCUMENT_HEADING",
    "DOCS_EXPORT_FILENAME",
    "DOCS_EXPORT_SECTION_HEADINGS",
    "DOCS_EXPORT_SECTION_ORDER",
    "DocumentationExportContext",
    "DocumentationFile",
    "build_docs_export_context",
    "create_docs_export_context",
    "generate_docs_export",
    "iter_docs_export_headings",
    "render_docs_export",
    "write_docs_export",
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
    "FULL_EXPORT_SECTION_HEADINGS",
    "FULL_EXPORT_SECTION_ORDER",
    "FullExportContext",
    "build_full_export_context",
    "create_full_export_context",
    "generate_full_export",
    "iter_full_export_headings",
    "render_full_export",
    "write_full_export",
]

from repodossier.exporters.model_markdown import (
    render_markdown_export_from_model,
    write_markdown_export_from_model,
    write_markdown_export_model_to_stream,
)

from repodossier.exporters.model_adapter import (
    build_repository_export_from_entries,
    build_file_tree_from_entries,
    export_warning_from_mapping,
    export_warning_from_object,
    export_warnings_from_objects,
    file_entries_from_objects,
    file_entry_from_mapping,
    file_entry_from_object,
)

