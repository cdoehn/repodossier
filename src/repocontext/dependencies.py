"""Dependency detection data model and analyzer scaffold.

This module contains the stable in-memory representation for dependency
analysis. Actual pyproject.toml and requirements.txt parsing is added in later
Milestone 10 patches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Iterable, Mapping


VALID_DEPENDENCY_TYPES: tuple[str, ...] = (
    "runtime",
    "development",
    "optional",
    "unknown",
)

_DEPENDENCY_TYPE_ORDER: Mapping[str, int] = {
    dependency_type: index
    for index, dependency_type in enumerate(VALID_DEPENDENCY_TYPES)
}


def normalize_dependency_name(name: str) -> str:
    """Return a canonical package name for comparison and stable sorting.

    This follows the common Python package-name normalization shape:
    lowercase, collapse separator runs, and treat underscores/dots like dashes.

    Extras are intentionally ignored for the normalized base name, so
    ``requests[security]`` normalizes to ``requests``.
    """

    base_name = name.strip()

    if "[" in base_name:
        base_name = base_name.split("[", 1)[0]

    normalized = re.sub(r"[-_.]+", "-", base_name)
    normalized = normalized.lower().strip("-")

    return normalized


@dataclass(frozen=True)
class Dependency:
    """A single detected dependency entry.

    ``raw_value`` keeps the original declaration for debugging and export
    fidelity. ``normalized_name`` is used for grouping and deterministic
    ordering.
    """

    name: str
    normalized_name: str = ""
    version_constraint: str = ""
    dependency_type: str = "unknown"
    source_file: str = ""
    source_section: str = ""
    raw_value: str = ""
    group: str = ""

    def __post_init__(self) -> None:
        cleaned_name = self.name.strip()
        if not cleaned_name:
            raise ValueError("Dependency name must not be empty.")

        cleaned_type = self.dependency_type.strip().lower()
        if cleaned_type not in VALID_DEPENDENCY_TYPES:
            allowed = ", ".join(VALID_DEPENDENCY_TYPES)
            raise ValueError(
                f"Unsupported dependency type {self.dependency_type!r}; "
                f"expected one of: {allowed}."
            )

        normalized_name = (
            self.normalized_name.strip()
            if self.normalized_name.strip()
            else normalize_dependency_name(cleaned_name)
        )

        if not normalized_name:
            raise ValueError("Dependency normalized_name must not be empty.")

        object.__setattr__(self, "name", cleaned_name)
        object.__setattr__(self, "normalized_name", normalized_name)
        object.__setattr__(self, "dependency_type", cleaned_type)

        if not self.raw_value:
            object.__setattr__(self, "raw_value", cleaned_name)

    def sort_key(self) -> tuple[int, str, str, str]:
        """Return the deterministic DependencyReport ordering key."""

        return (
            _DEPENDENCY_TYPE_ORDER[self.dependency_type],
            self.normalized_name,
            self.source_file,
            self.raw_value,
        )


@dataclass(frozen=True)
class DependencyReport:
    """Collected dependency analysis result for one repository."""

    dependencies: tuple[Dependency, ...] = field(default_factory=tuple)
    dependency_files: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    unsupported_lines: tuple[str, ...] = field(default_factory=tuple)
    unsupported_sections: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dependencies",
            tuple(sorted(tuple(self.dependencies), key=lambda item: item.sort_key())),
        )
        object.__setattr__(
            self,
            "dependency_files",
            _unique_sorted_strings(self.dependency_files),
        )
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        object.__setattr__(
            self,
            "unsupported_lines",
            tuple(str(item) for item in self.unsupported_lines),
        )
        object.__setattr__(
            self,
            "unsupported_sections",
            tuple(str(item) for item in self.unsupported_sections),
        )

    def dependencies_by_type(self, dependency_type: str) -> tuple[Dependency, ...]:
        """Return dependencies of one dependency type in stable order."""

        cleaned_type = dependency_type.strip().lower()
        if cleaned_type not in VALID_DEPENDENCY_TYPES:
            allowed = ", ".join(VALID_DEPENDENCY_TYPES)
            raise ValueError(
                f"Unsupported dependency type {dependency_type!r}; "
                f"expected one of: {allowed}."
            )

        return tuple(
            dependency
            for dependency in self.dependencies
            if dependency.dependency_type == cleaned_type
        )

    def counts_by_type(self) -> dict[str, int]:
        """Return dependency counts for all known dependency types."""

        counts = {dependency_type: 0 for dependency_type in VALID_DEPENDENCY_TYPES}
        for dependency in self.dependencies:
            counts[dependency.dependency_type] += 1
        return counts

    def is_empty(self) -> bool:
        """Return True when no dependencies and no dependency files were found."""

        return not self.dependencies and not self.dependency_files


def analyze_dependencies(
    repo_root: str | Path,
    files: Iterable[str | Path] | None = None,
) -> DependencyReport:
    """Analyze repository dependencies.

    This is the Milestone 10.1 scaffold. Later patches add concrete
    pyproject.toml and requirements.txt parsing while keeping this public
    function stable for exporters.
    """

    _ = Path(repo_root)
    _ = tuple(files or ())

    return DependencyReport()


def _unique_sorted_strings(values: Iterable[str]) -> tuple[str, ...]:
    unique_values = {
        str(value).strip()
        for value in values
        if str(value).strip()
    }
    return tuple(sorted(unique_values))
