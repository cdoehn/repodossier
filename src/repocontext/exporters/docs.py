"""Documentation export helpers for RepoContext.

This module contains the documentation-file detection, export-context model,
and renderer for Milestone 9. Writing and CLI integration are added in later
steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from repocontext.gitignore import ensure_repocontext_gitignore_entries
from repocontext.models import FileInfo

from .full import FullExportContext, build_full_export_context


DOCS_EXPORT_FILENAME = "docs.txt"
DOCS_EXPORT_DOCUMENT_HEADING = "# Documentation Context"

DOCS_EXPORT_SECTION_ORDER: tuple[str, ...] = (
    "documentation_quick_start",
    "documentation_summary",
    "documentation_files",
    "extracted_documents",
    "warnings",
)

DOCS_EXPORT_SECTION_HEADINGS: dict[str, str] = {
    "documentation_quick_start": "## Documentation Quick Start",
    "documentation_summary": "## Documentation Summary",
    "documentation_files": "## Documentation Files",
    "extracted_documents": "## Extracted Documents",
    "warnings": "## Warnings",
}

GENERATED_EXPORT_FILENAMES: frozenset[str] = frozenset(
    {
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
    }
)

DOCUMENTATION_CATEGORY_ORDER: tuple[str, ...] = (
    "Primary documentation",
    "Architecture documentation",
    "Specification documentation",
    "Tasks and roadmap",
    "Changelog and contribution docs",
    "License",
    "Other docs",
)

PRIMARY_DOCUMENTATION_CATEGORY = "Primary documentation"
ARCHITECTURE_DOCUMENTATION_CATEGORY = "Architecture documentation"
SPECIFICATION_DOCUMENTATION_CATEGORY = "Specification documentation"
TASKS_AND_ROADMAP_CATEGORY = "Tasks and roadmap"
CHANGELOG_AND_CONTRIBUTION_CATEGORY = "Changelog and contribution docs"
LICENSE_CATEGORY = "License"
OTHER_DOCS_CATEGORY = "Other docs"

_DOCUMENTATION_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {
        "",
        ".md",
        ".markdown",
        ".rst",
        ".txt",
    }
)

_CHANGELOG_AND_CONTRIBUTION_STEMS: frozenset[str] = frozenset(
    {
        "changelog",
        "changes",
        "contributing",
        "contribution",
        "contributors",
    }
)


@dataclass(frozen=True)
class DocumentationFile:
    """One exportable documentation file with its stable category."""

    file_info: FileInfo
    category: str

    @property
    def relative_path(self) -> Path:
        """Return the repository-relative documentation path."""

        return self.file_info.relative_path

    @property
    def line_count(self) -> int:
        """Return the documentation line count with a safe fallback."""

        return self.file_info.line_count or 0

    @property
    def estimated_tokens(self) -> int:
        """Return the estimated documentation token count with a safe fallback."""

        return self.file_info.estimated_tokens or 0

    @property
    def content(self) -> str:
        """Return the documentation content with a safe fallback."""

        return self.file_info.content or ""

    def sort_key(self) -> tuple[int, str]:
        """Return a deterministic category-aware sort key."""

        return (
            _documentation_category_index(self.category),
            self.relative_path.as_posix(),
        )


@dataclass(frozen=True)
class DocumentationExportContext:
    """Data required to render and write the documentation export."""

    full_context: FullExportContext
    documentation_files: Sequence[DocumentationFile]
    skipped_files: Sequence[FileInfo] = field(default_factory=tuple)
    warnings: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Normalize sequence inputs to immutable tuples in deterministic order."""

        object.__setattr__(
            self,
            "documentation_files",
            tuple(sorted(self.documentation_files, key=lambda item: item.sort_key())),
        )
        object.__setattr__(
            self,
            "skipped_files",
            tuple(
                sorted(
                    self.skipped_files,
                    key=lambda file_info: file_info.relative_path.as_posix(),
                )
            ),
        )
        object.__setattr__(self, "warnings", tuple(sorted(self.warnings)))

    @property
    def repository_root(self) -> Path:
        """Return the repository root path."""

        return self.full_context.repository_root

    @property
    def repository_info(self):
        """Return the repository metadata from the reused full context."""

        return self.full_context.repository_info

    @property
    def scanned_files(self) -> tuple[FileInfo, ...]:
        """Return all scanned files from the reused full context."""

        return tuple(self.full_context.scanned_files)

    @property
    def total_line_count(self) -> int:
        """Return total lines across exportable documentation files."""

        return sum(document.line_count for document in self.documentation_files)

    @property
    def estimated_token_count(self) -> int:
        """Return estimated tokens across exportable documentation files."""

        return sum(document.estimated_tokens for document in self.documentation_files)


def iter_docs_export_headings() -> tuple[str, ...]:
    """Return docs export headings in stable render order."""

    return (
        DOCS_EXPORT_DOCUMENT_HEADING,
        *(
            DOCS_EXPORT_SECTION_HEADINGS[section_name]
            for section_name in DOCS_EXPORT_SECTION_ORDER
        ),
    )


def build_docs_export_context(repository_root: Path | str) -> DocumentationExportContext:
    """Build the documentation export context for a Git repository."""

    return create_docs_export_context(build_full_export_context(repository_root))


def create_docs_export_context(
    full_context: FullExportContext,
) -> DocumentationExportContext:
    """Create a docs export context by filtering a FullExportContext."""

    documentation_files: list[DocumentationFile] = []
    skipped_files: list[FileInfo] = []
    warnings: list[str] = []

    for file_info in full_context.sorted_files:
        category = categorize_documentation_file(file_info.relative_path)
        if category is None:
            if _is_possible_documentation_path(file_info.relative_path):
                skipped_files.append(file_info)
                warnings.append(_skipped_documentation_warning(file_info))
            continue

        if _is_exportable_documentation_file(file_info):
            documentation_files.append(
                DocumentationFile(
                    file_info=file_info,
                    category=category,
                )
            )
        else:
            skipped_files.append(file_info)
            warnings.append(_skipped_documentation_warning(file_info))

    if not documentation_files:
        warnings.append("No documentation files found.")

    return DocumentationExportContext(
        full_context=full_context,
        documentation_files=documentation_files,
        skipped_files=skipped_files,
        warnings=warnings,
    )


def render_docs_export(context: DocumentationExportContext) -> str:
    """Render the complete documentation export text."""

    sections = [
        DOCS_EXPORT_DOCUMENT_HEADING,
        _render_documentation_quick_start_section(context),
        _render_documentation_summary_section(context),
        _render_documentation_files_section(context),
        _render_extracted_documents_section(context),
        _render_warnings_section(context),
    ]

    return "\n\n".join(section.rstrip() for section in sections).rstrip() + "\n"


def write_docs_export(
    context: DocumentationExportContext,
    output_path: Path | str | None = None,
) -> Path:
    """Write the rendered documentation export atomically and return its path."""

    resolved_output_path = _resolve_docs_export_output_path(context, output_path)
    temporary_output_path = _temporary_docs_export_output_path(resolved_output_path)
    rendered_export = render_docs_export(context)

    try:
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_output_path.write_text(rendered_export, encoding="utf-8")
        temporary_output_path.replace(resolved_output_path)
    except OSError:
        _remove_temporary_output_file(temporary_output_path)
        raise

    return resolved_output_path


def generate_docs_export(repository_root: Path | str) -> Path:
    """Build, render, and write docs.txt for a repository."""

    resolved_repository_root = Path(repository_root).resolve()
    ensure_repocontext_gitignore_entries(resolved_repository_root)
    context = build_docs_export_context(resolved_repository_root)
    return write_docs_export(context)


def is_documentation_file(path: str | Path, *, is_binary: bool = False) -> bool:
    """Return True when a repository-relative path is documentation-like."""

    if is_binary:
        return False

    normalized_path = _normalize_path(path)
    if not normalized_path:
        return False

    if _is_generated_export_path(normalized_path):
        return False

    path_obj = Path(normalized_path)
    suffix = path_obj.suffix.lower()
    if suffix not in _DOCUMENTATION_TEXT_SUFFIXES:
        return False

    return _is_possible_documentation_path(normalized_path)


def categorize_documentation_file(path: str | Path) -> str | None:
    """Return the stable documentation category for a path, or None."""

    if not is_documentation_file(path):
        return None

    normalized_path = _normalize_path(path)
    path_obj = Path(normalized_path)
    parts = _lower_path_parts(normalized_path)
    filename = parts[-1]
    stem = path_obj.stem.lower()

    if stem.startswith("readme"):
        return PRIMARY_DOCUMENTATION_CATEGORY

    if _contains_word(stem, "architecture"):
        return ARCHITECTURE_DOCUMENTATION_CATEGORY

    if _contains_word(stem, "spec"):
        return SPECIFICATION_DOCUMENTATION_CATEGORY

    if (
        _contains_word(stem, "tasks")
        or _contains_word(stem, "roadmap")
        or _contains_word(stem, "milestone")
        or parts[0] == "planning"
    ):
        return TASKS_AND_ROADMAP_CATEGORY

    if stem in _CHANGELOG_AND_CONTRIBUTION_STEMS:
        return CHANGELOG_AND_CONTRIBUTION_CATEGORY

    if filename == "license" or stem.startswith("license"):
        return LICENSE_CATEGORY

    return OTHER_DOCS_CATEGORY


def _resolve_docs_export_output_path(
    context: DocumentationExportContext,
    output_path: Path | str | None,
) -> Path:
    """Resolve the final docs export output path."""

    if output_path is not None:
        return Path(output_path).resolve()

    return context.repository_root / DOCS_EXPORT_FILENAME


def _temporary_docs_export_output_path(output_path: Path) -> Path:
    """Return the temporary path used for atomic docs export writes."""

    return output_path.with_name(f".{output_path.name}.tmp")


def _remove_temporary_output_file(path: Path) -> None:
    """Remove a temporary output file if it exists."""

    try:
        path.unlink()
    except FileNotFoundError:
        return


def _render_documentation_quick_start_section(
    context: DocumentationExportContext,
) -> str:
    """Render a compact AI-oriented docs export introduction."""

    repository_name = context.repository_info.name or context.repository_root.name
    category_counts = _documentation_category_counts(context.documentation_files)

    lines = [
        DOCS_EXPORT_SECTION_HEADINGS["documentation_quick_start"],
        "",
        f"Repository: {repository_name}",
        f"Documentation files: {len(context.documentation_files)}",
        f"Total documentation lines: {_format_number(context.total_line_count)}",
        f"Estimated documentation tokens: {_format_number(context.estimated_token_count)}",
        "Purpose: Documentation-only export for AI review.",
        "",
        "Document types:",
    ]

    if category_counts:
        for category in DOCUMENTATION_CATEGORY_ORDER:
            count = category_counts.get(category, 0)
            if count:
                lines.append(f"- {category}: {count}")
    else:
        lines.append("- none")

    return "\n".join(lines)


def _render_documentation_summary_section(
    context: DocumentationExportContext,
) -> str:
    """Render documentation files grouped by stable category."""

    lines = [
        DOCS_EXPORT_SECTION_HEADINGS["documentation_summary"],
        "",
    ]

    if not context.documentation_files:
        lines.append("No documentation files found.")
        return "\n".join(lines)

    first_category = True
    for category in DOCUMENTATION_CATEGORY_ORDER:
        documents = [
            document
            for document in context.documentation_files
            if document.category == category
        ]
        if not documents:
            continue

        if not first_category:
            lines.append("")
        first_category = False

        lines.append(f"{category}:")
        for document in documents:
            lines.append(
                "- "
                f"{document.relative_path.as_posix()} "
                f"— {document.line_count} lines, "
                f"~{_format_number(document.estimated_tokens)} tokens"
            )

    return "\n".join(lines)


def _render_documentation_files_section(
    context: DocumentationExportContext,
) -> str:
    """Render a machine-readable manifest table for exported docs."""

    lines = [
        DOCS_EXPORT_SECTION_HEADINGS["documentation_files"],
        "",
    ]

    if not context.documentation_files:
        lines.append("No documentation files exported.")
        return "\n".join(lines)

    lines.extend(
        [
            "| Path | Category | Lines | Tokens |",
            "| --- | --- | ---: | ---: |",
        ]
    )

    for document in context.documentation_files:
        lines.append(
            "| "
            f"{_escape_markdown_table_cell(document.relative_path.as_posix())} | "
            f"{_escape_markdown_table_cell(document.category)} | "
            f"{document.line_count} | "
            f"{document.estimated_tokens} |"
        )

    return "\n".join(lines)


def _render_extracted_documents_section(
    context: DocumentationExportContext,
) -> str:
    """Render the full content of every exportable documentation file."""

    lines = [
        DOCS_EXPORT_SECTION_HEADINGS["extracted_documents"],
        "",
    ]

    if not context.documentation_files:
        lines.append("No documentation files available for extraction.")
        return "\n".join(lines)

    first_document = True
    for document in context.documentation_files:
        if not first_document:
            lines.append("")
        first_document = False

        fence = _choose_code_fence(document.content)
        language = _code_fence_language(document.relative_path)

        lines.extend(
            [
                f"### File: {document.relative_path.as_posix()}",
                "",
                f"{fence}{language}",
                document.content.rstrip("\n"),
                fence,
            ]
        )

    return "\n".join(lines)


def _render_warnings_section(context: DocumentationExportContext) -> str:
    """Render deterministic docs export warnings."""

    lines = [
        DOCS_EXPORT_SECTION_HEADINGS["warnings"],
        "",
    ]

    if not context.warnings:
        lines.append("No warnings.")
        return "\n".join(lines)

    for warning in context.warnings:
        lines.append(f"- {warning}")

    return "\n".join(lines)


def _documentation_category_counts(
    documentation_files: Sequence[DocumentationFile],
) -> dict[str, int]:
    """Return stable counts by documentation category."""

    counts: dict[str, int] = {}
    for document in documentation_files:
        counts[document.category] = counts.get(document.category, 0) + 1
    return counts


def _is_exportable_documentation_file(file_info: FileInfo) -> bool:
    """Return True when a scanned file is safe to include in docs.txt."""

    return (
        file_info.is_text is True
        and file_info.is_binary is False
        and file_info.error is None
        and file_info.content is not None
        and is_documentation_file(file_info.relative_path)
    )


def _is_possible_documentation_path(path: str | Path) -> bool:
    """Return True for paths that are documentation-like before scan checks."""

    normalized_path = _normalize_path(path)
    if not normalized_path:
        return False

    if _is_generated_export_path(normalized_path):
        return False

    path_obj = Path(normalized_path)
    parts = _lower_path_parts(normalized_path)
    filename = parts[-1]
    stem = path_obj.stem.lower()

    if "docs" in parts[:-1]:
        return True

    if parts[0] == "planning":
        return True

    if filename == "license" or stem.startswith("license"):
        return True

    if stem.startswith("readme"):
        return True

    if _contains_word(stem, "architecture"):
        return True

    if _contains_word(stem, "spec"):
        return True

    if _contains_word(stem, "tasks"):
        return True

    if _contains_word(stem, "roadmap"):
        return True

    if _contains_word(stem, "milestone"):
        return True

    if stem in _CHANGELOG_AND_CONTRIBUTION_STEMS:
        return True

    return False


def _skipped_documentation_warning(file_info: FileInfo) -> str:
    """Return a deterministic warning for a skipped documentation-like file."""

    path = file_info.relative_path.as_posix()

    if file_info.is_binary is True:
        return f"Skipped binary documentation file: {path}"

    if file_info.error:
        return f"Skipped unreadable documentation file: {path}: {file_info.error}"

    if file_info.content is None:
        return f"Skipped documentation file without loaded content: {path}"

    return f"Skipped non-exportable documentation file: {path}"


def _documentation_category_index(category: str) -> int:
    """Return the stable sort index for a category."""

    try:
        return DOCUMENTATION_CATEGORY_ORDER.index(category)
    except ValueError:
        return len(DOCUMENTATION_CATEGORY_ORDER)


def _normalize_path(path: str | Path) -> str:
    """Return a stable POSIX-style repository-relative path string."""

    return Path(str(path)).as_posix().strip("/")


def _lower_path_parts(path: str) -> tuple[str, ...]:
    """Return lowercase POSIX path parts."""

    return tuple(part.lower() for part in Path(path).parts)


def _is_generated_export_path(path: str) -> bool:
    """Return True for generated RepoContext export file paths."""

    return Path(path).name.lower() in GENERATED_EXPORT_FILENAMES


def _contains_word(value: str, word: str) -> bool:
    """Return True when a normalized stem contains a semantic word."""

    normalized = value.replace("-", "_").replace(".", "_")
    return any(part == word or part.startswith(f"{word}_") for part in normalized.split("_"))


def _format_number(value: int) -> str:
    """Return an English-style thousands-separated number."""

    return f"{value:,}"


def _escape_markdown_table_cell(value: str) -> str:
    """Escape a value for use in a Markdown table cell."""

    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _choose_code_fence(content: str) -> str:
    """Return a code fence that is longer than any backtick run in content."""

    fence_length = 3
    while "`" * fence_length in content:
        fence_length += 1
    return "`" * fence_length


def _code_fence_language(path: Path) -> str:
    """Return a Markdown fence language for a documentation file."""

    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".rst":
        return "rst"
    return "text"


__all__ = [
    "DOCS_EXPORT_FILENAME",
    "DOCS_EXPORT_DOCUMENT_HEADING",
    "DOCS_EXPORT_SECTION_HEADINGS",
    "DOCS_EXPORT_SECTION_ORDER",
    "GENERATED_EXPORT_FILENAMES",
    "DOCUMENTATION_CATEGORY_ORDER",
    "DocumentationExportContext",
    "DocumentationFile",
    "PRIMARY_DOCUMENTATION_CATEGORY",
    "ARCHITECTURE_DOCUMENTATION_CATEGORY",
    "SPECIFICATION_DOCUMENTATION_CATEGORY",
    "TASKS_AND_ROADMAP_CATEGORY",
    "CHANGELOG_AND_CONTRIBUTION_CATEGORY",
    "LICENSE_CATEGORY",
    "OTHER_DOCS_CATEGORY",
    "build_docs_export_context",
    "categorize_documentation_file",
    "create_docs_export_context",
    "write_docs_export",
    "generate_docs_export",
    "is_documentation_file",
    "iter_docs_export_headings",
    "render_docs_export",
]
