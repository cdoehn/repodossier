"""AI-focused export generation for RepoContext.

The AI export is intentionally compact. It provides stable, high-level
sections for language models without embedding complete source dumps.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repocontext.gitignore import ensure_repocontext_gitignore_entries

from .full import FullExportContext, build_full_export_context


AI_EXPORT_FILENAME = "ai.txt"
AI_EXPORT_DOCUMENT_HEADING = "# AI CONTEXT"

AI_EXPORT_SECTION_ORDER: tuple[str, ...] = (
    "project",
    "architecture_summary",
    "important_files",
    "symbol_index",
    "import_graph",
    "call_graph",
    "notes",
)

AI_EXPORT_SECTION_HEADINGS: dict[str, str] = {
    "project": "## Project",
    "architecture_summary": "## Architecture Summary",
    "important_files": "## Important Files",
    "symbol_index": "## Symbol Index",
    "import_graph": "## Import Graph",
    "call_graph": "## Call Graph",
    "notes": "## Notes",
}


IMPORTANT_FILES_LIMIT = 20
GENERATED_EXPORT_FILENAMES: frozenset[str] = frozenset(
    {
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
    }
)


@dataclass(frozen=True)
class AIExportContext:
    """Data required to render the compact AI export."""

    full_context: FullExportContext

    @property
    def repository_root(self) -> Path:
        """Return the repository root path."""

        return self.full_context.repository_root


def iter_ai_export_headings() -> tuple[str, ...]:
    """Return AI export headings in stable render order."""

    return (
        AI_EXPORT_DOCUMENT_HEADING,
        *(
            AI_EXPORT_SECTION_HEADINGS[section_name]
            for section_name in AI_EXPORT_SECTION_ORDER
        ),
    )


def create_ai_export_context(full_context: FullExportContext) -> AIExportContext:
    """Create an AI export context from an existing Full Export context."""

    return AIExportContext(full_context=full_context)


def build_ai_export_context(repository_root: Path | str) -> AIExportContext:
    """Build the AI export context for a Git repository."""

    return create_ai_export_context(build_full_export_context(repository_root))


def render_ai_export(context: AIExportContext) -> str:
    """Render the compact AI export text."""

    sections = [
        AI_EXPORT_DOCUMENT_HEADING,
        _render_project_section(context),
        _render_architecture_summary_section(context),
        _render_important_files_section(context),
        _render_symbol_index_section(),
        _render_import_graph_section(),
        _render_call_graph_section(),
        _render_notes_section(),
    ]

    return "\n\n".join(section.rstrip() for section in sections).rstrip() + "\n"


def write_ai_export(
    context: AIExportContext,
    output_path: Path | str | None = None,
) -> Path:
    """Write the rendered AI export atomically and return its path."""

    resolved_output_path = _resolve_ai_export_output_path(context, output_path)
    temporary_output_path = _temporary_ai_export_output_path(resolved_output_path)
    rendered_export = render_ai_export(context)

    try:
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_output_path.write_text(rendered_export, encoding="utf-8")
        temporary_output_path.replace(resolved_output_path)
    except OSError:
        _remove_temporary_output_file(temporary_output_path)
        raise

    return resolved_output_path


def generate_ai_export(repository_root: Path | str) -> Path:
    """Build, render, and write ai.txt for a repository."""

    resolved_repository_root = Path(repository_root).resolve()
    ensure_repocontext_gitignore_entries(resolved_repository_root)
    context = build_ai_export_context(resolved_repository_root)
    return write_ai_export(context)


def _resolve_ai_export_output_path(
    context: AIExportContext,
    output_path: Path | str | None,
) -> Path:
    """Resolve the final AI export output path."""

    if output_path is not None:
        return Path(output_path).resolve()

    return context.repository_root / AI_EXPORT_FILENAME


def _temporary_ai_export_output_path(output_path: Path) -> Path:
    """Return the temporary path used for atomic AI export writes."""

    return output_path.with_name(f".{output_path.name}.tmp")


def _remove_temporary_output_file(temporary_output_path: Path) -> None:
    """Best-effort cleanup for a failed temporary export write."""

    try:
        temporary_output_path.unlink(missing_ok=True)
    except OSError:
        pass


def _render_project_section(context: AIExportContext) -> str:
    """Render compact repository facts for the AI export."""

    full_context = context.full_context
    repository_info = full_context.repository_info
    repository_name = repository_info.name or "unknown"

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["project"],
            "",
            f"Repository: {repository_name}",
            f"Tracked files: {full_context.tracked_file_count}",
            f"Scanned files: {len(full_context.scanned_files)}",
            f"Exported text files: {len(full_context.exported_text_files)}",
            f"Skipped binary files: {len(full_context.skipped_binary_files)}",
            f"Errored files: {len(full_context.errored_files)}",
            f"Total lines: {full_context.total_line_count}",
            f"Estimated tokens: {full_context.total_estimated_tokens}",
        ]
    )


def _render_architecture_summary_section(context: AIExportContext) -> str:
    """Render a compact architecture summary derived from repository files."""

    paths = _scanned_path_strings(context)
    lines = [
        AI_EXPORT_SECTION_HEADINGS["architecture_summary"],
        "",
        f"Detected project type: {_detect_architecture_project_type(context, paths)}",
    ]

    entrypoints = _detect_architecture_entrypoints(context)
    lines.extend(["", "Main entry points:"])
    if entrypoints:
        lines.extend(f"- {entrypoint}" for entrypoint in entrypoints)
    else:
        lines.append("- none detected")

    top_level_directories = _detect_top_level_directories(paths)
    if top_level_directories:
        lines.extend(["", "Top-level directories:"])
        lines.extend(f"- {directory}" for directory in top_level_directories)

    package_roots = _detect_python_package_roots(paths)
    if package_roots:
        lines.extend(["", "Python package/module roots:"])
        lines.extend(f"- {package_root}" for package_root in package_roots)

    core_areas = _detect_core_areas(paths)
    if core_areas:
        lines.extend(["", "Core areas:"])
        lines.extend(f"- {core_area}" for core_area in core_areas)

    test_locations = _detect_test_locations(paths)
    if test_locations:
        lines.extend(["", "Tests:"])
        lines.extend(f"- {test_location}" for test_location in test_locations)

    documentation_files = _detect_documentation_files(paths)
    if documentation_files:
        lines.extend(["", "Documentation:"])
        lines.extend(f"- {documentation_file}" for documentation_file in documentation_files)

    if not paths:
        lines.extend(["", "No scanned files available."])

    return "\n".join(lines)


def _scanned_path_strings(context: AIExportContext) -> tuple[str, ...]:
    """Return scanned repository-relative paths in deterministic order."""

    return tuple(
        sorted(
            file_info.relative_path.as_posix()
            for file_info in context.full_context.sorted_files
        )
    )


def _lower_path_set(paths: tuple[str, ...]) -> set[str]:
    """Return lowercase path strings for case-insensitive detection."""

    return {path.lower() for path in paths}


def _detect_architecture_project_type(
    context: AIExportContext,
    paths: tuple[str, ...],
) -> str:
    """Infer a conservative project type from files that exist in the repo."""

    lower_paths = _lower_path_set(paths)
    has_python = any(path.endswith(".py") for path in lower_paths)
    has_pyproject = "pyproject.toml" in lower_paths
    has_setup_py = "setup.py" in lower_paths
    has_scripts = bool(_parse_project_scripts(_content_for_path(context, "pyproject.toml")))
    has_cli_file = any(
        path == "cli.py" or path.endswith("/cli.py") or path.endswith("/__main__.py")
        for path in lower_paths
    )

    if has_python and has_pyproject and (has_scripts or has_cli_file):
        return "Python CLI project"

    if has_python and (has_pyproject or has_setup_py):
        return "Python package"

    if has_python:
        return "Python project"

    if paths and all(
        path.endswith((".md", ".txt")) or "." not in Path(path).name
        for path in lower_paths
    ):
        return "Documentation-oriented repository"

    return "Git repository"


def _content_for_path(context: AIExportContext, relative_path: str) -> str | None:
    """Return scanned file content for a repository-relative path."""

    target_path = relative_path.lower()
    for file_info in context.full_context.exported_text_files:
        if file_info.relative_path.as_posix().lower() == target_path:
            return file_info.content
    return None


def _parse_project_scripts(pyproject_content: str | None) -> tuple[str, ...]:
    """Parse simple [project.scripts] entries from pyproject.toml text."""

    if not pyproject_content:
        return ()

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

        script_name, raw_target = line.split("=", 1)
        script_name = script_name.strip()
        target = raw_target.strip().strip('"').strip("'")

        if script_name and target:
            scripts.append(f"{script_name}: {target}")
        elif script_name:
            scripts.append(script_name)

    return tuple(sorted(dict.fromkeys(scripts)))


def _detect_architecture_entrypoints(context: AIExportContext) -> tuple[str, ...]:
    """Detect likely entrypoints from project scripts and source paths."""

    entrypoints: list[str] = []

    for script in _parse_project_scripts(_content_for_path(context, "pyproject.toml")):
        _append_unique(entrypoints, script)

    for path in _scanned_path_strings(context):
        lower_path = path.lower()
        if lower_path == "cli.py" or lower_path.endswith("/cli.py"):
            _append_unique(entrypoints, path)
        elif lower_path == "__main__.py" or lower_path.endswith("/__main__.py"):
            _append_unique(entrypoints, path)

    return tuple(entrypoints)


def _detect_top_level_directories(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Return top-level directories present in scanned paths."""

    directories = {
        Path(path).parts[0]
        for path in paths
        if len(Path(path).parts) > 1
    }
    return tuple(sorted(directories))


def _detect_python_package_roots(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Detect Python package roots from __init__.py files."""

    package_roots: list[str] = []

    for path in paths:
        path_obj = Path(path)
        if path_obj.name != "__init__.py":
            continue

        parent = path_obj.parent.as_posix()
        if parent and parent != ".":
            _append_unique(package_roots, parent)

    return tuple(package_roots)


def _detect_core_areas(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Detect known RepoContext core areas from existing module filenames."""

    area_rules: tuple[tuple[str, str], ...] = (
        ("git.py", "Git repository discovery"),
        ("scanner.py", "File scanning"),
        ("symbols.py", "Symbol extraction"),
        ("import_graph.py", "Import graph analysis"),
        ("call_graph.py", "Call graph analysis"),
        ("gitignore.py", ".gitignore management"),
        ("exporters/full.py", "Full export generation"),
        ("exporters/ai.py", "AI export generation"),
        ("cli.py", "Command-line interface"),
    )

    core_areas: list[str] = []
    lower_to_original = {path.lower(): path for path in paths}

    for suffix, label in area_rules:
        for lower_path, original_path in sorted(lower_to_original.items()):
            if lower_path.endswith(suffix):
                _append_unique(core_areas, f"{label}: {original_path}")
                break

    return tuple(core_areas)


def _detect_test_locations(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Detect test locations from scanned paths."""

    lower_paths = _lower_path_set(paths)
    locations: list[str] = []

    if any(path == "tests" or path.startswith("tests/") for path in lower_paths):
        locations.append("tests/")

    for path in paths:
        name = Path(path).name.lower()
        if name.startswith("test_") and name.endswith(".py"):
            _append_unique(locations, path)

    return tuple(locations[:10])


def _detect_documentation_files(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Detect documentation files without inventing project details."""

    documentation_files: list[str] = []
    documentation_names = (
        "readme",
        "architecture",
        "spec",
        "tasks",
        "changelog",
        "roadmap",
        "milestone",
    )

    for path in paths:
        lower_name = Path(path).name.lower()
        stem = Path(lower_name).stem

        if lower_name in {"license", "licence"}:
            _append_unique(documentation_files, path)
            continue

        if lower_name.endswith((".md", ".txt")) and any(
            marker in stem for marker in documentation_names
        ):
            _append_unique(documentation_files, path)

    return tuple(documentation_files[:12])


def _append_unique(items: list[str], value: str) -> None:
    """Append a value once while preserving list order."""

    if value not in items:
        items.append(value)

def _render_important_files_section(context: AIExportContext) -> str:
    """Render a compact, deterministic important-file ranking."""

    ranked_files = _rank_important_files(context, limit=IMPORTANT_FILES_LIMIT)

    lines = [
        AI_EXPORT_SECTION_HEADINGS["important_files"],
        "",
    ]

    if not ranked_files:
        lines.append("No important files detected.")
        return "\n".join(lines)

    for path, reason, _score in ranked_files:
        lines.append(f"- {path}")
        lines.append(f"  Reason: {reason}")

    return "\n".join(lines)


def _rank_important_files(
    context: AIExportContext,
    *,
    limit: int,
) -> tuple[tuple[str, str, int], ...]:
    """Return important files as path, reason, score tuples."""

    candidates: list[tuple[int, str, str]] = []

    for file_info in context.full_context.sorted_files:
        if not _is_ai_important_file_candidate(file_info):
            continue

        path = file_info.relative_path.as_posix()
        score, reasons = _score_important_file(context, file_info)
        if score <= 0:
            continue

        candidates.append((score, path, "; ".join(reasons)))

    candidates.sort(key=lambda item: (-item[0], item[1]))

    return tuple(
        (path, reason, score)
        for score, path, reason in candidates[:limit]
    )


def _is_ai_important_file_candidate(file_info: object) -> bool:
    """Return True when a file can appear in the Important Files section."""

    relative_path = getattr(file_info, "relative_path", None)
    if relative_path is None:
        return False

    path = Path(relative_path)
    filename = path.name.lower()
    path_string = path.as_posix().lower()

    if filename in GENERATED_EXPORT_FILENAMES:
        return False

    if path_string in {
        "project_bundle.txt",
        "bundle_project.sh",
    }:
        return False

    if getattr(file_info, "is_binary", False) is True:
        return False

    if getattr(file_info, "is_text", True) is False:
        return False

    if getattr(file_info, "error", None) is not None:
        return False

    return True


def _score_important_file(
    context: AIExportContext,
    file_info: object,
) -> tuple[int, tuple[str, ...]]:
    """Score one file and return human-readable reasons."""

    path = Path(getattr(file_info, "relative_path")).as_posix()
    lower_path = path.lower()
    filename = Path(lower_path).name
    content = getattr(file_info, "content", None) or ""

    score = 0
    reasons: list[str] = []

    if filename == "pyproject.toml":
        score += 100
        reasons.append("Python project configuration")

    if filename == "setup.py":
        score += 95
        reasons.append("Python packaging entry point")

    if filename in {"requirements.txt", "requirements-dev.txt"}:
        score += 90
        reasons.append("Python dependency list")

    if filename == "readme.md" or filename == "readme.txt":
        score += 85
        reasons.append("Primary project documentation")

    if "architecture" in filename:
        score += 80
        reasons.append("Architecture documentation")

    if "spec" in filename:
        score += 75
        reasons.append("Project specification")

    if "tasks" in filename or "roadmap" in filename or "milestone" in filename:
        score += 60
        reasons.append("Planning or roadmap documentation")

    if filename == "cli.py" or lower_path.endswith("/cli.py"):
        score += 80
        reasons.append("CLI entry point")

    if filename == "__main__.py":
        score += 70
        reasons.append("Python module execution entry point")

    if lower_path.endswith("exporters/full.py"):
        score += 75
        reasons.append("Full export pipeline implementation")

    if lower_path.endswith("exporters/ai.py"):
        score += 75
        reasons.append("AI export pipeline implementation")

    if lower_path.endswith("scanner.py"):
        score += 65
        reasons.append("Repository file scanning implementation")

    if lower_path.endswith("git.py"):
        score += 60
        reasons.append("Git repository discovery implementation")

    if lower_path.endswith("symbols.py"):
        score += 60
        reasons.append("Symbol extraction implementation")

    if lower_path.endswith("import_graph.py"):
        score += 60
        reasons.append("Import graph implementation")

    if lower_path.endswith("call_graph.py"):
        score += 60
        reasons.append("Call graph implementation")

    if lower_path.startswith("tests/") and filename.startswith("test_"):
        score += 35
        reasons.append("Automated test coverage")

    symbol_count = _count_python_symbol_like_lines(file_info)
    if symbol_count:
        score += min(symbol_count, 20)
        reasons.append(f"Contains {symbol_count} Python symbol-like definitions")

    incoming_import_count = _count_incoming_import_mentions(context, path)
    if incoming_import_count:
        score += min(incoming_import_count * 4, 40)
        reasons.append(f"Imported by {incoming_import_count} scanned file(s)")

    line_count = getattr(file_info, "line_count", None) or 0
    if line_count >= 300 and lower_path.endswith(".py"):
        score += 10
        reasons.append("Large Python implementation file")

    if not reasons:
        return 0, ()

    return score, tuple(reasons)


def _count_python_symbol_like_lines(file_info: object) -> int:
    """Count simple Python def/class lines without executing code."""

    language = (getattr(file_info, "language", None) or "").lower()
    relative_path = getattr(file_info, "relative_path", None)
    suffix = Path(relative_path).suffix.lower() if relative_path is not None else ""

    if language != "python" and suffix != ".py":
        return 0

    content = getattr(file_info, "content", None) or ""

    count = 0
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith(("def ", "async def ", "class ")):
            count += 1

    return count


def _count_incoming_import_mentions(context: AIExportContext, path: str) -> int:
    """Count scanned files that appear to import a local Python module path."""

    if not path.endswith(".py"):
        return 0

    module_name = _module_name_from_ai_export_path(path)
    if not module_name:
        return 0

    import_needle = f"import {module_name}"
    from_needle = f"from {module_name} import"
    short_module_name = module_name.rsplit(".", 1)[-1]
    short_from_needle = f"from .{short_module_name} import"

    count = 0
    for file_info in context.full_context.exported_text_files:
        candidate_path = file_info.relative_path.as_posix()
        if candidate_path == path:
            continue

        content = file_info.content or ""
        if (
            import_needle in content
            or from_needle in content
            or short_from_needle in content
        ):
            count += 1

    return count


def _module_name_from_ai_export_path(path: str) -> str | None:
    """Convert a Python path into a best-effort module name."""

    path_obj = Path(path)
    if path_obj.suffix != ".py":
        return None

    parts = list(path_obj.with_suffix("").parts)

    if parts and parts[0] == "src":
        parts = parts[1:]

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    if not parts:
        return None

    if not all(part.isidentifier() for part in parts):
        return None

    return ".".join(parts)

def _render_symbol_index_section() -> str:
    """Render the placeholder Symbol Index section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["symbol_index"],
            "",
            "Symbol index rendering is not implemented yet.",
        ]
    )


def _render_import_graph_section() -> str:
    """Render the placeholder Import Graph section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["import_graph"],
            "",
            "Import graph rendering is not implemented yet.",
        ]
    )


def _render_call_graph_section() -> str:
    """Render the placeholder Call Graph section."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["call_graph"],
            "",
            "Call graph rendering is not implemented yet.",
        ]
    )


def _render_notes_section() -> str:
    """Render compact AI export notes."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["notes"],
            "",
            "- This export intentionally excludes complete source dumps.",
            "- Detailed section content will be expanded in later Milestone 8 steps.",
        ]
    )


__all__ = [
    "AI_EXPORT_DOCUMENT_HEADING",
    "AI_EXPORT_FILENAME",
    "AI_EXPORT_SECTION_HEADINGS",
    "AI_EXPORT_SECTION_ORDER",
    "AIExportContext",
    "build_ai_export_context",
    "create_ai_export_context",
    "generate_ai_export",
    "iter_ai_export_headings",
    "render_ai_export",
    "write_ai_export",
]
