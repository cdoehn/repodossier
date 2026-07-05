"""Foundational structures and orchestration for the Full Export MVP."""

from __future__ import annotations
from repodossier.languages import code_fence_language as _shared_code_fence_language
from repodossier.languages import display_language_name as _shared_display_language_name

from repodossier.secrets import SecretFinding, mask_secrets_in_text

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from repodossier.dependencies import analyze_dependencies, render_dependency_full_section
from repodossier.git import RepositoryInfo, get_repository_info
from repodossier.gitignore import ensure_repodossier_gitignore_entries
from repodossier.models import FileInfo
from repodossier.scanner import RepositoryScanner
from repodossier.schema import analyze_database_schemas
from repodossier.config import apply_config_to_file_infos, apply_export_byte_limit, format_limit_notice, full_config_summary_section, get_active_config, is_file_size_allowed, truncate_text_by_line_limit

FULL_EXPORT_SECTION_ORDER: tuple[str, ...] = (
    "ai_quick_start",
    "repository_statistics",
    "file_summary",
    "repository_tree",
    "dependencies",
    "database_schema",
    "complete_source_export",
    "warnings",
)

FULL_EXPORT_SECTION_HEADINGS: dict[str, str] = {
    "ai_quick_start": "# AI Quick Start",
    "repository_statistics": "# Repository Statistics",
    "file_summary": "# File Summary",
    "repository_tree": "# Repository Tree",
    "dependencies": "# Dependencies",
    "database_schema": "# Database Schema",
    "complete_source_export": "# Complete Source Export",
    "warnings": "# Warnings",
}


CALL_GRAPH_MAX_INTERNAL_EDGES = 200
CALL_GRAPH_MAX_EXTERNAL_EDGES = 25
CALL_GRAPH_MAX_AMBIGUOUS_EDGES = 25
CALL_GRAPH_MAX_UNRESOLVED_EDGES = 25

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



def _file_info_size_bytes(file_info: FileInfo) -> int | None:
    """Return file size from FileInfo metadata, filesystem, or loaded content."""

    for attribute in ("size_bytes", "size", "byte_count"):
        value = getattr(file_info, attribute, None)
        if isinstance(value, int):
            return value

    content = getattr(file_info, "content", None)
    if isinstance(content, str):
        return len(content.encode("utf-8"))

    path = getattr(file_info, "path", None)
    if path is None:
        path = getattr(file_info, "absolute_path", None)
    if path is None:
        path = getattr(file_info, "file_path", None)

    if path is None:
        return None

    try:
        return Path(path).stat().st_size
    except OSError:
        return None


def _file_info_display_path(file_info: FileInfo) -> str:
    """Return a stable display path for source-dump notices."""

    for attribute in ("relative_path", "path", "file_path", "filepath"):
        value = getattr(file_info, attribute, None)
        if value is not None:
            if hasattr(value, "as_posix"):
                return value.as_posix()
            return str(value).replace("\\", "/")

    return "<unknown file>"


def _should_skip_file_content_for_size_limit(file_info: FileInfo) -> bool:
    """Return whether file content should be skipped by max_file_bytes."""

    return not is_file_size_allowed(_file_info_size_bytes(file_info), get_active_config())


def _max_file_bytes_notice(file_info: FileInfo) -> str:
    size = _file_info_size_bytes(file_info)
    configured_limit = get_active_config().limits.max_file_bytes
    if size is None:
        return format_limit_notice(
            f"{_file_info_display_path(file_info)} exceeds limits.max_file_bytes"
        )
    return format_limit_notice(
        f"{_file_info_display_path(file_info)} has {size} bytes "
        f"and exceeds limits.max_file_bytes={configured_limit}"
    )

def create_full_export_context(
    repository_info: RepositoryInfo,
    scanned_files: Sequence[FileInfo],
    warnings: Sequence[str] = (),
) -> FullExportContext:
    """Create a Full Export context from repository and scanner results."""

    selection = apply_config_to_file_infos(
        scanned_files,
        get_active_config(),
    )
    filtered_scanned_files = list(selection.files)

    return FullExportContext(
        repository_info=repository_info,
        scanned_files=filtered_scanned_files,
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


def _render_full_export_unmasked(context: FullExportContext) -> str:
    """Render a minimal Full Export skeleton.

    Later Milestone 3 steps expand each section with its final content.
    This function already keeps the section order stable and makes the
    default CLI command able to produce full.txt.
    """
    sections = [
        _render_ai_quick_start(context),
        _render_repository_statistics(context),
        _render_file_summary(context),
        _render_repository_tree(context),
        _render_dependencies(context),
        _render_database_schema(context),
        _render_complete_source_export(context),
        _render_warnings(context),
    ]
    return "\n\n".join(section.rstrip() for section in sections).rstrip() + "\n"




def _format_full_secret_detection_section(findings: list[SecretFinding]) -> str:
    """Format the full export secret detection summary without leaking values."""

    lines = [
        "# Secret Detection",
        "",
        f"Total findings: {len(findings)}",
    ]

    if not findings:
        return "\n".join(lines)

    counts_by_type: dict[str, int] = {}
    for finding in findings:
        counts_by_type[finding.secret_type] = counts_by_type.get(finding.secret_type, 0) + 1

    lines.extend(["", "Findings by type:"])
    for secret_type in sorted(counts_by_type):
        lines.append(f"- {secret_type}: {counts_by_type[secret_type]}")

    return "\n".join(lines)


def _insert_full_secret_detection_section(text: str, section: str) -> str:
    """Insert the secret detection section before the source dump when possible."""

    source_dump_markers = [
        "\n# Complete Source Export",
        "\n# Complete source dump",
        "\n# Source Dump",
        "\n# Source dump",
    ]

    for marker in source_dump_markers:
        marker_index = text.find(marker)
        if marker_index != -1:
            before = text[:marker_index].rstrip()
            after = text[marker_index:].lstrip("\n")
            return f"{before}\n\n{section}\n\n{after}"

    return f"{text.rstrip()}\n\n{section}\n"


def render_full_export(*args: object, **kwargs: object) -> str:
    """Render the full export with potential secrets masked."""

    rendered = _render_full_export_unmasked(*args, **kwargs)
    masked_text, findings = mask_secrets_in_text(rendered, "full.txt")
    secret_section = _format_full_secret_detection_section(findings)
    return _insert_full_secret_detection_section(masked_text, secret_section)
def write_full_export(
    context: FullExportContext,
    output_path: Path | str | None = None,
) -> Path:
    """Write the rendered Full Export atomically and return its path."""
    resolved_output_path = _resolve_full_export_output_path(context, output_path)
    temporary_output_path = _temporary_full_export_output_path(resolved_output_path)
    rendered_export = render_full_export(context)

    try:
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        rendered_export = full_config_summary_section(get_active_config()) + "\n" + rendered_export
        rendered_export = apply_export_byte_limit(
            rendered_export,
            get_active_config(),
        )
        temporary_output_path.write_text(rendered_export, encoding="utf-8")
        temporary_output_path.replace(resolved_output_path)
    except OSError:
        _remove_temporary_output_file(temporary_output_path)
        raise

    return resolved_output_path


def _resolve_full_export_output_path(
    context: FullExportContext,
    output_path: Path | str | None,
) -> Path:
    """Resolve the final Full Export output path."""
    if output_path is not None:
        return Path(output_path).resolve()

    return context.repository_root / "full.txt"


def _temporary_full_export_output_path(output_path: Path) -> Path:
    """Return the temporary path used for atomic Full Export writes."""
    return output_path.with_name(f".{output_path.name}.tmp")


def _remove_temporary_output_file(temporary_output_path: Path) -> None:
    """Best-effort cleanup for a failed temporary export write."""
    try:
        temporary_output_path.unlink(missing_ok=True)
    except OSError:
        pass


def generate_full_export(repository_root: Path | str) -> Path:
    """Build, render, and write the Full Export for a repository."""
    resolved_repository_root = Path(repository_root).resolve()
    ensure_repodossier_gitignore_entries(resolved_repository_root)
    context = build_full_export_context(resolved_repository_root)
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
    return language_names.get(language.lower(), _display_language_name(language))


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


def _render_file_summary(context: FullExportContext) -> str:
    """Render a readable grouped summary of all exported text files."""
    lines = [
        FULL_EXPORT_SECTION_HEADINGS["file_summary"],
        "",
    ]

    if not context.exported_text_files:
        lines.append("No exportable text files.")
        return "\n".join(lines)

    grouped_files = _group_file_summary_entries(context)

    lines.extend(
        [
            f"Exported text files: {len(context.exported_text_files)}",
            f"Total lines: {_format_number(context.total_line_count)}",
            f"Estimated tokens: {_format_number(context.total_estimated_tokens)}",
            "",
        ]
    )

    for group_index, (language, entries) in enumerate(grouped_files):
        if group_index > 0:
            lines.append("")

        file_word = "file" if len(entries) == 1 else "files"
        lines.append(f"## {language} ({len(entries)} {file_word})")

        for file_info in entries:
            lines.append(_format_file_summary_entry(file_info))

    return "\n".join(lines)


def _group_file_summary_entries(
    context: FullExportContext,
) -> tuple[tuple[str, tuple[FileInfo, ...]], ...]:
    """Group exported text files by display language in stable order."""
    grouped: dict[str, list[FileInfo]] = {}

    for file_info in context.exported_text_files:
        language = (
            _format_language_name(file_info.language)
            if file_info.language
            else "Unknown"
        )
        grouped.setdefault(language, []).append(file_info)

    return tuple(
        (language, tuple(files))
        for language, files in sorted(grouped.items(), key=lambda item: item[0])
    )


def _format_file_summary_entry(file_info: FileInfo) -> str:
    """Format one file summary bullet."""
    path = _format_inline_code(file_info.relative_path.as_posix())
    line_count = file_info.line_count or 0
    token_count = file_info.estimated_tokens or 0
    line_word = "line" if line_count == 1 else "lines"
    token_word = "token" if token_count == 1 else "tokens"

    return (
        f"- {path} — "
        f"{_format_number(line_count)} {line_word}, "
        f"~{_format_number(token_count)} {token_word}"
    )


def _format_number(value: int) -> str:
    """Format integers for human-readable export summaries."""
    return f"{value:,}"


def _format_inline_code(value: str) -> str:
    """Format a value as Markdown inline code."""
    return f"`{value.replace('`', '\\`')}`"


def _render_repository_tree(context: FullExportContext) -> str:
    """Render a deterministic tree view of scanned Git-tracked files."""
    lines = [
        FULL_EXPORT_SECTION_HEADINGS["repository_tree"],
        "",
        ".",
    ]

    if not context.sorted_files:
        return "\n".join(lines)

    tree = _build_repository_tree(context)
    lines.extend(_format_repository_tree_items(tree))

    return "\n".join(lines)


def _build_repository_tree(context: FullExportContext) -> dict[str, object]:
    """Build a nested dictionary tree from repository-relative file paths."""
    root: dict[str, object] = {}

    for file_info in context.sorted_files:
        path_parts = file_info.relative_path.parts
        if not path_parts:
            continue

        current_node = root
        for directory_name in path_parts[:-1]:
            existing_node = current_node.get(directory_name)
            if not isinstance(existing_node, dict):
                existing_node = {}
                current_node[directory_name] = existing_node
            current_node = existing_node

        current_node[path_parts[-1]] = _repository_tree_file_label(file_info)

    return root


def _format_repository_tree_items(
    tree: dict[str, object],
    prefix: str = "",
) -> list[str]:
    """Format nested tree items using common tree drawing characters."""
    lines: list[str] = []
    items = sorted(tree.items(), key=lambda item: item[0])

    for index, (name, value) in enumerate(items):
        is_last = index == len(items) - 1
        branch = "└── " if is_last else "├── "

        if isinstance(value, dict):
            lines.append(f"{prefix}{branch}{name}")
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(_format_repository_tree_items(value, child_prefix))
        else:
            lines.append(f"{prefix}{branch}{value}")

    return lines


def _repository_tree_file_label(file_info: FileInfo) -> str:
    """Return the display label for one file inside the repository tree."""
    label = file_info.relative_path.name
    markers: list[str] = []

    if file_info.is_binary is True:
        markers.append("binary skipped")

    if file_info.error is not None:
        markers.append("error")

    if markers:
        return f"{label} [{', '.join(markers)}]"

    return label



def _render_dependencies(context: FullExportContext) -> str:
    """Render dependency information for the Full Export."""

    dependency_report = analyze_dependencies(
        context.repository_root,
        files=(file_info.relative_path for file_info in context.scanned_files),
    )
    return render_dependency_full_section(dependency_report).rstrip()


def _render_database_schema(context: FullExportContext) -> str:
    """Render database schema information for the Full Export."""

    try:
        schema_report = analyze_database_schemas(
            context.repository_root,
            files=context.scanned_files,
        )
    except Exception as exc:
        return "\n".join(
            [
                FULL_EXPORT_SECTION_HEADINGS["database_schema"],
                "",
                "## Summary",
                "",
                "Database files: 0",
                "SQL schema files: 0",
                "Tables: 0",
                "Views: 0",
                "Warnings: 1",
                "",
                "## Schema Warnings",
                "",
                f"- Could not analyze database schemas: {type(exc).__name__}: {exc}",
            ]
        )

    return _format_database_schema_full_section(schema_report)


def _format_database_schema_full_section(schema_report) -> str:
    """Format a DatabaseSchemaReport as the full.txt Database Schema section."""

    lines = [
        FULL_EXPORT_SECTION_HEADINGS["database_schema"],
        "",
        "## Summary",
        "",
        f"Database files: {len(schema_report.database_files)}",
        f"SQL schema files: {len(schema_report.sql_schema_files)}",
        f"Tables: {len(schema_report.tables)}",
        f"Views: {len(schema_report.views)}",
        f"Warnings: {len(schema_report.warnings)}",
        "",
        "## Database Files",
        "",
    ]

    database_paths = tuple(schema_report.database_files) + tuple(schema_report.sql_schema_files)
    if database_paths:
        lines.extend(f"- {path}" for path in database_paths)
    else:
        lines.append("No database schema files detected.")

    lines.extend(["", "## Tables", ""])
    if schema_report.tables:
        _append_schema_tables(lines, schema_report.tables)
    else:
        lines.append("No database tables detected.")

    lines.extend(["", "## Views", ""])
    if schema_report.views:
        _append_schema_tables(lines, schema_report.views)
    else:
        lines.append("No database views detected.")

    lines.extend(["", "## CREATE TABLE Statements", ""])
    _append_create_statements(lines, schema_report.create_statements)

    lines.extend(["", "## Schema Warnings", ""])
    if schema_report.warnings:
        lines.extend(f"- {warning}" for warning in schema_report.warnings)
    else:
        lines.append("No schema warnings.")

    return "\n".join(lines).rstrip()


def _append_schema_tables(lines: list[str], tables) -> None:
    """Append formatted schema tables or views to the output lines."""

    for table_index, table in enumerate(tables):
        if table_index > 0:
            lines.append("")

        lines.append(f"### {table.name}")
        lines.append(f"Source: {table.source_file or 'unknown'}")
        lines.append(f"Type: {table.table_type}")
        lines.append("")
        lines.append("Columns:")

        if table.columns:
            for column in table.columns:
                lines.append(f"- {_format_schema_column(column)}")
        else:
            lines.append("- none")

        if table.foreign_keys:
            lines.append("")
            lines.append("Foreign keys:")
            for foreign_key in table.foreign_keys:
                lines.append(f"- {_format_schema_foreign_key(foreign_key)}")

        if table.indexes:
            lines.append("")
            lines.append("Indexes:")
            for index in table.indexes:
                lines.append(f"- {_format_schema_index(index)}")


def _format_schema_column(column) -> str:
    """Format one database column in compact full.txt form."""

    parts = [column.name]

    if column.data_type:
        parts.append(column.data_type)

    if column.is_primary_key:
        parts.append("PRIMARY KEY")

    if column.nullable is False:
        parts.append("NOT NULL")
    elif column.nullable is True:
        parts.append("NULL")

    if column.default_value is not None:
        parts.append(f"DEFAULT {column.default_value}")

    return " ".join(parts)


def _format_schema_foreign_key(foreign_key) -> str:
    """Format one database foreign-key relationship."""

    line = (
        f"{foreign_key.from_column} -> "
        f"{foreign_key.to_table}.{foreign_key.to_column}"
    )

    actions: list[str] = []
    if foreign_key.on_update:
        actions.append(f"ON UPDATE {foreign_key.on_update}")
    if foreign_key.on_delete:
        actions.append(f"ON DELETE {foreign_key.on_delete}")

    if actions:
        line += f" ({', '.join(actions)})"

    return line


def _format_schema_index(index) -> str:
    """Format one database index."""

    unique_prefix = "UNIQUE " if index.unique else ""
    columns = ", ".join(index.columns) if index.columns else "unknown columns"
    return f"{index.name} {unique_prefix}({columns})"


def _append_create_statements(lines: list[str], create_statements) -> None:
    """Append limited CREATE TABLE statements to the Database Schema section."""

    if not create_statements:
        lines.append("No CREATE TABLE statements detected.")
        return

    max_statements = 20
    max_statement_length = 800

    visible_statements = tuple(create_statements[:max_statements])
    for statement_index, statement in enumerate(visible_statements, start=1):
        compact_statement = " ".join(str(statement).split())
        if len(compact_statement) > max_statement_length:
            compact_statement = compact_statement[: max_statement_length - 4].rstrip() + " ..."

        lines.append(f"{statement_index}. `{compact_statement}`")

    remaining_count = len(create_statements) - len(visible_statements)
    if remaining_count > 0:
        lines.append(f"- ... {remaining_count} more")


def _apply_max_export_bytes_limit(rendered: str) -> str:
    """Apply the global max_export_bytes limit to a rendered full export."""

    limit = get_active_config().limits.max_export_bytes
    if limit is None:
        return rendered

    rendered_bytes = rendered.encode("utf-8")
    if len(rendered_bytes) <= limit:
        return rendered

    notice = "\n\n" + format_limit_notice("limits.max_export_bytes was reached") + "\n"
    notice_bytes = notice.encode("utf-8")

    if len(notice_bytes) >= limit:
        return notice_bytes[:limit].decode("utf-8", errors="ignore")

    available_bytes = limit - len(notice_bytes)
    truncated = rendered_bytes[:available_bytes].decode("utf-8", errors="ignore").rstrip()
    return truncated + notice

def _render_complete_source_export(context: FullExportContext) -> str:
    """Render the complete source dump for all exported text files."""
    parts = [
        FULL_EXPORT_SECTION_HEADINGS["complete_source_export"],
        "",
    ]

    if not context.exported_text_files:
        parts.append("No exportable text files.")
        return "\n".join(parts)

    for file_info in context.exported_text_files:
        if _should_skip_file_content_for_size_limit(file_info):
            notice_block = (
                f"## File: {file_info.relative_path.as_posix()}\n\n"
                f"{_max_file_bytes_notice(file_info)}"
            )
            parts.append(notice_block)
            continue

        content = file_info.content or ""
        content, line_truncated, omitted_lines = truncate_text_by_line_limit(
            content,
            get_active_config(),
        )
        if line_truncated:
            if content and not content.endswith("\n"):
                content += "\n"
            content += format_limit_notice(
                "limits.max_line_count was reached",
                omitted_count=omitted_lines,
            )
            content += "\n"

        fence = _choose_code_fence(content)
        language = _code_fence_language(file_info.language)
        opening_fence = f"{fence}{language}" if language else fence

        file_block = (
            f"## File: {file_info.relative_path.as_posix()}\n\n"
            f"{opening_fence}\n"
            f"{content}"
        )

        if not file_block.endswith("\n"):
            file_block += "\n"

        file_block += fence
        parts.append(file_block)

    return _apply_max_export_bytes_limit("\n\n".join(parts))


def _choose_code_fence(content: str) -> str:
    """Choose a Markdown code fence that is longer than fences in the content."""
    backtick = chr(96)
    fence = backtick * 3

    while fence in content:
        fence += backtick

    return fence


def _display_language_name(language: str | None) -> str:
    """Return a human-readable language group name for file summaries."""

    return _shared_display_language_name(language)


def _code_fence_language(language: str | None) -> str:
    """Return a Markdown code fence language for source blocks."""

    return _shared_code_fence_language(language)


def _render_warnings(context: FullExportContext) -> str:
    """Render collected Full Export warnings."""
    warnings = _collect_warnings(context)
    lines = [
        FULL_EXPORT_SECTION_HEADINGS["warnings"],
        "",
    ]

    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("No warnings.")

    return "\n".join(lines)


def _collect_warnings(context: FullExportContext) -> tuple[str, ...]:
    """Collect automatic and explicitly supplied warnings for the Full Export."""
    warnings: list[str] = list(context.warnings)

    if context.tracked_file_count == 0:
        warnings.append("No Git-tracked files found.")

    for file_info in context.skipped_binary_files:
        warnings.append(
            f"Skipped binary file: {file_info.relative_path.as_posix()}"
        )

    for file_info in context.errored_files:
        error_detail = file_info.error or "unknown error"
        warnings.append(
            f"Could not read file: {file_info.relative_path.as_posix()} ({error_detail})"
        )

    if context.tracked_file_count > 0 and not context.exported_text_files:
        warnings.append("No exportable text files found.")

    return tuple(warnings)




def _sorted_import_graph_edges(import_graph):
    """Return local dependency edges in deterministic display order."""

    return tuple(
        sorted(
            import_graph.edges,
            key=lambda edge: (
                edge.source_module,
                edge.target_module,
                edge.line_number,
                edge.import_type,
                edge.imported_name or "",
                edge.source_path.as_posix(),
                edge.target_path.as_posix(),
            ),
        )
    )


def _sorted_external_import_names(import_graph):
    """Return external import module names in deterministic display order."""

    return tuple(
        sorted(
            {
                reference.imported_module
                for reference in import_graph.external_imports
                if reference.imported_module
            }
        )
    )


def _sorted_unresolved_imports(import_graph):
    """Return unresolved imports in deterministic display order."""

    return tuple(
        sorted(
            import_graph.unresolved_imports,
            key=lambda reference: (
                reference.source_module,
                reference.imported_module or "",
                reference.imported_name or "",
                reference.line_number,
                reference.level,
            ),
        )
    )


def _sorted_import_graph_errors(import_graph):
    """Return import analysis errors in deterministic display order."""

    return tuple(
        sorted(
            import_graph.errors,
            key=lambda error: (
                error.source_path.as_posix(),
                error.error_type,
                error.line_number or 0,
                error.message,
            ),
        )
    )


def _append_limited_items(lines, items, *, max_items, formatter):
    """Append sorted display items with a deterministic truncation line."""

    if not items:
        lines.append("- none")
        return

    for item in items[:max_items]:
        lines.append(formatter(item))

    remaining_count = len(items) - max_items
    if remaining_count > 0:
        lines.append(f"- ... {remaining_count} more")


def _format_import_graph_section(import_graph, *, max_edges=200, max_imports=100):
    """Render a compact Import Graph section for full.txt."""

    from repodossier.import_graph import calculate_import_graph_metrics

    metrics = calculate_import_graph_metrics(import_graph)
    sorted_edges = _sorted_import_graph_edges(import_graph)
    external_names = _sorted_external_import_names(import_graph)
    unresolved_imports = _sorted_unresolved_imports(import_graph)
    analysis_errors = _sorted_import_graph_errors(import_graph)

    lines = [
        "## Import Graph",
        "",
        "Summary:",
        f"- Local modules: {metrics.module_count}",
        f"- Local dependencies: {metrics.local_dependency_count}",
        f"- External imports: {metrics.external_import_count}",
        f"- Unresolved imports: {metrics.unresolved_import_count}",
        f"- Analysis errors: {metrics.error_count}",
        "",
    ]

    if metrics.root_modules:
        lines.append("Root modules:")
        _append_limited_items(
            lines,
            metrics.root_modules,
            max_items=max_imports,
            formatter=lambda module_name: f"- {module_name}",
        )
        lines.append("")

    if metrics.leaf_modules:
        lines.append("Leaf modules:")
        _append_limited_items(
            lines,
            metrics.leaf_modules,
            max_items=max_imports,
            formatter=lambda module_name: f"- {module_name}",
        )
        lines.append("")

    lines.append("Local dependencies:")
    _append_limited_items(
        lines,
        sorted_edges,
        max_items=max_edges,
        formatter=lambda edge: f"- {edge.source_module} -> {edge.target_module}",
    )
    lines.append("")

    lines.append("External imports:")
    _append_limited_items(
        lines,
        external_names,
        max_items=max_imports,
        formatter=lambda imported_module: f"- {imported_module}",
    )
    lines.append("")

    lines.append("Unresolved imports:")
    _append_limited_items(
        lines,
        unresolved_imports,
        max_items=max_imports,
        formatter=_format_unresolved_import_line,
    )
    lines.append("")

    if analysis_errors:
        lines.append("Analysis errors:")
        _append_limited_items(
            lines,
            analysis_errors,
            max_items=max_imports,
            formatter=lambda error: (
                f"- {error.source_path}: {error.error_type}: {error.message}"
            ),
        )
        lines.append("")

    return "\n".join(lines).rstrip()


def _format_unresolved_import_line(reference):
    """Format one unresolved import reference."""

    imported = reference.imported_module or "."
    if reference.imported_name:
        imported = f"{imported}.{reference.imported_name}"
    return f"- {reference.source_module}: {imported}"


# Import graph integration for the full export pipeline.
#
# This adapter connects the existing export file list to the import graph
# builder. Rendering the graph into full.txt is handled separately.
def _import_graph_export_source_path(file_info, repo_root):
    """Return a Python source path from an export/scanner file object."""

    from pathlib import Path

    root = Path(repo_root)
    raw_path = None

    if isinstance(file_info, (str, Path)):
        raw_path = file_info
    else:
        for attribute_name in (
            "path",
            "source_path",
            "absolute_path",
            "relative_path",
            "repo_relative_path",
        ):
            if not hasattr(file_info, attribute_name):
                continue

            value = getattr(file_info, attribute_name)
            if value:
                raw_path = value
                break

    if not isinstance(file_info, (str, Path)):
        if getattr(file_info, "is_binary", False) is True:
            return None
        if getattr(file_info, "is_text", True) is False:
            return None
        if getattr(file_info, "error", None):
            return None

    if raw_path is None:
        return None

    path = Path(raw_path)
    if path.suffix != ".py":
        return None

    if not path.is_absolute():
        path = root / path

    return path


def _build_import_graph_for_export(repo_root, files):
    """Build an import graph from the file list used by the export pipeline."""

    from repodossier.import_graph import build_import_graph

    source_paths = []
    for file_info in files:
        source_path = _import_graph_export_source_path(file_info, repo_root)
        if source_path is not None:
            source_paths.append(source_path)

    return build_import_graph(source_paths, repo_root=repo_root)


def _call_graph_export_source_paths(repo_root, files):
    """Return Python source paths from the file list used by the export pipeline."""

    source_paths = []
    for file_info in files:
        source_path = _import_graph_export_source_path(file_info, repo_root)
        if source_path is not None:
            source_paths.append(source_path)

    return tuple(
        sorted(
            source_paths,
            key=lambda path: Path(path).as_posix(),
        )
    )


def _call_graph_export_source_entries(repo_root, files):
    """Return Python source paths and optional scanner-provided source text."""

    entries = []

    for file_info in files:
        source_path = _import_graph_export_source_path(file_info, repo_root)
        if source_path is None:
            continue

        source_content = None
        if not isinstance(file_info, (str, Path)):
            content = getattr(file_info, "content", None)
            if isinstance(content, str):
                source_content = content

        entries.append((source_path, source_content))

    return tuple(
        sorted(
            entries,
            key=lambda item: Path(item[0]).as_posix(),
        )
    )


def _call_graph_display_source_path(source_path, repo_root):
    """Return a stable repository-relative source path for call graph edges."""

    path = Path(source_path)
    root = Path(repo_root)

    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return path


def _build_call_graph_for_export(repo_root, files, *, import_graph=None):
    """Build a call graph from the file list used by the export pipeline."""

    from repodossier.call_graph import CallGraph, parse_calls_from_source
    from repodossier.import_graph import build_import_graph, module_name_from_python_path
    from repodossier.symbols import build_symbol_index

    source_entries = _call_graph_export_source_entries(repo_root, files)
    source_paths = tuple(
        source_path
        for source_path, _source_content in source_entries
    )
    symbol_index = build_symbol_index(source_paths, base_path=repo_root)

    if import_graph is None:
        import_graph = build_import_graph(source_paths, repo_root=repo_root)

    call_graph = CallGraph()

    for source_path, source_content in source_entries:
        module_name = module_name_from_python_path(source_path, repo_root=repo_root)
        if module_name is None:
            continue

        try:
            source = (
                source_content
                if source_content is not None
                else Path(source_path).read_text(encoding="utf-8")
            )
            file_graph = parse_calls_from_source(
                source,
                source_path=_call_graph_display_source_path(source_path, repo_root),
                module_name=module_name,
                symbol_index=symbol_index,
                import_graph=import_graph,
            )
        except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
            continue

        for edge in file_graph.sorted_edges():
            call_graph.add_edge(edge)

    return call_graph


def _format_call_graph_edge_line(edge):
    """Format one call graph edge below a grouped caller heading."""

    line_number = edge.line_number if edge.line_number is not None else "unknown"
    return (
        f"  - line {line_number}: calls {edge.callee_key} "
        f"[{edge.call_type}, {edge.confidence}]"
    )


def _append_grouped_call_graph_edges(lines, edges, *, max_edges):
    """Append call graph edges grouped by caller symbol."""

    if not edges:
        lines.append("- none")
        return

    visible_edges = edges[:max_edges]
    current_caller = None

    for edge in visible_edges:
        caller = edge.caller_key
        if caller != current_caller:
            if current_caller is not None:
                lines.append("")
            lines.append(f"{caller} ({edge.caller_file})")
            current_caller = caller

        lines.append(_format_call_graph_edge_line(edge))

    remaining_count = len(edges) - max_edges
    if remaining_count > 0:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"- ... {remaining_count} more")


def _is_internal_call_graph_edge(edge):
    """Return True for repo-relevant resolved call graph edges."""

    return edge.confidence in {"local", "local_method", "imported_local"}


def _is_external_call_graph_edge(edge):
    """Return True for calls known to target external modules."""

    return edge.confidence == "external"


def _is_ambiguous_call_graph_edge(edge):
    """Return True for intentionally ambiguous call graph edges."""

    return edge.confidence == "ambiguous"


def _is_unresolved_call_graph_edge(edge):
    """Return True for unresolved call graph edges."""

    return edge.confidence.startswith("unresolved")


def _format_call_graph_summary_edge_line(edge):
    """Format one compact non-prominent call graph edge."""

    line_number = edge.line_number if edge.line_number is not None else "unknown"
    return (
        f"- {edge.caller_key} -> {edge.callee_key} "
        f"(line {line_number}, {edge.call_type}, {edge.confidence})"
    )


def _split_call_graph_edges(edges):
    """Split call graph edges into prominent and noisy groups."""

    internal_edges = []
    external_edges = []
    ambiguous_edges = []
    unresolved_edges = []
    other_edges = []

    for edge in edges:
        if _is_internal_call_graph_edge(edge):
            internal_edges.append(edge)
        elif _is_external_call_graph_edge(edge):
            external_edges.append(edge)
        elif _is_ambiguous_call_graph_edge(edge):
            ambiguous_edges.append(edge)
        elif _is_unresolved_call_graph_edge(edge):
            unresolved_edges.append(edge)
        else:
            other_edges.append(edge)

    return (
        tuple(internal_edges),
        tuple(external_edges),
        tuple(ambiguous_edges),
        tuple(unresolved_edges),
        tuple(other_edges),
    )


def _format_call_graph_section(
    call_graph,
    *,
    max_edges=CALL_GRAPH_MAX_INTERNAL_EDGES,
    max_external_edges=CALL_GRAPH_MAX_EXTERNAL_EDGES,
    max_ambiguous_edges=CALL_GRAPH_MAX_AMBIGUOUS_EDGES,
    max_unresolved_edges=CALL_GRAPH_MAX_UNRESOLVED_EDGES,
):
    """Render a compact Call Graph section for full.txt.

    Resolved repo-internal calls are shown prominently and grouped by caller.
    External, ambiguous, and unresolved calls are separated and limited so the
    export remains useful for large projects.
    """

    edges = tuple(call_graph.sorted_edges())
    (
        internal_edges,
        external_edges,
        ambiguous_edges,
        unresolved_edges,
        other_edges,
    ) = _split_call_graph_edges(edges)

    lines = [
        "## Call Graph",
        "",
        "Summary:",
        f"- Call edges: {len(edges)}",
        f"- Local/internal calls: {len(internal_edges)}",
        f"- External calls: {len(external_edges)}",
        f"- Ambiguous calls: {len(ambiguous_edges)}",
        f"- Unresolved calls: {len(unresolved_edges)}",
        "",
        "Internal calls by caller:",
    ]

    _append_grouped_call_graph_edges(
        lines,
        internal_edges,
        max_edges=max_edges,
    )

    lines.extend(["", "External calls:"])
    _append_limited_items(
        lines,
        external_edges,
        max_items=max_external_edges,
        formatter=_format_call_graph_summary_edge_line,
    )

    lines.extend(["", "Ambiguous calls:"])
    _append_limited_items(
        lines,
        ambiguous_edges,
        max_items=max_ambiguous_edges,
        formatter=_format_call_graph_summary_edge_line,
    )

    lines.extend(["", "Unresolved calls:"])
    _append_limited_items(
        lines,
        unresolved_edges,
        max_items=max_unresolved_edges,
        formatter=_format_call_graph_summary_edge_line,
    )

    if other_edges:
        lines.extend(["", "Other calls:"])
        _append_limited_items(
            lines,
            other_edges,
            max_items=max_unresolved_edges,
            formatter=_format_call_graph_summary_edge_line,
        )

    return "\n".join(lines).rstrip()


_ORIGINAL_RENDER_FULL_EXPORT_WITHOUT_IMPORT_GRAPH = render_full_export


def render_full_export(*args, **kwargs):
    """Render the full export and append the Import Graph section when possible."""

    output = _ORIGINAL_RENDER_FULL_EXPORT_WITHOUT_IMPORT_GRAPH(*args, **kwargs)

    if not isinstance(output, str):
        return _apply_max_export_bytes_limit(output)
    repo_root = kwargs.get("repo_root")
    files = kwargs.get("files")

    # Most full-export renderers receive a FullExportContext. Prefer context fields.
    context = None
    for value in list(args) + list(kwargs.values()):
        if hasattr(value, "repository_info"):
            context = value
            break

    if context is not None:
        repository_info = getattr(context, "repository_info", None)
        if repo_root is None and repository_info is not None:
            repo_root = getattr(repository_info, "root_path", None)

        if files is None:
            for attribute_name in ("files", "scanned_files", "file_summaries"):
                if hasattr(context, attribute_name):
                    candidate_files = getattr(context, attribute_name)
                    if candidate_files is not None:
                        files = candidate_files
                        break

    if repo_root is None:
        for value in list(args) + list(kwargs.values()):
            if hasattr(value, "root_path"):
                repo_root = getattr(value, "root_path")
                break

    if files is None:
        for value in list(args) + list(kwargs.values()):
            if isinstance(value, (list, tuple)):
                files = value
                break

    if repo_root is None or files is None:
        return output

    sections = []
    import_graph = None

    try:
        import_graph = _build_import_graph_for_export(repo_root, files)
        sections.append(_format_import_graph_section(import_graph))
    except Exception:
        import_graph = None

    try:
        call_graph = _build_call_graph_for_export(
            repo_root,
            files,
            import_graph=import_graph,
        )
        sections.append(_format_call_graph_section(call_graph))
    except Exception:
        pass

    if not sections:
        return output

    separator = "\n\n" if output and not output.endswith("\n\n") else ""
    return f"{output}{separator}{chr(10).join(chr(10) + section if index else section for index, section in enumerate(sections))}\n"


def render_full_export_from_model(export: "RepositoryExport") -> str:
    """Render full Markdown from a RepositoryExport model.

    This bridge is intentionally model-only. It does not scan files, inspect Git,
    or run analyzers. Legacy full-export functions stay unchanged while callers
    can opt into the model-rendered Markdown path explicitly.
    """

    from repodossier.renderers import render_full_markdown

    return render_full_markdown(export)


def write_full_export_from_model(export, output_path) -> None:
    """Write full Markdown rendered from a RepositoryExport model."""

    from pathlib import Path

    Path(output_path).write_text(
        render_full_export_from_model(export),
        encoding="utf-8",
    )

