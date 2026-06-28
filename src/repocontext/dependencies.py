"""Dependency detection data model and analyzer.

This module contains the stable in-memory representation for dependency
analysis and the pyproject.toml / requirements.txt parsers used by Milestone 10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import re
import tomllib


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

_DEVELOPMENT_POETRY_GROUPS: frozenset[str] = frozenset(
    {"dev", "test", "tests", "docs", "doc", "lint", "quality"}
)

_REQUIREMENT_NAME_RE = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9._,-]+\])?)\s*(.*)$"
)


_REQUIREMENTS_KNOWN_FILE_NAMES: frozenset[str] = frozenset(
    {
        "requirements.txt",
        "requirements-dev.txt",
        "dev-requirements.txt",
        "requirements_test.txt",
        "requirements-test.txt",
        "requirements-docs.txt",
        "docs-requirements.txt",
        "requirements-lint.txt",
        "lint-requirements.txt",
    }
)

_REQUIREMENTS_DEVELOPMENT_MARKERS: frozenset[str] = frozenset(
    {"dev", "test", "tests", "lint", "docs", "doc"}
)

_REQUIREMENTS_VCS_PREFIXES: tuple[str, ...] = (
    "git+",
    "hg+",
    "svn+",
    "bzr+",
)


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

    Milestone 10.3 supports pyproject.toml and requirements.txt analysis.
    """

    root = Path(repo_root)

    dependencies: list[Dependency] = []
    dependency_files: list[str] = []
    warnings: list[str] = []
    unsupported_sections: list[str] = []
    unsupported_lines: list[str] = []

    for pyproject_path in _iter_pyproject_candidates(root, files):
        source_file = _relative_file_path(root, pyproject_path)
        dependency_files.append(source_file)

        parsed = _parse_pyproject_file(pyproject_path, source_file)
        dependencies.extend(parsed.dependencies)
        warnings.extend(parsed.warnings)
        unsupported_sections.extend(parsed.unsupported_sections)

    for requirements_path in _iter_requirements_candidates(root, files):
        source_file = _relative_file_path(root, requirements_path)
        dependency_files.append(source_file)

        parsed = _parse_requirements_file(requirements_path, source_file)
        dependencies.extend(parsed.dependencies)
        warnings.extend(parsed.warnings)
        unsupported_lines.extend(parsed.unsupported_lines)

    return DependencyReport(
        dependencies=tuple(dependencies),
        dependency_files=tuple(dependency_files),
        warnings=tuple(warnings),
        unsupported_lines=tuple(unsupported_lines),
        unsupported_sections=tuple(unsupported_sections),
    )


def _iter_pyproject_candidates(
    repo_root: Path,
    files: Iterable[str | Path] | None,
) -> tuple[Path, ...]:
    candidates: list[Path] = []

    if files is None:
        root_pyproject = repo_root / "pyproject.toml"
        if root_pyproject.exists():
            candidates.append(root_pyproject)
    else:
        for file_item in files:
            candidate = _coerce_file_path(file_item)
            if candidate.name != "pyproject.toml":
                continue

            absolute_candidate = candidate if candidate.is_absolute() else repo_root / candidate
            if absolute_candidate.exists():
                candidates.append(absolute_candidate)

        root_pyproject = repo_root / "pyproject.toml"
        if root_pyproject.exists():
            candidates.append(root_pyproject)

    return tuple(dict.fromkeys(path.resolve() for path in candidates))


def _iter_requirements_candidates(
    repo_root: Path,
    files: Iterable[str | Path] | None,
) -> tuple[Path, ...]:
    candidates: list[Path] = []

    if files is None:
        for child in sorted(repo_root.iterdir(), key=lambda item: item.as_posix()):
            if child.is_file() and _is_requirements_file(child.relative_to(repo_root)):
                candidates.append(child)

        requirements_dir = repo_root / "requirements"
        if requirements_dir.is_dir():
            candidates.extend(
                path
                for path in sorted(requirements_dir.glob("*.txt"), key=lambda item: item.as_posix())
                if path.is_file()
            )
    else:
        for file_item in files:
            candidate = _coerce_file_path(file_item)
            if not _is_requirements_file(candidate):
                continue

            absolute_candidate = candidate if candidate.is_absolute() else repo_root / candidate
            if absolute_candidate.exists() and absolute_candidate.is_file():
                candidates.append(absolute_candidate)

    return tuple(dict.fromkeys(path.resolve() for path in candidates))


def _is_requirements_file(path: str | Path) -> bool:
    path_obj = Path(path)
    name_lower = path_obj.name.lower()

    if name_lower in _REQUIREMENTS_KNOWN_FILE_NAMES:
        return True

    if path_obj.suffix.lower() != ".txt":
        return False

    if name_lower.startswith(("requirements-", "requirements_")):
        return True

    if name_lower.endswith(("-requirements.txt", "_requirements.txt")):
        return True

    return any(part.lower() == "requirements" for part in path_obj.parts)


def _requirements_dependency_type(path: str | Path) -> str:
    path_obj = Path(path)
    name_lower = path_obj.name.lower()

    if name_lower == "requirements.txt":
        return "runtime"

    haystack = path_obj.as_posix().lower()
    for marker in _REQUIREMENTS_DEVELOPMENT_MARKERS:
        if re.search(rf"(^|[-_./]){re.escape(marker)}($|[-_./])", haystack):
            return "development"

    return "unknown"


def _parse_requirements_file(file_path: Path, source_file: str) -> DependencyReport:
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return DependencyReport(
            warnings=(f"{source_file}: could not read requirements file: {exc}",)
        )
    except UnicodeDecodeError as exc:
        return DependencyReport(
            warnings=(f"{source_file}: could not decode requirements file as UTF-8: {exc}",)
        )

    dependency_type = _requirements_dependency_type(source_file)
    dependencies: list[Dependency] = []
    warnings: list[str] = []
    unsupported_lines: list[str] = []

    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        cleaned_line = _clean_requirement_line(raw_line)
        if not cleaned_line:
            continue

        if _is_unsupported_requirement_line(cleaned_line):
            unsupported_entry = f"{source_file}:{line_number}: {cleaned_line}"
            unsupported_lines.append(unsupported_entry)
            warnings.append(
                f"{source_file}:{line_number}: unsupported requirement line ignored: "
                f"{cleaned_line}"
            )
            continue

        dependency = _dependency_from_requirement_string(
            cleaned_line,
            dependency_type=dependency_type,
            source_file=source_file,
            source_section=source_file,
            group="",
            warnings=warnings,
        )
        if dependency is not None:
            dependencies.append(dependency)

    return DependencyReport(
        dependencies=tuple(dependencies),
        warnings=tuple(warnings),
        unsupported_lines=tuple(unsupported_lines),
    )


def _clean_requirement_line(raw_line: str) -> str:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return ""

    return re.split(r"\s+#", line, maxsplit=1)[0].strip()


def _is_unsupported_requirement_line(line: str) -> bool:
    lowered = line.strip().lower()

    if not lowered:
        return False

    if lowered.startswith("-"):
        return True

    return lowered.startswith(_REQUIREMENTS_VCS_PREFIXES)


def _coerce_file_path(file_item: str | Path) -> Path:
    for attribute_name in ("relative_path", "path", "name"):
        value = getattr(file_item, attribute_name, None)
        if isinstance(value, str | Path):
            return Path(value)

    return Path(file_item)


def _relative_file_path(repo_root: Path, file_path: Path) -> str:
    try:
        return file_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return file_path.as_posix()


def _parse_pyproject_file(file_path: Path, source_file: str) -> DependencyReport:
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return DependencyReport(
            warnings=(f"{source_file}: could not read pyproject.toml: {exc}",)
        )
    except UnicodeDecodeError as exc:
        return DependencyReport(
            warnings=(f"{source_file}: could not decode pyproject.toml as UTF-8: {exc}",)
        )

    try:
        data = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as exc:
        return DependencyReport(
            warnings=(f"{source_file}: invalid pyproject.toml: {exc}",)
        )

    dependencies: list[Dependency] = []
    warnings: list[str] = []
    unsupported_sections: list[str] = []

    dependencies.extend(
        _read_pep621_dependencies(data, source_file, warnings, unsupported_sections)
    )
    dependencies.extend(
        _read_poetry_dependencies(data, source_file, warnings, unsupported_sections)
    )

    return DependencyReport(
        dependencies=tuple(dependencies),
        warnings=tuple(warnings),
        unsupported_sections=tuple(unsupported_sections),
    )


def _read_pep621_dependencies(
    data: Mapping[str, Any],
    source_file: str,
    warnings: list[str],
    unsupported_sections: list[str],
) -> tuple[Dependency, ...]:
    project = data.get("project")
    if not isinstance(project, Mapping):
        return ()

    dependencies: list[Dependency] = []

    runtime_dependencies = project.get("dependencies")
    if runtime_dependencies is not None:
        if isinstance(runtime_dependencies, list):
            for raw_dependency in runtime_dependencies:
                dependency = _dependency_from_requirement_string(
                    raw_dependency,
                    dependency_type="runtime",
                    source_file=source_file,
                    source_section="project.dependencies",
                    group="",
                    warnings=warnings,
                )
                if dependency is not None:
                    dependencies.append(dependency)
        else:
            section = "project.dependencies"
            unsupported_sections.append(section)
            warnings.append(f"{source_file}: {section} is not a list.")

    optional_dependencies = project.get("optional-dependencies")
    if optional_dependencies is not None:
        if isinstance(optional_dependencies, Mapping):
            for group, group_dependencies in optional_dependencies.items():
                section = f"project.optional-dependencies.{group}"

                if not isinstance(group_dependencies, list):
                    unsupported_sections.append(section)
                    warnings.append(f"{source_file}: {section} is not a list.")
                    continue

                for raw_dependency in group_dependencies:
                    dependency = _dependency_from_requirement_string(
                        raw_dependency,
                        dependency_type="optional",
                        source_file=source_file,
                        source_section=section,
                        group=str(group),
                        warnings=warnings,
                    )
                    if dependency is not None:
                        dependencies.append(dependency)
        else:
            section = "project.optional-dependencies"
            unsupported_sections.append(section)
            warnings.append(f"{source_file}: {section} is not a table.")

    return tuple(dependencies)


def _read_poetry_dependencies(
    data: Mapping[str, Any],
    source_file: str,
    warnings: list[str],
    unsupported_sections: list[str],
) -> tuple[Dependency, ...]:
    poetry = _get_nested_mapping(data, ("tool", "poetry"))
    if poetry is None:
        return ()

    dependencies: list[Dependency] = []

    dependencies.extend(
        _read_poetry_dependency_table(
            poetry.get("dependencies"),
            dependency_type="runtime",
            source_file=source_file,
            source_section="tool.poetry.dependencies",
            group="",
            warnings=warnings,
            unsupported_sections=unsupported_sections,
        )
    )

    dependencies.extend(
        _read_poetry_dependency_table(
            poetry.get("dev-dependencies"),
            dependency_type="development",
            source_file=source_file,
            source_section="tool.poetry.dev-dependencies",
            group="dev",
            warnings=warnings,
            unsupported_sections=unsupported_sections,
        )
    )

    groups = poetry.get("group")
    if groups is not None:
        if not isinstance(groups, Mapping):
            section = "tool.poetry.group"
            unsupported_sections.append(section)
            warnings.append(f"{source_file}: {section} is not a table.")
        else:
            for group_name, group_data in groups.items():
                group_name_text = str(group_name)
                section = f"tool.poetry.group.{group_name_text}.dependencies"

                if not isinstance(group_data, Mapping):
                    unsupported_sections.append(f"tool.poetry.group.{group_name_text}")
                    warnings.append(
                        f"{source_file}: tool.poetry.group.{group_name_text} "
                        "is not a table."
                    )
                    continue

                dependencies.extend(
                    _read_poetry_dependency_table(
                        group_data.get("dependencies"),
                        dependency_type=_poetry_group_dependency_type(group_name_text),
                        source_file=source_file,
                        source_section=section,
                        group=group_name_text,
                        warnings=warnings,
                        unsupported_sections=unsupported_sections,
                    )
                )

    return tuple(dependencies)


def _read_poetry_dependency_table(
    dependency_table: Any,
    *,
    dependency_type: str,
    source_file: str,
    source_section: str,
    group: str,
    warnings: list[str],
    unsupported_sections: list[str],
) -> tuple[Dependency, ...]:
    if dependency_table is None:
        return ()

    if not isinstance(dependency_table, Mapping):
        unsupported_sections.append(source_section)
        warnings.append(f"{source_file}: {source_section} is not a table.")
        return ()

    dependencies: list[Dependency] = []

    for raw_name, raw_constraint in dependency_table.items():
        name = str(raw_name)

        if _is_python_dependency(name):
            continue

        dependency = _dependency_from_name_and_constraint(
            name=name,
            version_constraint=_stringify_poetry_constraint(raw_constraint),
            dependency_type=dependency_type,
            source_file=source_file,
            source_section=source_section,
            raw_value=_poetry_raw_value(name, raw_constraint),
            group=group,
        )
        dependencies.append(dependency)

    return tuple(dependencies)


def _dependency_from_requirement_string(
    raw_dependency: Any,
    *,
    dependency_type: str,
    source_file: str,
    source_section: str,
    group: str,
    warnings: list[str],
) -> Dependency | None:
    if not isinstance(raw_dependency, str):
        warnings.append(
            f"{source_file}: {source_section} contains non-string dependency "
            f"{raw_dependency!r}."
        )
        return None

    cleaned = raw_dependency.strip()
    if not cleaned:
        return None

    match = _REQUIREMENT_NAME_RE.match(cleaned)
    if match is None:
        warnings.append(
            f"{source_file}: could not parse dependency {cleaned!r} "
            f"in {source_section}."
        )
        return None

    name = match.group(1).strip()
    version_constraint = match.group(2).strip()

    return _dependency_from_name_and_constraint(
        name=name,
        version_constraint=version_constraint,
        dependency_type=dependency_type,
        source_file=source_file,
        source_section=source_section,
        raw_value=cleaned,
        group=group,
    )


def _dependency_from_name_and_constraint(
    *,
    name: str,
    version_constraint: str,
    dependency_type: str,
    source_file: str,
    source_section: str,
    raw_value: str,
    group: str,
) -> Dependency:
    return Dependency(
        name=name,
        version_constraint=version_constraint.strip(),
        dependency_type=dependency_type,
        source_file=source_file,
        source_section=source_section,
        raw_value=raw_value.strip() or name,
        group=group,
    )


def _get_nested_mapping(
    data: Mapping[str, Any],
    path: tuple[str, ...],
) -> Mapping[str, Any] | None:
    current: Any = data

    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)

    if isinstance(current, Mapping):
        return current

    return None


def _poetry_group_dependency_type(group_name: str) -> str:
    normalized = normalize_dependency_name(group_name)
    if normalized in _DEVELOPMENT_POETRY_GROUPS:
        return "development"
    return "optional"


def _stringify_poetry_constraint(raw_constraint: Any) -> str:
    if isinstance(raw_constraint, str):
        return raw_constraint.strip()

    if isinstance(raw_constraint, Mapping):
        version = raw_constraint.get("version")
        if isinstance(version, str):
            return version.strip()
        return ""

    return ""


def _poetry_raw_value(name: str, raw_constraint: Any) -> str:
    constraint = _stringify_poetry_constraint(raw_constraint)
    if constraint:
        return f"{name} {constraint}"
    return name


def _is_python_dependency(name: str) -> bool:
    return normalize_dependency_name(name) == "python"


def _unique_sorted_strings(values: Iterable[str]) -> tuple[str, ...]:
    unique_values = {
        str(value).strip()
        for value in values
        if str(value).strip()
    }
    return tuple(sorted(unique_values))


def render_dependency_full_section(report: DependencyReport) -> str:
    """Render a human-readable dependency section for full.txt exports."""

    counts = report.counts_by_type()
    lines: list[str] = [
        "# Dependencies",
        "",
        "## Summary",
        "",
        f"Runtime dependencies: {counts['runtime']}",
        f"Development dependencies: {counts['development']}",
        f"Optional dependencies: {counts['optional']}",
        f"Unknown dependencies: {counts['unknown']}",
        "",
        "## Dependency Files",
        "",
    ]

    if report.dependency_files:
        lines.extend(f"- {dependency_file}" for dependency_file in report.dependency_files)
    else:
        lines.append("No dependency files found.")

    sections = (
        ("runtime", "Runtime Dependencies"),
        ("development", "Development Dependencies"),
        ("optional", "Optional Dependencies"),
        ("unknown", "Unknown Dependencies"),
    )

    for dependency_type, heading in sections:
        lines.extend(["", f"## {heading}", ""])
        dependencies = report.dependencies_by_type(dependency_type)
        if dependencies:
            lines.extend(
                f"- {_format_dependency_for_full_export(dependency)}"
                for dependency in dependencies
            )
        else:
            lines.append("None detected.")

    warnings = tuple(report.warnings) + tuple(report.unsupported_lines)
    if warnings:
        lines.extend(["", "## Unsupported / Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    return "\n".join(lines).rstrip() + "\n"


def insert_dependency_full_section(full_text: str, report: DependencyReport) -> str:
    """Insert the dependency section into an existing full.txt export."""

    if "# Dependencies" in full_text or "## Dependencies" in full_text:
        return full_text

    section = render_dependency_full_section(report).strip()
    normalized_text = full_text.rstrip()

    source_dump_markers = (
        "# Complete Source Dump",
        "## Complete Source Dump",
        "# Source Dump",
        "## Source Dump",
    )

    for marker in source_dump_markers:
        marker_index = normalized_text.find(marker)
        if marker_index == -1:
            continue

        before = normalized_text[:marker_index].rstrip()
        after = normalized_text[marker_index:].lstrip()
        return f"{before}\n\n{section}\n\n{after}\n"

    return f"{normalized_text}\n\n{section}\n"


def append_dependencies_full_section(
    full_text: str,
    repo_root: str | Path,
    files: Iterable[str | Path] | None = None,
) -> str:
    """Analyze dependencies and append/insert the full export section."""

    report = analyze_dependencies(repo_root, files=files)
    return insert_dependency_full_section(full_text, report)


def _format_dependency_for_full_export(dependency: Dependency) -> str:
    display_value = dependency.raw_value or dependency.name

    if dependency.group:
        display_value = f"{dependency.group}: {display_value}"

    details: list[str] = []
    if dependency.source_file:
        details.append(dependency.source_file)
    if dependency.source_section and dependency.source_section != dependency.source_file:
        details.append(dependency.source_section)

    if details:
        display_value = f"{display_value} ({', '.join(details)})"

    return display_value


def render_dependency_ai_section(report: DependencyReport) -> str:
    """Render a compact dependency section for ai.txt exports."""

    lines: list[str] = [
        "## Dependencies",
        "",
    ]

    dependency_sections = (
        ("runtime", "Runtime"),
        ("development", "Development"),
        ("optional", "Optional"),
        ("unknown", "Unknown"),
    )

    for dependency_type, heading in dependency_sections:
        dependencies = report.dependencies_by_type(dependency_type)
        if not dependencies:
            continue

        lines.extend([f"{heading}:", ""])
        lines.extend(
            f"- {_format_dependency_for_ai_export(dependency)}"
            for dependency in dependencies
        )
        lines.append("")

    lines.extend(["Detected files:", ""])
    if report.dependency_files:
        lines.extend(f"- {dependency_file}" for dependency_file in report.dependency_files)
    else:
        lines.append("- None detected")

    warnings = tuple(report.warnings) + tuple(report.unsupported_lines)
    if warnings:
        lines.extend(["", "Warnings:", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    return "\n".join(lines).rstrip() + "\n"


def insert_dependency_ai_section(ai_text: str, report: DependencyReport) -> str:
    """Insert the dependency section into an existing ai.txt export."""

    if "## Dependencies" in ai_text or "# Dependencies" in ai_text:
        return ai_text

    section = render_dependency_ai_section(report).strip()
    normalized_text = ai_text.rstrip()

    preferred_markers = (
        "## Symbol Index",
        "## Import Graph",
        "## Call Graph",
        "# Symbol Index",
        "# Import Graph",
        "# Call Graph",
    )

    for marker in preferred_markers:
        marker_index = normalized_text.find(marker)
        if marker_index == -1:
            continue

        before = normalized_text[:marker_index].rstrip()
        after = normalized_text[marker_index:].lstrip()
        return f"{before}\n\n{section}\n\n{after}\n"

    return f"{normalized_text}\n\n{section}\n"


def append_dependencies_ai_section(
    ai_text: str,
    repo_root: str | Path,
    files: Iterable[str | Path] | None = None,
) -> str:
    """Analyze dependencies and append/insert the ai.txt dependency section."""

    report = analyze_dependencies(repo_root, files=files)
    return insert_dependency_ai_section(ai_text, report)


def _format_dependency_for_ai_export(dependency: Dependency) -> str:
    display_value = dependency.raw_value or dependency.name

    if dependency.group:
        display_value = f"{dependency.group}: {display_value}"

    if dependency.source_file:
        display_value = f"{display_value} ({dependency.source_file})"

    return display_value

