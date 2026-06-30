"""AI-focused export generation for RepoDossier.

The AI export is intentionally compact. It provides stable, high-level
sections for language models without embedding complete source dumps.
"""

from __future__ import annotations
from repodossier.secrets import SecretFinding, mask_secrets_in_text
from repodossier.dependencies import append_dependencies_ai_section

from dataclasses import dataclass, replace
from pathlib import Path

from repodossier.gitignore import ensure_repodossier_gitignore_entries
from repodossier.schema import analyze_database_schemas

from .full import FullExportContext, build_full_export_context
from repodossier.config import ai_config_summary_section, apply_config_to_file_infos, format_limit_notice, get_active_config, is_file_size_allowed


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


AI_CALL_GRAPH_MAX_INTERNAL_EDGES = 120
AI_CALL_GRAPH_MAX_EXTERNAL_EDGES = 30
AI_CALL_GRAPH_MAX_AMBIGUOUS_EDGES = 30
AI_CALL_GRAPH_MAX_UNRESOLVED_EDGES = 30


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
    """Create an AI export context from an already-built full export context."""

    filtered_context = _filter_ai_export_input_context(full_context)
    limited_context = _apply_ai_export_file_content_limits(filtered_context)
    return AIExportContext(full_context=limited_context)


def _filter_ai_export_input_context(full_context: FullExportContext) -> FullExportContext:
    """Exclude generated RepoDossier export files from AI-export analysis input."""

    filtered_scanned_files = tuple(
        file_info
        for file_info in full_context.scanned_files
        if not _is_generated_export_file_path(file_info.relative_path)
    )

    if filtered_scanned_files == full_context.scanned_files:
        return full_context

    return replace(full_context, scanned_files=filtered_scanned_files)



def _apply_ai_export_file_content_limits(full_context: FullExportContext) -> FullExportContext:
    """Strip large file contents from AI-only analysis inputs when configured."""

    config = get_active_config()
    limited_scanned_files = tuple(
        _strip_ai_file_content_for_size_limit(file_info, config)
        for file_info in full_context.scanned_files
    )

    if limited_scanned_files == full_context.scanned_files:
        return full_context

    return replace(full_context, scanned_files=limited_scanned_files)


def _strip_ai_file_content_for_size_limit(file_info: object, config: object) -> object:
    """Return file info with content removed when max_file_bytes excludes it."""

    size_bytes = getattr(file_info, "size_bytes", None)
    if size_bytes is None:
        return file_info

    if is_file_size_allowed(size_bytes, config):
        return file_info

    content = getattr(file_info, "content", None)
    if content in (None, ""):
        return file_info

    return replace(file_info, content="")

def _is_generated_export_file_path(relative_path: object) -> bool:
    """Return True when a repository-root path is a generated RepoDossier export."""

    path = Path(relative_path)
    return path.as_posix().lower() in GENERATED_EXPORT_FILENAMES

def build_ai_export_context(repository_root: Path | str) -> AIExportContext:
    """Build the AI export context for a Git repository."""

    return create_ai_export_context(build_full_export_context(repository_root))



def _insert_ai_config_summary_after_heading(rendered: str) -> str:
    """Insert the RepoDossier config summary without replacing the AI export title."""

    summary = ai_config_summary_section(get_active_config()).rstrip()
    if not summary:
        return rendered

    heading = "# AI CONTEXT\n"
    if rendered.startswith(heading):
        remainder = rendered[len(heading):].lstrip("\n")
        return f"{heading}\n{summary}\n\n{remainder}"

    return f"{summary}\n\n{rendered}"

def _render_ai_export_unmasked(context: AIExportContext) -> str:
    """Render the compact AI export text."""

    sections = [
        AI_EXPORT_DOCUMENT_HEADING,
        _render_project_section(context),
        _render_architecture_summary_section(context),
        _render_important_files_section(context),
        _render_symbol_index_section(context),
        _render_import_graph_section(context),
        _render_call_graph_section(context),
        _render_notes_section(),
    ]

    rendered = "\n\n".join(section.rstrip() for section in sections).rstrip() + "\n"
    return _insert_ai_config_summary_after_heading(rendered)





def _format_ai_secret_detection_section(findings: list[SecretFinding]) -> str:
    """Format a compact secret detection note without leaking values."""

    if not findings:
        return ""

    counts_by_type: dict[str, int] = {}
    for finding in findings:
        counts_by_type[finding.secret_type] = counts_by_type.get(finding.secret_type, 0) + 1

    lines = [
        "# Secret Detection",
        "",
        "Potential secrets were masked before export.",
        f"Potential secrets masked: {len(findings)}",
    ]

    lines.extend(["", "Findings by type:"])
    for secret_type in sorted(counts_by_type):
        lines.append(f"- {secret_type}: {counts_by_type[secret_type]}")

    return "\n".join(lines)


def _append_ai_secret_detection_section(text: str, section: str) -> str:
    """Append the secret detection note only when findings exist."""

    if not section:
        return text

    return f"{text.rstrip()}\n\n{section}\n"


def render_ai_export(*args: object, **kwargs: object) -> str:
    """Render export content with potential secrets masked."""

    rendered = _render_ai_export_unmasked(*args, **kwargs)
    masked_text, findings = mask_secrets_in_text(rendered, "ai.txt")
    secret_section = _format_ai_secret_detection_section(findings)
    return _append_ai_secret_detection_section(masked_text, secret_section)
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
    ensure_repodossier_gitignore_entries(resolved_repository_root)
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
    """Detect known RepoDossier core areas from existing module filenames."""

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
    """Return important files from the shared Milestone 12 ranking logic."""

    ranked_files = _rank_important_files_with_shared_ranker(
        context,
        limit=limit,
    )

    if ranked_files is not None:
        return ranked_files

    return _legacy_rank_important_files(context, limit=limit)


def _rank_important_files_with_shared_ranker(
    context: AIExportContext,
    *,
    limit: int,
) -> tuple[tuple[str, str, int], ...] | None:
    """Rank important files with the central repodossier.ranking module.

    Returning None means the shared ranker could not be used and the older AI
    export fallback should preserve existing output behavior.
    """

    try:
        from repodossier.ranking import rank_important_files as shared_rank_important_files
    except Exception:
        return None

    symbols, import_graph, call_graph = _build_ai_important_file_ranking_inputs(
        context,
    )

    try:
        ranked_scores = shared_rank_important_files(
            context.full_context.sorted_files,
            limit=limit,
            symbols=symbols,
            import_graph=import_graph,
            call_graph=call_graph,
        )
    except Exception:
        return None

    return tuple(
        (
            ranked_file.path,
            _format_ai_important_file_rank_reason(ranked_file),
            ranked_file.score,
        )
        for ranked_file in ranked_scores
    )


def _build_ai_important_file_ranking_inputs(
    context: AIExportContext,
) -> tuple[object | None, object | None, object | None]:
    """Build optional analysis inputs for AI important-file ranking.

    Each input is best-effort. A failed symbol, import, or call analysis must
    not break ai.txt rendering.
    """

    source_paths = _symbol_index_source_paths(context)
    symbols = None
    import_graph = None
    call_graph = None

    if source_paths:
        try:
            from repodossier.symbols import build_symbol_index

            symbols = build_symbol_index(
                source_paths,
                base_path=context.repository_root,
            )
        except Exception:
            symbols = None

        try:
            from repodossier.import_graph import build_import_graph

            import_graph = build_import_graph(
                source_paths,
                repo_root=context.repository_root,
            )
        except Exception:
            import_graph = None

    call_graph_source_entries = _call_graph_source_entries(context)
    if call_graph_source_entries:
        try:
            call_graph = _build_ai_call_graph(
                context,
                call_graph_source_entries,
            )
        except Exception:
            call_graph = None

    return symbols, import_graph, call_graph


def _format_ai_important_file_rank_reason(ranked_file: object) -> str:
    """Return a stable, compact reason string for one ranked file."""

    reasons = tuple(getattr(ranked_file, "reasons", ()) or ())
    if reasons:
        return "; ".join(str(reason) for reason in reasons)

    return "Important file ranking signal"


def _legacy_rank_important_files(
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
    }:
        return False

    if getattr(file_info, "is_binary", False) is True:
        return False

    if getattr(file_info, "is_text", True) is False:
        return False

    if getattr(file_info, "error", None) is not None:
        return False

    return True


def _important_file_order_priority(lower_path: str, filename: str) -> int:
    """Return a coarse priority boost for AI-facing important-file ordering."""

    if filename in {"pyproject.toml", "setup.py", "requirements.txt", "requirements-dev.txt"}:
        return 1000

    if filename in {"readme.md", "readme.txt"}:
        return 950

    if "architecture" in filename:
        return 940

    if "spec" in filename:
        return 930

    if "tasks" in filename or "roadmap" in filename:
        return 850

    if filename == "cli.py" or lower_path.endswith("/cli.py"):
        return 800

    if filename == "__main__.py":
        return 780

    if lower_path.endswith("exporters/full.py") or lower_path.endswith("exporters/ai.py"):
        return 720

    if lower_path.endswith(("scanner.py", "git.py", "symbols.py", "import_graph.py", "call_graph.py")):
        return 700

    if lower_path.startswith("tests/") and filename.startswith("test_"):
        return 100

    if "milestone" in filename:
        return 90

    return 0


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

    base_priority = _important_file_order_priority(lower_path, filename)
    if base_priority:
        score += base_priority

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

def _render_symbol_index_section(context: AIExportContext) -> str:
    """Render Python symbols from the existing Symbol Index implementation."""

    source_paths = _symbol_index_source_paths(context)

    lines = [
        AI_EXPORT_SECTION_HEADINGS["symbol_index"],
        "",
    ]

    if not source_paths:
        lines.append("No Python source files available for symbol analysis.")
        return "\n".join(lines)

    try:
        from repodossier.symbols import build_symbol_index

        symbol_indexes = build_symbol_index(
            source_paths,
            base_path=context.repository_root,
        )
    except Exception as exc:
        lines.append(f"Could not build symbol index: {type(exc).__name__}: {exc}")
        return "\n".join(lines)

    symbol_blocks = _format_ai_symbol_index_blocks(symbol_indexes)
    if symbol_blocks:
        lines.extend(symbol_blocks)
    else:
        lines.append("No Python symbols found.")

    error_lines = _format_ai_symbol_index_errors(symbol_indexes)
    if error_lines:
        lines.extend(["", "Analysis errors:"])
        lines.extend(error_lines)

    return "\n".join(lines)



def _ai_symbol_source_path_is_allowed(file_info: object, config: object) -> bool:
    """Return whether a file may be used as AI symbol analysis input."""

    size_bytes = getattr(file_info, "size_bytes", None)
    if size_bytes is not None and not is_file_size_allowed(size_bytes, config):
        return False

    max_line_count = getattr(getattr(config, "limits", None), "max_line_count", None)
    line_count = getattr(file_info, "line_count", None)
    if max_line_count is not None and line_count is not None and line_count > max_line_count:
        return False

    return True

def _symbol_index_source_paths(context: AIExportContext) -> tuple[Path, ...]:
    """Return Python source paths from scanned export data."""

    source_paths: list[Path] = []
    config = get_active_config()

    for file_info in context.full_context.exported_text_files:
        if not _ai_symbol_source_path_is_allowed(file_info, config):
            continue

        relative_path = getattr(file_info, "relative_path", None)
        if relative_path is None:
            continue

        relative_path_obj = Path(relative_path)
        if relative_path_obj.suffix.lower() != ".py":
            continue

        if getattr(file_info, "is_binary", False) is True:
            continue

        if getattr(file_info, "error", None) is not None:
            continue

        absolute_path = getattr(file_info, "absolute_path", None)
        source_path = (
            Path(absolute_path)
            if absolute_path is not None
            else context.repository_root / relative_path_obj
        )
        source_paths.append(source_path)

    return tuple(
        sorted(
            source_paths,
            key=lambda path: _repository_relative_display_path(path, context.repository_root),
        )
    )


def _format_ai_symbol_index_blocks(symbol_indexes: object) -> list[str]:
    """Format symbol index entries grouped by file."""

    lines: list[str] = []
    files_with_symbols = 0

    for file_index in _sorted_symbol_file_indexes(symbol_indexes):
        symbols = _sorted_symbols_for_ai_export(getattr(file_index, "symbols", ()))
        if not symbols:
            continue

        if files_with_symbols > 0:
            lines.append("")

        lines.append(f"### {_symbol_file_display_path(file_index)}")

        visible_symbols = symbols[:50]
        for symbol in visible_symbols:
            lines.append(_format_ai_symbol_line(symbol))

        remaining_count = len(symbols) - len(visible_symbols)
        if remaining_count > 0:
            lines.append(f"- ... {remaining_count} more symbols")

        files_with_symbols += 1

        if files_with_symbols >= 40:
            remaining_files = _count_remaining_symbol_files(
                symbol_indexes,
                skip_files=files_with_symbols,
            )
            if remaining_files > 0:
                lines.extend(["", f"- ... {remaining_files} more files with symbols"])
            break

    return lines


def _sorted_symbol_file_indexes(symbol_indexes: object) -> tuple[object, ...]:
    """Return symbol file indexes in deterministic order."""

    return tuple(
        sorted(
            symbol_indexes or (),
            key=lambda file_index: _symbol_file_display_path(file_index),
        )
    )


def _symbol_file_display_path(file_index: object) -> str:
    """Return a stable display path for one symbol file index."""

    return Path(str(getattr(file_index, "file_path", ""))).as_posix()


def _sorted_symbols_for_ai_export(symbols: object) -> tuple[object, ...]:
    """Return symbols in deterministic source order."""

    kind_order = {
        "class": 0,
        "method": 1,
        "function": 2,
    }

    return tuple(
        sorted(
            symbols or (),
            key=lambda symbol: (
                getattr(symbol, "line_start", 0) or 0,
                kind_order.get(getattr(symbol, "kind", ""), 99),
                getattr(symbol, "parent", "") or "",
                getattr(symbol, "name", "") or "",
            ),
        )
    )


def _format_ai_symbol_line(symbol: object) -> str:
    """Format one symbol line for ai.txt."""

    kind = getattr(symbol, "kind", "symbol") or "symbol"
    name = getattr(symbol, "name", "unknown") or "unknown"
    parent = getattr(symbol, "parent", None)
    line_start = getattr(symbol, "line_start", None)

    if kind == "method" and parent:
        display_name = f"{parent}.{name}"
    else:
        display_name = name

    if line_start is None:
        return f"- {kind} {display_name}"

    return f"- {kind} {display_name}:{line_start}"


def _format_ai_symbol_index_errors(symbol_indexes: object) -> list[str]:
    """Format non-fatal symbol analysis errors."""

    lines: list[str] = []

    for file_index in _sorted_symbol_file_indexes(symbol_indexes):
        errors = getattr(file_index, "errors", ()) or ()
        if not errors:
            continue

        display_path = _symbol_file_display_path(file_index)
        for error in errors[:3]:
            lines.append(f"- {display_path}: {error}")

        remaining_count = len(errors) - min(len(errors), 3)
        if remaining_count > 0:
            lines.append(f"- {display_path}: ... {remaining_count} more errors")

    return lines


def _count_remaining_symbol_files(
    symbol_indexes: object,
    *,
    skip_files: int,
) -> int:
    """Count symbol-containing files after the visible file limit."""

    files_with_symbols = [
        file_index
        for file_index in _sorted_symbol_file_indexes(symbol_indexes)
        if getattr(file_index, "symbols", ())
    ]
    return max(0, len(files_with_symbols) - skip_files)


def _repository_relative_display_path(path: Path, repository_root: Path) -> str:
    """Return a stable repository-relative display path when possible."""

    try:
        return path.resolve(strict=False).relative_to(
            repository_root.resolve(strict=False)
        ).as_posix()
    except ValueError:
        return path.as_posix()

def _render_import_graph_section(context: AIExportContext) -> str:
    """Render a compact Import Graph section using the Milestone 6 graph builder."""

    source_paths = _import_graph_source_paths(context)

    lines = [
        AI_EXPORT_SECTION_HEADINGS["import_graph"],
        "",
    ]

    if not source_paths:
        lines.append("No Python source files available for import graph analysis.")
        return "\n".join(lines)

    try:
        from repodossier.import_graph import (
            build_import_graph,
            calculate_import_graph_metrics,
        )

        import_graph = build_import_graph(
            source_paths,
            repo_root=context.repository_root,
        )
        metrics = calculate_import_graph_metrics(import_graph)
    except Exception as exc:
        lines.append(f"Could not build import graph: {type(exc).__name__}: {exc}")
        return "\n".join(lines)

    lines.extend(
        [
            "Summary:",
            f"- Local modules: {metrics.module_count}",
            f"- Local dependencies: {metrics.local_dependency_count}",
            f"- External imports: {metrics.external_import_count}",
            f"- Unresolved imports: {metrics.unresolved_import_count}",
            f"- Analysis errors: {metrics.error_count}",
            "",
            "Local imports by source file:",
        ]
    )

    local_blocks = _format_ai_import_graph_local_blocks(import_graph, context)
    if local_blocks:
        lines.extend(local_blocks)
    else:
        lines.append("- none")

    external_lines = _format_ai_import_graph_external_lines(import_graph)
    lines.extend(["", "External imports:"])
    if external_lines:
        lines.extend(external_lines)
    else:
        lines.append("- none")

    unresolved_lines = _format_ai_import_graph_unresolved_lines(import_graph)
    lines.extend(["", "Unresolved imports:"])
    if unresolved_lines:
        lines.extend(unresolved_lines)
    else:
        lines.append("- none")

    error_lines = _format_ai_import_graph_error_lines(import_graph, context)
    if error_lines:
        lines.extend(["", "Analysis errors:"])
        lines.extend(error_lines)

    return "\n".join(lines)


def _import_graph_source_paths(context: AIExportContext) -> tuple[Path, ...]:
    """Return Python source paths for import graph analysis."""

    return _symbol_index_source_paths(context)


def _format_ai_import_graph_local_blocks(
    import_graph: object,
    context: AIExportContext,
) -> list[str]:
    """Format local import graph edges grouped by source file."""

    edges_by_source: dict[tuple[str, str], list[object]] = {}

    for edge in _sorted_ai_import_graph_edges(import_graph):
        source_path = _repository_relative_display_path(
            Path(getattr(edge, "source_path")),
            context.repository_root,
        )
        source_module = getattr(edge, "source_module", "")
        edges_by_source.setdefault((source_path, source_module), []).append(edge)

    lines: list[str] = []

    for index, ((source_path, source_module), edges) in enumerate(
        sorted(edges_by_source.items(), key=lambda item: item[0])
    ):
        if index > 0:
            lines.append("")

        lines.append(f"### {source_path}")
        if source_module:
            lines.append(f"Module: {source_module}")
        lines.append("imports:")

        visible_edges = edges[:50]
        for edge in visible_edges:
            target_module = getattr(edge, "target_module", "")
            imported_name = getattr(edge, "imported_name", None)
            line_number = getattr(edge, "line_number", 0) or "unknown"

            if imported_name:
                lines.append(f"- {target_module} ({imported_name}, line {line_number})")
            else:
                lines.append(f"- {target_module} (line {line_number})")

        remaining_count = len(edges) - len(visible_edges)
        if remaining_count > 0:
            lines.append(f"- ... {remaining_count} more local imports")

    return lines


def _sorted_ai_import_graph_edges(import_graph: object) -> tuple[object, ...]:
    """Return local import graph edges in deterministic order."""

    return tuple(
        sorted(
            getattr(import_graph, "edges", ()) or (),
            key=lambda edge: (
                getattr(edge, "source_module", ""),
                getattr(edge, "target_module", ""),
                getattr(edge, "line_number", 0) or 0,
                getattr(edge, "import_type", ""),
                getattr(edge, "imported_name", "") or "",
                Path(getattr(edge, "source_path")).as_posix(),
                Path(getattr(edge, "target_path")).as_posix(),
            ),
        )
    )


def _format_ai_import_graph_external_lines(import_graph: object) -> list[str]:
    """Format external imports compactly and deterministically."""

    grouped: dict[str, set[str]] = {}

    for reference in getattr(import_graph, "external_imports", ()) or ():
        source_module = getattr(reference, "source_module", "")
        imported_module = getattr(reference, "imported_module", None)
        imported_name = getattr(reference, "imported_name", None)

        if not source_module or not imported_module:
            continue

        display = imported_module
        if imported_name and imported_name != "*":
            display = f"{display}.{imported_name}"

        grouped.setdefault(source_module, set()).add(display)

    lines: list[str] = []
    for source_module, imported_modules in sorted(grouped.items()):
        imports = ", ".join(sorted(imported_modules)[:20])
        extra_count = len(imported_modules) - min(len(imported_modules), 20)

        if extra_count > 0:
            imports = f"{imports}, ... {extra_count} more"

        lines.append(f"- {source_module}: {imports}")

    return lines[:100]


def _format_ai_import_graph_unresolved_lines(import_graph: object) -> list[str]:
    """Format unresolved imports compactly and deterministically."""

    references = tuple(
        sorted(
            getattr(import_graph, "unresolved_imports", ()) or (),
            key=lambda reference: (
                getattr(reference, "source_module", ""),
                getattr(reference, "imported_module", "") or "",
                getattr(reference, "imported_name", "") or "",
                getattr(reference, "line_number", 0) or 0,
                getattr(reference, "level", 0) or 0,
            ),
        )
    )

    lines: list[str] = []

    for reference in references[:100]:
        source_module = getattr(reference, "source_module", "")
        imported_module = getattr(reference, "imported_module", None) or "."
        imported_name = getattr(reference, "imported_name", None)
        line_number = getattr(reference, "line_number", 0) or "unknown"

        imported = imported_module
        if imported_name and imported_name != "*":
            imported = f"{imported}.{imported_name}"

        lines.append(f"- {source_module}: {imported} (line {line_number})")

    remaining_count = len(references) - len(lines)
    if remaining_count > 0:
        lines.append(f"- ... {remaining_count} more unresolved imports")

    return lines


def _format_ai_import_graph_error_lines(
    import_graph: object,
    context: AIExportContext,
) -> list[str]:
    """Format import graph analysis errors."""

    errors = tuple(
        sorted(
            getattr(import_graph, "errors", ()) or (),
            key=lambda error: (
                Path(getattr(error, "source_path")).as_posix(),
                getattr(error, "error_type", ""),
                getattr(error, "line_number", 0) or 0,
                getattr(error, "message", ""),
            ),
        )
    )

    lines: list[str] = []

    for error in errors[:50]:
        source_path = _repository_relative_display_path(
            Path(getattr(error, "source_path")),
            context.repository_root,
        )
        error_type = getattr(error, "error_type", "ImportAnalysisError")
        message = getattr(error, "message", "")
        line_number = getattr(error, "line_number", None)

        if line_number is None:
            lines.append(f"- {source_path}: {error_type}: {message}")
        else:
            lines.append(f"- {source_path}:{line_number}: {error_type}: {message}")

    remaining_count = len(errors) - len(lines)
    if remaining_count > 0:
        lines.append(f"- ... {remaining_count} more import analysis errors")

    return lines

def _render_call_graph_section(context: AIExportContext) -> str:
    """Render a compact Call Graph section using the Milestone 7 graph builder."""

    source_entries = _call_graph_source_entries(context)

    lines = [
        AI_EXPORT_SECTION_HEADINGS["call_graph"],
        "",
    ]

    if not source_entries:
        lines.append("No Python source files available for call graph analysis.")
        return "\n".join(lines)

    try:
        call_graph = _build_ai_call_graph(context, source_entries)
    except Exception as exc:
        lines.append(f"Could not build call graph: {type(exc).__name__}: {exc}")
        return "\n".join(lines)

    edges = tuple(call_graph.sorted_edges())
    if not edges:
        lines.append("No call graph edges found.")
        return "\n".join(lines)

    (
        internal_edges,
        external_edges,
        ambiguous_edges,
        unresolved_edges,
        other_edges,
    ) = _split_ai_call_graph_edges(edges)

    lines.extend(
        [
            "Summary:",
            f"- Call edges: {len(edges)}",
            f"- Local/internal calls: {len(internal_edges)}",
            f"- External calls: {len(external_edges)}",
            f"- Ambiguous calls: {len(ambiguous_edges)}",
            f"- Unresolved calls: {len(unresolved_edges)}",
            "",
            "Internal calls by caller:",
        ]
    )

    _append_ai_grouped_call_graph_edges(
        lines,
        internal_edges,
        max_edges=AI_CALL_GRAPH_MAX_INTERNAL_EDGES,
    )

    lines.extend(["", "External calls:"])
    _append_ai_flat_call_graph_edges(
        lines,
        external_edges,
        max_edges=AI_CALL_GRAPH_MAX_EXTERNAL_EDGES,
    )

    lines.extend(["", "Ambiguous calls:"])
    _append_ai_flat_call_graph_edges(
        lines,
        ambiguous_edges,
        max_edges=AI_CALL_GRAPH_MAX_AMBIGUOUS_EDGES,
    )

    lines.extend(["", "Unresolved calls:"])
    _append_ai_flat_call_graph_edges(
        lines,
        unresolved_edges,
        max_edges=AI_CALL_GRAPH_MAX_UNRESOLVED_EDGES,
    )

    if other_edges:
        lines.extend(["", "Other calls:"])
        _append_ai_flat_call_graph_edges(
            lines,
            other_edges,
            max_edges=AI_CALL_GRAPH_MAX_UNRESOLVED_EDGES,
        )

    return "\n".join(lines)


def _call_graph_source_entries(
    context: AIExportContext,
) -> tuple[tuple[Path, str | None], ...]:
    """Return Python source paths and scanner-provided source text."""

    entries: list[tuple[Path, str | None]] = []

    for file_info in context.full_context.exported_text_files:
        relative_path = getattr(file_info, "relative_path", None)
        if relative_path is None:
            continue

        relative_path_obj = Path(relative_path)
        if relative_path_obj.suffix.lower() != ".py":
            continue

        if getattr(file_info, "is_binary", False) is True:
            continue

        if getattr(file_info, "error", None) is not None:
            continue

        absolute_path = getattr(file_info, "absolute_path", None)
        source_path = (
            Path(absolute_path)
            if absolute_path is not None
            else context.repository_root / relative_path_obj
        )

        content = getattr(file_info, "content", None)
        entries.append((source_path, content if isinstance(content, str) else None))

    return tuple(
        sorted(
            entries,
            key=lambda item: _repository_relative_display_path(
                item[0],
                context.repository_root,
            ),
        )
    )


def _build_ai_call_graph(
    context: AIExportContext,
    source_entries: tuple[tuple[Path, str | None], ...],
) -> object:
    """Build a repository call graph for the AI export."""

    from repodossier.call_graph import CallGraph, parse_calls_from_source
    from repodossier.import_graph import build_import_graph, module_name_from_python_path
    from repodossier.symbols import build_symbol_index

    source_paths = tuple(source_path for source_path, _content in source_entries)
    symbol_index = build_symbol_index(source_paths, base_path=context.repository_root)
    import_graph = build_import_graph(source_paths, repo_root=context.repository_root)
    call_graph = CallGraph()

    for source_path, source_content in source_entries:
        module_name = module_name_from_python_path(
            source_path,
            repo_root=context.repository_root,
        )
        if module_name is None:
            continue

        try:
            source = (
                source_content
                if source_content is not None
                else source_path.read_text(encoding="utf-8")
            )
            file_graph = parse_calls_from_source(
                source,
                source_path=_repository_relative_display_path(
                    source_path,
                    context.repository_root,
                ),
                module_name=module_name,
                symbol_index=symbol_index,
                import_graph=import_graph,
            )
        except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
            continue

        for edge in file_graph.sorted_edges():
            call_graph.add_edge(edge)

    return call_graph


def _split_ai_call_graph_edges(
    edges: tuple[object, ...],
) -> tuple[
    tuple[object, ...],
    tuple[object, ...],
    tuple[object, ...],
    tuple[object, ...],
    tuple[object, ...],
]:
    """Split call graph edges into display groups."""

    internal_edges = []
    external_edges = []
    ambiguous_edges = []
    unresolved_edges = []
    other_edges = []

    for edge in edges:
        confidence = getattr(edge, "confidence", "")
        if confidence in {"local", "local_method", "imported_local"}:
            internal_edges.append(edge)
        elif confidence == "external":
            external_edges.append(edge)
        elif confidence == "ambiguous":
            ambiguous_edges.append(edge)
        elif confidence.startswith("unresolved"):
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


def _append_ai_grouped_call_graph_edges(
    lines: list[str],
    edges: tuple[object, ...],
    *,
    max_edges: int,
) -> None:
    """Append call graph edges grouped by caller."""

    if not edges:
        lines.append("- none")
        return

    visible_edges = edges[:max_edges]
    current_caller = None

    for edge in visible_edges:
        caller = getattr(edge, "caller_key", getattr(edge, "caller_name", "unknown"))
        caller_file = getattr(edge, "caller_file", "unknown")

        if caller != current_caller:
            if current_caller is not None:
                lines.append("")
            lines.append(f"- {caller} ({caller_file})")
            lines.append("  calls:")
            current_caller = caller

        lines.append(f"  - {_format_ai_call_graph_callee(edge)}")

    remaining_count = len(edges) - len(visible_edges)
    if remaining_count > 0:
        lines.append(f"- ... {remaining_count} more internal calls")


def _append_ai_flat_call_graph_edges(
    lines: list[str],
    edges: tuple[object, ...],
    *,
    max_edges: int,
) -> None:
    """Append compact non-internal call graph edges."""

    if not edges:
        lines.append("- none")
        return

    visible_edges = edges[:max_edges]
    for edge in visible_edges:
        caller = getattr(edge, "caller_key", getattr(edge, "caller_name", "unknown"))
        lines.append(f"- {caller} -> {_format_ai_call_graph_callee(edge)}")

    remaining_count = len(edges) - len(visible_edges)
    if remaining_count > 0:
        lines.append(f"- ... {remaining_count} more calls")


def _format_ai_call_graph_callee(edge: object) -> str:
    """Format the callee side of one call graph edge."""

    callee = getattr(edge, "callee_key", getattr(edge, "callee_name", "unknown"))
    line_number = getattr(edge, "line_number", None)
    call_type = getattr(edge, "call_type", "unknown")
    confidence = getattr(edge, "confidence", "unknown")

    if line_number is None:
        line_display = "unknown"
    else:
        line_display = str(line_number)

    return f"{callee} (line {line_display}, {call_type}, {confidence})"

def _render_notes_section() -> str:
    """Render compact AI export notes."""

    return "\n".join(
        [
            AI_EXPORT_SECTION_HEADINGS["notes"],
            "",
            "- This export intentionally excludes complete source dumps.",
            "- It is generated from Git-tracked scanner data plus static Python AST analysis.",
            "- Symbol, import, and call graph data are best-effort and deterministic.",
            "- Dynamic runtime behavior, reflection, monkeypatching, and unresolved external types may be incomplete.",
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


_REPODOSSIER_DEPENDENCY_AI_EXPORT_WRAPPER = True


def _repodossier_dependency_ai_path_from_value(value):
    from pathlib import Path as _Path

    if isinstance(value, (str, _Path)):
        try:
            return _Path(value)
        except TypeError:
            return None

    for attribute_name in (
        "repo_root",
        "repository_root",
        "project_root",
        "root",
        "base_path",
        "workdir",
        "cwd",
        "absolute_path",
        "relative_path",
        "path",
    ):
        attribute_value = getattr(value, attribute_name, None)
        if isinstance(attribute_value, (str, _Path)):
            try:
                return _Path(attribute_value)
            except TypeError:
                return None

    return None


def _repodossier_dependency_ai_files_from_value(value):
    if value is None or isinstance(value, (str, bytes, dict)):
        return None

    try:
        items = list(value)
    except TypeError:
        return None

    if not items:
        return None

    path_like_count = 0
    for item in items:
        if _repodossier_dependency_ai_path_from_value(item) is not None:
            path_like_count += 1

    if path_like_count == 0:
        return None

    return items


def _repodossier_dependency_ai_files_from_call(args, kwargs):
    for key in (
        "files",
        "scanned_files",
        "file_infos",
        "file_reports",
        "source_files",
        "project_files",
    ):
        if key in kwargs:
            files = _repodossier_dependency_ai_files_from_value(kwargs[key])
            if files is not None:
                return files

    for value in args:
        files = _repodossier_dependency_ai_files_from_value(value)
        if files is not None:
            selection = apply_config_to_file_infos(
                files,
                get_active_config(),
                repository_root=locals().get("repository_root") or locals().get("repo_root") or locals().get("root"),
            )
            return list(selection.files)
    return None


def _repodossier_dependency_ai_root_from_call(args, kwargs):
    for key in (
        "repo_root",
        "repository_root",
        "project_root",
        "root",
        "base_path",
        "workdir",
        "cwd",
    ):
        if key in kwargs:
            candidate = _repodossier_dependency_ai_path_from_value(kwargs[key])
            if candidate is not None and candidate.exists() and candidate.is_dir():
                return candidate

    for value in args:
        candidate = _repodossier_dependency_ai_path_from_value(value)
        if candidate is not None and candidate.exists() and candidate.is_dir():
            return candidate

    files = _repodossier_dependency_ai_files_from_call(args, kwargs)
    if files:
        from pathlib import Path as _Path
        import os as _os

        absolute_paths = []
        for file_item in files:
            path_value = _repodossier_dependency_ai_path_from_value(file_item)
            if path_value is not None and path_value.is_absolute():
                absolute_paths.append(path_value)

        if absolute_paths:
            common = _Path(_os.path.commonpath([path.as_posix() for path in absolute_paths]))
            if common.is_file():
                common = common.parent
            if common.exists():
                return common

    return None


def _repodossier_dependency_ai_root_and_files(args, kwargs):
    return (
        _repodossier_dependency_ai_root_from_call(args, kwargs),
        _repodossier_dependency_ai_files_from_call(args, kwargs),
    )


def _repodossier_wrap_ai_export_function(original_function):
    if getattr(original_function, "_repodossier_dependencies_wrapped", False):
        return original_function

    def wrapped_function(*args, **kwargs):
        result = original_function(*args, **kwargs)

        if not isinstance(result, str):
            return result

        repo_root, files = _repodossier_dependency_ai_root_and_files(args, kwargs)
        if repo_root is None:
            return result

        return append_dependencies_ai_section(result, repo_root, files=files)

    wrapped_function.__name__ = getattr(original_function, "__name__", "wrapped_function")
    wrapped_function.__doc__ = getattr(original_function, "__doc__", None)
    wrapped_function._repodossier_dependencies_wrapped = True
    return wrapped_function


for _repodossier_ai_export_name in ('generate_ai_export', 'render_ai_export', 'build_ai_export_context'):
    _repodossier_ai_export_function = globals().get(_repodossier_ai_export_name)
    if callable(_repodossier_ai_export_function):
        globals()[_repodossier_ai_export_name] = _repodossier_wrap_ai_export_function(
            _repodossier_ai_export_function
        )

del _repodossier_ai_export_name
del _repodossier_ai_export_function


AI_DATABASE_SCHEMA_MAX_FILES = 20
AI_DATABASE_SCHEMA_MAX_TABLES = 30
AI_DATABASE_SCHEMA_MAX_COLUMNS_PER_TABLE = 20
AI_DATABASE_SCHEMA_MAX_RELATIONSHIPS = 50
AI_DATABASE_SCHEMA_MAX_WARNINGS = 20


def _render_database_schema_section(context: AIExportContext) -> str:
    """Render a compact Database Schema section for ai.txt."""

    try:
        schema_report = analyze_database_schemas(
            context.repository_root,
            files=context.full_context.scanned_files,
        )
    except Exception as exc:
        return "\n".join(
            [
                "## Database Schema",
                "",
                "Could not analyze database schemas.",
                "",
                "Warnings:",
                f"- {type(exc).__name__}: {exc}",
            ]
        )

    lines = [
        "## Database Schema",
        "",
        "Summary:",
        f"- Database files: {len(schema_report.database_files)}",
        f"- SQL schema files: {len(schema_report.sql_schema_files)}",
        f"- Tables: {len(schema_report.tables)}",
        f"- Views: {len(schema_report.views)}",
        f"- Warnings: {len(schema_report.warnings)}",
    ]

    database_schema_files = tuple(schema_report.database_files) + tuple(schema_report.sql_schema_files)
    if database_schema_files:
        lines.extend(["", "Detected database/schema files:"])
        visible_files = database_schema_files[:AI_DATABASE_SCHEMA_MAX_FILES]
        lines.extend(f"- {path}" for path in visible_files)

        remaining_files = len(database_schema_files) - len(visible_files)
        if remaining_files > 0:
            lines.append(f"- ... {remaining_files} more")
    else:
        lines.extend(["", "No database schema files detected."])

    lines.extend(["", "Tables:"])
    if schema_report.tables:
        _append_ai_schema_tables(lines, schema_report.tables)
    else:
        lines.append("- none detected")

    relationships = _collect_ai_schema_relationships(schema_report.tables)
    lines.extend(["", "Relationships:"])
    if relationships:
        visible_relationships = relationships[:AI_DATABASE_SCHEMA_MAX_RELATIONSHIPS]
        lines.extend(f"- {relationship}" for relationship in visible_relationships)

        remaining_relationships = len(relationships) - len(visible_relationships)
        if remaining_relationships > 0:
            lines.append(f"- ... {remaining_relationships} more")
    else:
        lines.append("- none detected")

    if schema_report.warnings:
        lines.extend(["", "Warnings:"])
        visible_warnings = schema_report.warnings[:AI_DATABASE_SCHEMA_MAX_WARNINGS]
        lines.extend(f"- {warning}" for warning in visible_warnings)

        remaining_warnings = len(schema_report.warnings) - len(visible_warnings)
        if remaining_warnings > 0:
            lines.append(f"- ... {remaining_warnings} more")

    return "\n".join(lines).rstrip()


def _append_ai_schema_tables(lines: list[str], tables) -> None:
    """Append compact table summaries to the AI Database Schema section."""

    visible_tables = tuple(tables[:AI_DATABASE_SCHEMA_MAX_TABLES])

    for table in visible_tables:
        column_summary = _format_ai_schema_columns(table.columns)
        source_suffix = f" ({table.source_file})" if table.source_file else ""
        lines.append(f"- {table.name}{source_suffix}: {column_summary}")

    remaining_tables = len(tables) - len(visible_tables)
    if remaining_tables > 0:
        lines.append(f"- ... {remaining_tables} more")


def _format_ai_schema_columns(columns) -> str:
    """Return a compact AI-oriented column summary."""

    if not columns:
        return "no columns detected"

    visible_columns = tuple(columns[:AI_DATABASE_SCHEMA_MAX_COLUMNS_PER_TABLE])
    formatted_columns = [_format_ai_schema_column(column) for column in visible_columns]

    remaining_columns = len(columns) - len(visible_columns)
    if remaining_columns > 0:
        formatted_columns.append(f"... {remaining_columns} more")

    return ", ".join(formatted_columns)


def _format_ai_schema_column(column) -> str:
    """Format one column for the compact AI Database Schema section."""

    parts = [column.name]

    if column.data_type:
        parts.append(column.data_type)

    if column.is_primary_key:
        parts.append("PK")

    if column.nullable is False:
        parts.append("NOT NULL")

    return " ".join(parts)


def _collect_ai_schema_relationships(tables) -> tuple[str, ...]:
    """Collect compact foreign-key relationship lines."""

    relationships: list[str] = []

    for table in tables:
        for foreign_key in table.foreign_keys:
            relationships.append(
                f"{table.name}.{foreign_key.from_column} -> "
                f"{foreign_key.to_table}.{foreign_key.to_column}"
            )

    return tuple(sorted(dict.fromkeys(relationships)))


def _insert_database_schema_ai_section(rendered: str, context: AIExportContext) -> str:
    """Insert Database Schema into rendered ai.txt output."""

    if "## Database Schema" in rendered:
        return rendered

    database_schema_section = _render_database_schema_section(context)

    if "\n\n## Symbol Index" in rendered:
        return rendered.replace(
            "\n\n## Symbol Index",
            f"\n\n{database_schema_section}\n\n## Symbol Index",
            1,
        )

    if "\n\n## Import Graph" in rendered:
        return rendered.replace(
            "\n\n## Import Graph",
            f"\n\n{database_schema_section}\n\n## Import Graph",
            1,
        )

    if "\n\n## Notes" in rendered:
        return rendered.replace(
            "\n\n## Notes",
            f"\n\n{database_schema_section}\n\n## Notes",
            1,
        )

    return f"{rendered.rstrip()}\n\n{database_schema_section}\n"


def _repodossier_schema_wrap_ai_render_function(function):
    """Wrap AI rendering so Database Schema appears in ai.txt."""

    def wrapped_function(*args, **kwargs):
        rendered = function(*args, **kwargs)
        context = args[0] if args else kwargs.get("context")

        if isinstance(context, AIExportContext):
            return _insert_database_schema_ai_section(rendered, context)

        return rendered

    wrapped_function.__name__ = getattr(function, "__name__", "wrapped_function")
    wrapped_function.__doc__ = getattr(function, "__doc__", None)
    wrapped_function.__module__ = getattr(function, "__module__", __name__)
    return wrapped_function


_REPODOSSIER_DATABASE_SCHEMA_AI_EXPORT_WRAPPER = True
render_ai_export = _repodossier_schema_wrap_ai_render_function(render_ai_export)


_REPODOSSIER_AI_MAX_EXPORT_BYTES_WRAPPER = True


def _apply_ai_max_export_bytes_limit(rendered: str) -> str:
    """Apply the global max_export_bytes limit to a rendered AI export."""

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


_REPODOSSIER_ORIGINAL_RENDER_AI_EXPORT_FOR_MAX_EXPORT_BYTES = render_ai_export


def render_ai_export(context: AIExportContext) -> str:
    """Render ai.txt and apply the configured final export byte limit."""

    rendered = _REPODOSSIER_ORIGINAL_RENDER_AI_EXPORT_FOR_MAX_EXPORT_BYTES(context)
    return _apply_ai_max_export_bytes_limit(rendered)

