"""Foundational structures and orchestration for the Full Export MVP."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from repocontext.git import RepositoryInfo, get_repository_info
from repocontext.models import FileInfo
from repocontext.scanner import RepositoryScanner

FULL_EXPORT_SECTION_ORDER: tuple[str, ...] = (
    "ai_quick_start",
    "repository_statistics",
    "file_summary",
    "repository_tree",
    "complete_source_export",
    "warnings",
)

FULL_EXPORT_SECTION_HEADINGS: dict[str, str] = {
    "ai_quick_start": "# AI Quick Start",
    "repository_statistics": "# Repository Statistics",
    "file_summary": "# File Summary",
    "repository_tree": "# Repository Tree",
    "complete_source_export": "# Complete Source Export",
    "warnings": "# Warnings",
}


def iter_full_export_headings() -> tuple[str, ...]:
    """Return Full Export section headings in stable render order."""
    return tuple(
        FULL_EXPORT_SECTION_HEADINGS[section_name]
        for section_name in FULL_EXPORT_SECTION_ORDER
    )


@dataclass(frozen=True)
class FullExportContext:
    """Data required to build the Full Export output.

    The context deliberately separates repository discovery and file scanning
    from rendering and writing steps.
    """

    repository_info: RepositoryInfo
    scanned_files: Sequence[FileInfo]
    warnings: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Normalize sequence inputs to immutable tuples."""
        object.__setattr__(self, "scanned_files", tuple(self.scanned_files))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    @property
    def repository_root(self) -> Path:
        """Return the repository root path."""
        return self.repository_info.root_path

    @property
    def tracked_file_count(self) -> int:
        """Return the number of Git-tracked files known from repository discovery."""
        return len(self.repository_info.tracked_files)

    @property
    def sorted_files(self) -> tuple[FileInfo, ...]:
        """Return scanned files sorted by repository-relative path."""
        return tuple(
            sorted(
                self.scanned_files,
                key=lambda file_info: file_info.relative_path.as_posix(),
            )
        )

    @property
    def exported_text_files(self) -> tuple[FileInfo, ...]:
        """Return text files that are suitable for the complete source export."""
        return tuple(
            file_info
            for file_info in self.sorted_files
            if file_info.is_text is True
            and file_info.is_binary is False
            and file_info.error is None
            and file_info.content is not None
        )

    @property
    def skipped_binary_files(self) -> tuple[FileInfo, ...]:
        """Return files detected as binary and skipped for source dumping."""
        return tuple(
            file_info
            for file_info in self.sorted_files
            if file_info.is_binary is True
        )

    @property
    def errored_files(self) -> tuple[FileInfo, ...]:
        """Return scanned files that contain an access or decoding error."""
        return tuple(
            file_info
            for file_info in self.sorted_files
            if file_info.error is not None
        )

    @property
    def total_line_count(self) -> int:
        """Return the total line count across exported text files."""
        return sum(file_info.line_count or 0 for file_info in self.exported_text_files)

    @property
    def total_estimated_tokens(self) -> int:
        """Return the total estimated token count across exported text files."""
        return sum(
            file_info.estimated_tokens or 0
            for file_info in self.exported_text_files
        )

    @property
    def file_type_counts(self) -> tuple[tuple[str, int], ...]:
        """Return repository file type counts based on scanned file extensions."""
        counter: Counter[str] = Counter()
        for file_info in self.sorted_files:
            suffix = file_info.relative_path.suffix.lower()
            file_type = suffix if suffix else "[no extension]"
            counter[file_type] += 1
        return tuple(sorted(counter.items()))


def create_full_export_context(
    repository_info: RepositoryInfo,
    scanned_files: Sequence[FileInfo],
    warnings: Sequence[str] = (),
) -> FullExportContext:
    """Create a Full Export context from repository and scanner results."""
    return FullExportContext(
        repository_info=repository_info,
        scanned_files=scanned_files,
        warnings=warnings,
    )


def build_full_export_context(repository_root: Path | str) -> FullExportContext:
    """Build the Full Export context for a Git repository."""
    resolved_repository_root = Path(repository_root).resolve()
    repository_info = get_repository_info(resolved_repository_root)
    scanned_files = RepositoryScanner().scan(resolved_repository_root)

    return create_full_export_context(
        repository_info=repository_info,
        scanned_files=scanned_files,
    )


def render_full_export(context: FullExportContext) -> str:
    """Render a minimal Full Export skeleton.

    Later Milestone 3 steps expand each section with its final content.
    This function already keeps the section order stable and makes the
    default CLI command able to produce full.txt.
    """
    sections = [
        _render_ai_quick_start_placeholder(context),
        _render_repository_statistics(context),
        _render_file_summary_placeholder(context),
        _render_repository_tree_placeholder(context),
        _render_complete_source_export_placeholder(context),
        _render_warnings_placeholder(context),
    ]
    return "\n\n".join(section.rstrip() for section in sections).rstrip() + "\n"


def write_full_export(
    context: FullExportContext,
    output_path: Path | str | None = None,
) -> Path:
    """Write the rendered Full Export to full.txt and return its path."""
    resolved_output_path = (
        Path(output_path).resolve()
        if output_path is not None
        else context.repository_root / "full.txt"
    )
    rendered_export = render_full_export(context)
    resolved_output_path.write_text(rendered_export, encoding="utf-8")
    return resolved_output_path


def generate_full_export(repository_root: Path | str) -> Path:
    """Build, render, and write the Full Export for a repository."""
    context = build_full_export_context(repository_root)
    return write_full_export(context)


def _render_ai_quick_start_placeholder(context: FullExportContext) -> str:
    return "\n".join(
        [
            FULL_EXPORT_SECTION_HEADINGS["ai_quick_start"],
            "",
            f"Repository: {context.repository_info.name or 'unknown'}",
            "AI Quick Start details will be expanded in Milestone 3.4.",
        ]
    )


def _render_repository_statistics(context: FullExportContext) -> str:
    """Render repository-wide statistics for the Full Export."""
    lines = [
        FULL_EXPORT_SECTION_HEADINGS["repository_statistics"],
        "",
        f"Total tracked files: {context.tracked_file_count}",
        f"Scanned files: {len(context.scanned_files)}",
        f"Exported text files: {len(context.exported_text_files)}",
        f"Skipped binary files: {len(context.skipped_binary_files)}",
        f"Errored files: {len(context.errored_files)}",
        f"Total lines: {context.total_line_count}",
        f"Estimated tokens: {context.total_estimated_tokens}",
        "",
        "File types:",
    ]

    if context.file_type_counts:
        lines.extend(
            f"- {file_type}: {count}"
            for file_type, count in context.file_type_counts
        )
    else:
        lines.append("- none: 0")

    return "\n".join(lines)


def _render_file_summary_placeholder(context: FullExportContext) -> str:
    return "\n".join(
        [
            FULL_EXPORT_SECTION_HEADINGS["file_summary"],
            "",
            f"Files ready for export: {len(context.exported_text_files)}",
            "File Summary details will be expanded in Milestone 3.5.",
        ]
    )


def _render_repository_tree_placeholder(context: FullExportContext) -> str:
    return "\n".join(
        [
            FULL_EXPORT_SECTION_HEADINGS["repository_tree"],
            "",
            "Repository Tree rendering will be expanded in Milestone 3.6.",
        ]
    )


def _render_complete_source_export_placeholder(context: FullExportContext) -> str:
    return "\n".join(
        [
            FULL_EXPORT_SECTION_HEADINGS["complete_source_export"],
            "",
            f"Source files ready for dumping: {len(context.exported_text_files)}",
            "Complete Source Export rendering will be expanded in Milestone 3.7.",
        ]
    )


def _render_warnings_placeholder(context: FullExportContext) -> str:
    lines = [
        FULL_EXPORT_SECTION_HEADINGS["warnings"],
        "",
    ]

    if context.warnings:
        lines.extend(f"- {warning}" for warning in context.warnings)
    else:
        lines.append("Warning rendering will be expanded in Milestone 3.8.")

    return "\n".join(lines)
