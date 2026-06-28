"""Documentation export helpers for RepoContext.

This module contains the documentation-file detection and export-context
foundation for Milestone 9. Rendering, writing, and CLI integration are added
in later steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from repocontext.models import FileInfo

from .full import FullExportContext, build_full_export_context


DOCS_EXPORT_FILENAME = "docs.txt"

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


__all__ = [
    "DOCS_EXPORT_FILENAME",
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
    "is_documentation_file",
]
