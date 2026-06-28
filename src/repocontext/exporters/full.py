"""Foundational structures and orchestration for the Full Export MVP."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from repocontext.git import RepositoryInfo, get_repository_info
from repocontext.gitignore import ensure_repocontext_gitignore_entries
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
        _render_file_summary(context),
        _render_repository_tree(context),
        _render_complete_source_export(context),
        _render_warnings(context),
    ]
    return "\n\n".join(section.rstrip() for section in sections).rstrip() + "\n"


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
    ensure_repocontext_gitignore_entries(resolved_repository_root)
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
        content = file_info.content or ""
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

    return "\n\n".join(parts)


def _choose_code_fence(content: str) -> str:
    """Choose a Markdown code fence that is longer than fences in the content."""
    backtick = chr(96)
    fence = backtick * 3

    while fence in content:
        fence += backtick

    return fence


def _code_fence_language(language: str | None) -> str:
    """Return a Markdown code fence language identifier."""
    if language is None:
        return "text"

    language_identifiers = {
        "bash": "bash",
        "dockerfile": "dockerfile",
        "ini": "ini",
        "json": "json",
        "makefile": "makefile",
        "markdown": "markdown",
        "python": "python",
        "text": "text",
        "toml": "toml",
        "yaml": "yaml",
    }

    return language_identifiers.get(language.lower(), "text")


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



def _format_import_graph_section(import_graph, *, max_edges=200, max_imports=100):
    """Render a compact Import Graph section for full.txt."""

    from repocontext.import_graph import calculate_import_graph_metrics

    metrics = calculate_import_graph_metrics(import_graph)
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
        for module_name in metrics.root_modules[:max_imports]:
            lines.append(f"- {module_name}")
        lines.append("")

    if metrics.leaf_modules:
        lines.append("Leaf modules:")
        for module_name in metrics.leaf_modules[:max_imports]:
            lines.append(f"- {module_name}")
        lines.append("")

    lines.append("Local dependencies:")
    if import_graph.edges:
        for edge in import_graph.edges[:max_edges]:
            lines.append(f"- {edge.source_module} -> {edge.target_module}")
        if len(import_graph.edges) > max_edges:
            lines.append(f"- ... {len(import_graph.edges) - max_edges} more")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("External imports:")
    external_names = sorted(
        {
            reference.imported_module
            for reference in import_graph.external_imports
            if reference.imported_module
        }
    )
    if external_names:
        for imported_module in external_names[:max_imports]:
            lines.append(f"- {imported_module}")
        if len(external_names) > max_imports:
            lines.append(f"- ... {len(external_names) - max_imports} more")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Unresolved imports:")
    if import_graph.unresolved_imports:
        for reference in import_graph.unresolved_imports[:max_imports]:
            imported = reference.imported_module or "."
            if reference.imported_name:
                imported = f"{imported}.{reference.imported_name}"
            lines.append(f"- {reference.source_module}: {imported}")
        if len(import_graph.unresolved_imports) > max_imports:
            lines.append(f"- ... {len(import_graph.unresolved_imports) - max_imports} more")
    else:
        lines.append("- none")
    lines.append("")

    if import_graph.errors:
        lines.append("Analysis errors:")
        for error in import_graph.errors[:max_imports]:
            lines.append(f"- {error.source_path}: {error.error_type}: {error.message}")
        if len(import_graph.errors) > max_imports:
            lines.append(f"- ... {len(import_graph.errors) - max_imports} more")
        lines.append("")

    return "\n".join(lines).rstrip()


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

    from repocontext.import_graph import build_import_graph

    source_paths = []
    for file_info in files:
        source_path = _import_graph_export_source_path(file_info, repo_root)
        if source_path is not None:
            source_paths.append(source_path)

    return build_import_graph(source_paths, repo_root=repo_root)


_ORIGINAL_RENDER_FULL_EXPORT_WITHOUT_IMPORT_GRAPH = render_full_export


def render_full_export(*args, **kwargs):
    """Render the full export and append the Import Graph section when possible."""

    output = _ORIGINAL_RENDER_FULL_EXPORT_WITHOUT_IMPORT_GRAPH(*args, **kwargs)

    if not isinstance(output, str):
        return output

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

    try:
        import_graph = _build_import_graph_for_export(repo_root, files)
        section = _format_import_graph_section(import_graph)
    except Exception:
        return output

    if "## Import Graph" in output:
        return output

    separator = "\n\n" if output and not output.endswith("\n\n") else ""
    return f"{output}{separator}{section}\n"

