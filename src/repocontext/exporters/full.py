"""Foundational structures for the Full Export MVP.

This module intentionally contains only the section structure and context model
for Milestone 3.1. Rendering full.txt and wiring the default CLI command are
implemented in later Milestone 3 steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from repocontext.git import RepositoryInfo
from repocontext.models import FileInfo

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
    from later rendering and writing steps.
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
