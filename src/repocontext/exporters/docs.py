"""Documentation export helpers for RepoContext.

This module starts Milestone 9 with deterministic documentation-file
classification. Rendering, writing, and CLI integration are added in later
steps.
"""

from __future__ import annotations

from pathlib import Path


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

    parts = _lower_path_parts(normalized_path)
    filename = parts[-1]
    stem = path_obj.stem.lower()

    if "docs" in parts[:-1]:
        return True

    if parts[0] == "planning" and suffix in {".md", ".txt"}:
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
    "PRIMARY_DOCUMENTATION_CATEGORY",
    "ARCHITECTURE_DOCUMENTATION_CATEGORY",
    "SPECIFICATION_DOCUMENTATION_CATEGORY",
    "TASKS_AND_ROADMAP_CATEGORY",
    "CHANGELOG_AND_CONTRIBUTION_CATEGORY",
    "LICENSE_CATEGORY",
    "OTHER_DOCS_CATEGORY",
    "categorize_documentation_file",
    "is_documentation_file",
]
