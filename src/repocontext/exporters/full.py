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
        _render_ai_quick_start(context),
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


def _render_ai_quick_start(context: FullExportContext) -> str:
    """Render the AI-oriented quick start summary."""
    return "\n".join(
        [
            FULL_EXPORT_SECTION_HEADINGS["ai_quick_start"],
            "",
            f"Project type: {_detect_project_type(context)}",
            f"Primary language: {_detect_primary_language(context)}",
            f"Package manager: {_detect_package_manager(context)}",
            f"Test framework: {_detect_test_framework(context)}",
            f"Entrypoints: {_format_entrypoints(_detect_entrypoints(context))}",
            f"Purpose: {_detect_project_purpose(context)}",
        ]
    )


def _detect_primary_language(context: FullExportContext) -> str:
    """Detect the dominant language among exported text files."""
    language_counts: Counter[str] = Counter(
        file_info.language
        for file_info in context.exported_text_files
        if file_info.language
    )

    if not language_counts:
        return "Unknown"

    language, _count = sorted(
        language_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[0]
    return _format_language_name(language)


def _detect_project_type(context: FullExportContext) -> str:
    """Infer a simple project type from scanned repository files."""
    paths = _lowercase_scanned_paths(context)
    primary_language = _detect_primary_language(context)

    if "pyproject.toml" in paths and _detect_entrypoints(context):
        return "Python CLI project"

    if "pyproject.toml" in paths or "setup.py" in paths:
        return "Python package"

    if primary_language == "Python":
        return "Python project"

    if primary_language == "Bash":
        return "Bash project"

    if context.exported_text_files and all(
        (file_info.language or "").lower() in {"markdown", "text"}
        for file_info in context.exported_text_files
    ):
        return "Documentation project"

    return "Unknown Git repository"


def _detect_package_manager(context: FullExportContext) -> str:
    """Detect packaging or dependency management files."""
    paths = _lowercase_scanned_paths(context)
    detected: list[str] = []

    for candidate in ("pyproject.toml", "requirements.txt", "setup.py", "package.json"):
        if candidate in paths:
            detected.append(candidate)

    if detected:
        return ", ".join(detected)

    return "Unknown"


def _detect_test_framework(context: FullExportContext) -> str:
    """Detect the likely test framework from repository files."""
    paths = _lowercase_scanned_paths(context)
    combined_text = "\n".join(
        file_info.content or ""
        for file_info in context.exported_text_files
    ).lower()

    has_tests_dir = any(path == "tests" or path.startswith("tests/") for path in paths)

    if "pytest" in combined_text or has_tests_dir:
        return "pytest"

    if "unittest" in combined_text:
        return "unittest"

    return "Unknown"


def _detect_entrypoints(context: FullExportContext) -> tuple[str, ...]:
    """Detect likely command-line entrypoints."""
    pyproject_content = _find_file_content(context, "pyproject.toml")
    if pyproject_content is not None:
        scripts = _parse_pyproject_scripts(pyproject_content)
        if scripts:
            return scripts

    paths = _lowercase_scanned_paths(context)
    fallback_entrypoints: list[str] = []

    for path in sorted(paths):
        if path.endswith("/cli.py") or path == "cli.py":
            fallback_entrypoints.append(path)

    return tuple(fallback_entrypoints)


def _detect_project_purpose(context: FullExportContext) -> str:
    """Detect a short project purpose without inventing details."""
    readme_content = _find_first_matching_file_content(
        context,
        ("readme.md", "readme.txt", "readme"),
    )
    if readme_content:
        purpose = _extract_readme_purpose(readme_content)
        if purpose:
            return purpose

    pyproject_content = _find_file_content(context, "pyproject.toml")
    if pyproject_content:
        description = _extract_pyproject_description(pyproject_content)
        if description:
            return description

    return "Unknown"


def _format_entrypoints(entrypoints: tuple[str, ...]) -> str:
    """Format entrypoint names for display."""
    if not entrypoints:
        return "Unknown"
    return ", ".join(entrypoints)


def _format_language_name(language: str) -> str:
    """Format internal lowercase language names for display."""
    language_names = {
        "bash": "Bash",
        "dockerfile": "Dockerfile",
        "ini": "INI",
        "json": "JSON",
        "makefile": "Makefile",
        "markdown": "Markdown",
        "python": "Python",
        "text": "Text",
        "toml": "TOML",
        "yaml": "YAML",
    }
    return language_names.get(language.lower(), language.title())


def _lowercase_scanned_paths(context: FullExportContext) -> set[str]:
    """Return scanned repository-relative paths as lowercase POSIX strings."""
    return {
        file_info.relative_path.as_posix().lower()
        for file_info in context.sorted_files
    }


def _find_file_content(context: FullExportContext, relative_path: str) -> str | None:
    """Return content for a scanned file matching a repository-relative path."""
    normalized_relative_path = relative_path.lower()
    for file_info in context.exported_text_files:
        if file_info.relative_path.as_posix().lower() == normalized_relative_path:
            return file_info.content
    return None


def _find_first_matching_file_content(
    context: FullExportContext,
    candidate_paths: tuple[str, ...],
) -> str | None:
    """Return content for the first matching candidate path."""
    for candidate_path in candidate_paths:
        content = _find_file_content(context, candidate_path)
        if content is not None:
            return content
    return None


def _parse_pyproject_scripts(pyproject_content: str) -> tuple[str, ...]:
    """Parse simple project.scripts entries from pyproject.toml content."""
    scripts: list[str] = []
    in_scripts_section = False

    for raw_line in pyproject_content.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            in_scripts_section = line == "[project.scripts]"
            continue

        if not in_scripts_section or "=" not in line:
            continue

        script_name = line.split("=", 1)[0].strip()
        if script_name:
            scripts.append(script_name)

    return tuple(sorted(scripts))


def _extract_readme_purpose(readme_content: str) -> str | None:
    """Extract a short purpose from the first useful README paragraph."""
    first_heading: str | None = None

    for raw_line in readme_content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            if first_heading is None:
                first_heading = line.lstrip("#").strip() or None
            continue

        return line

    return first_heading


def _extract_pyproject_description(pyproject_content: str) -> str | None:
    """Extract a simple project description from pyproject.toml content."""
    for raw_line in pyproject_content.splitlines():
        line = raw_line.strip()

        if not line.startswith("description") or "=" not in line:
            continue

        _key, raw_value = line.split("=", 1)
        value = raw_value.strip().strip('"').strip("'")
        if value:
            return value

    return None


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
