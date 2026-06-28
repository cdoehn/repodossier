"""Important file ranking utilities for RepoContext.

The ranking module provides a reusable, deterministic foundation for deciding
which repository files are most useful for AI-oriented context exports.

The ranking is explainable: every score is split into signal categories and
each ranked file carries human-readable reasons.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import tomllib


GENERATED_EXPORT_FILENAMES: frozenset[str] = frozenset(
    {
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
    }
)

NON_PROJECT_EXPORT_PATHS: frozenset[str] = frozenset(
    {
        "project_bundle.txt",
        "bundle_project.sh",
    }
)

DOCUMENTATION_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".md",
        ".markdown",
        ".rst",
        ".txt",
    }
)

PYTHON_ENTRYPOINT_FILENAMES: dict[str, int] = {
    "__main__.py": 85,
    "main.py": 80,
    "cli.py": 75,
    "app.py": 70,
    "server.py": 70,
    "manage.py": 70,
    "wsgi.py": 65,
    "asgi.py": 65,
}

IMPORT_INCOMING_WEIGHT = 35
IMPORT_INCOMING_MAX_SCORE = 120
IMPORT_OUTGOING_WEIGHT = 8
IMPORT_OUTGOING_MAX_SCORE = 32

CALL_INCOMING_WEIGHT = 35
CALL_INCOMING_MAX_SCORE = 120
CALL_OUTGOING_WEIGHT = 6
CALL_OUTGOING_MAX_SCORE = 24


@dataclass(frozen=True, slots=True)
class ImportantFileSignals:
    """Score components used to rank one important file."""

    entrypoint_score: int = 0
    import_centrality_score: int = 0
    call_centrality_score: int = 0
    documentation_score: int = 0
    structural_score: int = 0

    @property
    def total(self) -> int:
        """Return the total score across all signal categories."""

        return (
            self.entrypoint_score
            + self.import_centrality_score
            + self.call_centrality_score
            + self.documentation_score
            + self.structural_score
        )


@dataclass(frozen=True, slots=True)
class ImportantFileScore:
    """Ranking result for one repository-relative file path."""

    path: str
    score: int
    reasons: tuple[str, ...]
    signals: ImportantFileSignals

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path).as_posix())
        object.__setattr__(self, "score", int(self.score))
        object.__setattr__(self, "reasons", tuple(self.reasons))


@dataclass(frozen=True, slots=True)
class _ImportCentrality:
    """Internal import centrality score details for one file."""

    score: int = 0
    incoming_count: int = 0
    outgoing_count: int = 0

    @property
    def reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []

        if self.incoming_count:
            noun = "file" if self.incoming_count == 1 else "files"
            reasons.append(f"Imported by {self.incoming_count} local {noun}")

        if self.outgoing_count:
            noun = "file" if self.outgoing_count == 1 else "files"
            reasons.append(f"Imports {self.outgoing_count} local {noun}")

        return tuple(reasons)


@dataclass(frozen=True, slots=True)
class _CallCentrality:
    """Internal call centrality score details for one file."""

    score: int = 0
    incoming_count: int = 0
    outgoing_count: int = 0

    @property
    def reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []

        if self.incoming_count:
            noun = "file" if self.incoming_count == 1 else "files"
            reasons.append(f"Called by {self.incoming_count} local {noun}")

        if self.outgoing_count:
            noun = "file" if self.outgoing_count == 1 else "files"
            reasons.append(f"Calls {self.outgoing_count} local {noun}")

        return tuple(reasons)


def rank_important_files(
    files: Iterable[object],
    *,
    limit: int | None = None,
    symbols: object | None = None,
    import_graph: object | None = None,
    call_graph: object | None = None,
    project_metadata: object | None = None,
) -> tuple[ImportantFileScore, ...]:
    """Rank important files with deterministic, explainable scores."""

    del project_metadata

    file_items = list(files)
    candidate_paths = _collect_candidate_paths(file_items)
    pyproject_entrypoint_paths = _detect_pyproject_entrypoint_paths(
        file_items,
        candidate_paths,
    )
    import_centrality_by_path = _calculate_import_centrality_by_path(
        import_graph,
        candidate_paths,
    )
    call_centrality_by_path = _calculate_call_centrality_by_path(
        call_graph,
        symbols,
        candidate_paths,
    )

    ranked: list[ImportantFileScore] = []

    for file_info in file_items:
        path = _relative_path_from_file(file_info)
        if path is None:
            continue

        if not _is_important_file_candidate(file_info, path):
            continue

        score = _score_path(
            file_info,
            path,
            pyproject_entrypoint_paths=pyproject_entrypoint_paths,
            import_centrality_by_path=import_centrality_by_path,
            call_centrality_by_path=call_centrality_by_path,
        )
        if score is None or score.score <= 0:
            continue

        ranked.append(score)

    ranked.sort(key=_important_file_sort_key)

    if limit is not None:
        return tuple(ranked[: max(0, limit)])

    return tuple(ranked)


def _collect_candidate_paths(files: Iterable[object]) -> frozenset[str]:
    """Return normalized candidate paths from FileInfo-like objects or paths."""

    paths: set[str] = set()
    for file_info in files:
        path = _relative_path_from_file(file_info)
        if path is None:
            continue
        paths.add(path.as_posix())
    return frozenset(paths)


def _detect_pyproject_entrypoint_paths(
    files: Iterable[object],
    candidate_paths: frozenset[str],
) -> frozenset[str]:
    """Return file paths referenced by pyproject console scripts."""

    entrypoint_paths: set[str] = set()

    for file_info in files:
        path = _relative_path_from_file(file_info)
        if path is None or path.name != "pyproject.toml":
            continue

        content = getattr(file_info, "content", None)
        if not content:
            continue

        for target in _parse_pyproject_script_targets(content):
            entrypoint_paths.update(
                _resolve_script_target_to_paths(target, candidate_paths)
            )

    return frozenset(entrypoint_paths)


def _parse_pyproject_script_targets(content: str) -> tuple[str, ...]:
    """Parse console script targets from pyproject.toml content."""

    try:
        pyproject = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return ()

    targets: list[str] = []

    project_scripts = pyproject.get("project", {}).get("scripts", {})
    if isinstance(project_scripts, dict):
        targets.extend(
            target
            for target in project_scripts.values()
            if isinstance(target, str)
        )

    poetry_scripts = (
        pyproject.get("tool", {})
        .get("poetry", {})
        .get("scripts", {})
    )
    if isinstance(poetry_scripts, dict):
        targets.extend(
            target
            for target in poetry_scripts.values()
            if isinstance(target, str)
        )

    return tuple(targets)


def _resolve_script_target_to_paths(
    target: str,
    candidate_paths: frozenset[str],
) -> tuple[str, ...]:
    """Resolve a console script target such as package.cli:main to file paths."""

    module_name = target.split(":", 1)[0].strip()
    if not module_name:
        return ()

    module_path = module_name.replace(".", "/")
    candidates = [
        f"{module_path}.py",
        f"src/{module_path}.py",
    ]

    if module_name.endswith(".__main__"):
        package_path = module_name[: -len(".__main__")].replace(".", "/")
        candidates.extend(
            [
                f"{package_path}/__main__.py",
                f"src/{package_path}/__main__.py",
            ]
        )

    matched = [candidate for candidate in candidates if candidate in candidate_paths]
    return tuple(dict.fromkeys(matched))


def _calculate_import_centrality_by_path(
    import_graph: object | None,
    candidate_paths: frozenset[str],
) -> dict[str, _ImportCentrality]:
    """Calculate simple import centrality from ImportGraph-like edges."""

    if import_graph is None:
        return {}

    edges = getattr(import_graph, "edges", None)
    if not edges:
        return {}

    incoming_sources_by_target: dict[str, set[str]] = {}
    outgoing_targets_by_source: dict[str, set[str]] = {}

    for edge in edges:
        source_path = _normalized_graph_path(getattr(edge, "source_path", None))
        target_path = _normalized_graph_path(getattr(edge, "target_path", None))

        if source_path is None or target_path is None:
            continue

        if source_path not in candidate_paths or target_path not in candidate_paths:
            continue

        if source_path == target_path:
            continue

        incoming_sources_by_target.setdefault(target_path, set()).add(source_path)
        outgoing_targets_by_source.setdefault(source_path, set()).add(target_path)

    centrality: dict[str, _ImportCentrality] = {}
    all_paths = set(incoming_sources_by_target) | set(outgoing_targets_by_source)

    for path in all_paths:
        incoming_count = len(incoming_sources_by_target.get(path, set()))
        outgoing_count = len(outgoing_targets_by_source.get(path, set()))
        score = _bounded_score(
            incoming_count,
            weight=IMPORT_INCOMING_WEIGHT,
            maximum=IMPORT_INCOMING_MAX_SCORE,
        ) + _bounded_score(
            outgoing_count,
            weight=IMPORT_OUTGOING_WEIGHT,
            maximum=IMPORT_OUTGOING_MAX_SCORE,
        )
        centrality[path] = _ImportCentrality(
            score=score,
            incoming_count=incoming_count,
            outgoing_count=outgoing_count,
        )

    return centrality


def _calculate_call_centrality_by_path(
    call_graph: object | None,
    symbols: object | None,
    candidate_paths: frozenset[str],
) -> dict[str, _CallCentrality]:
    """Calculate file centrality from resolved local CallGraph-like edges."""

    if call_graph is None:
        return {}

    edges = getattr(call_graph, "edges", None)
    if not edges:
        return {}

    symbol_path_lookup = _build_symbol_path_lookup(symbols, candidate_paths)

    incoming_sources_by_target: dict[str, set[str]] = {}
    outgoing_targets_by_source: dict[str, set[str]] = {}

    for edge in edges:
        source_path = _normalized_graph_path(getattr(edge, "caller_file", None))
        target_path = _resolve_call_target_path(edge, symbol_path_lookup)

        if source_path is None or target_path is None:
            continue

        if source_path not in candidate_paths or target_path not in candidate_paths:
            continue

        if source_path == target_path:
            continue

        incoming_sources_by_target.setdefault(target_path, set()).add(source_path)
        outgoing_targets_by_source.setdefault(source_path, set()).add(target_path)

    centrality: dict[str, _CallCentrality] = {}
    all_paths = set(incoming_sources_by_target) | set(outgoing_targets_by_source)

    for path in all_paths:
        incoming_count = len(incoming_sources_by_target.get(path, set()))
        outgoing_count = len(outgoing_targets_by_source.get(path, set()))
        score = _bounded_score(
            incoming_count,
            weight=CALL_INCOMING_WEIGHT,
            maximum=CALL_INCOMING_MAX_SCORE,
        ) + _bounded_score(
            outgoing_count,
            weight=CALL_OUTGOING_WEIGHT,
            maximum=CALL_OUTGOING_MAX_SCORE,
        )
        centrality[path] = _CallCentrality(
            score=score,
            incoming_count=incoming_count,
            outgoing_count=outgoing_count,
        )

    return centrality


def _build_symbol_path_lookup(
    symbols: object | None,
    candidate_paths: frozenset[str],
) -> dict[str, str]:
    """Build best-effort symbol qualified-name to file path lookup."""

    if symbols is None:
        return {}

    lookup: dict[str, str] = {}
    indexes = _iter_symbol_indexes(symbols)

    for index in indexes:
        index_file_path = _normalized_graph_path(getattr(index, "file_path", None))
        if index_file_path not in candidate_paths:
            continue

        module_name = _module_name_from_path(index_file_path)
        for symbol in getattr(index, "symbols", ()) or ():
            symbol_name = getattr(symbol, "name", None)
            if not symbol_name:
                continue

            symbol_file_path = _normalized_graph_path(
                getattr(symbol, "file_path", None)
            ) or index_file_path

            if symbol_file_path not in candidate_paths:
                continue

            parent = getattr(symbol, "parent", None)
            keys = {str(symbol_name)}

            if parent:
                keys.add(f"{parent}.{symbol_name}")

            if module_name:
                keys.add(f"{module_name}.{symbol_name}")
                if parent:
                    keys.add(f"{module_name}.{parent}.{symbol_name}")

            for key in keys:
                lookup.setdefault(key, symbol_file_path)

    return lookup


def _iter_symbol_indexes(symbols: object) -> tuple[object, ...]:
    """Return FileSymbolIndex-like items from multiple possible containers."""

    if isinstance(symbols, (str, bytes)):
        return ()

    if isinstance(symbols, Iterable):
        return tuple(symbols)

    for attribute_name in ("files", "indexes", "symbol_indexes"):
        value = getattr(symbols, attribute_name, None)
        if value is None or isinstance(value, (str, bytes)):
            continue
        if isinstance(value, Iterable):
            return tuple(value)

    return ()


def _resolve_call_target_path(
    edge: object,
    symbol_path_lookup: dict[str, str],
) -> str | None:
    """Resolve a call edge callee to a repository-relative file path."""

    explicit_path = _normalized_graph_path(getattr(edge, "callee_file", None))
    if explicit_path is not None:
        return explicit_path

    qualified_name = getattr(edge, "callee_qualified_name", None)
    if isinstance(qualified_name, str):
        exact_match = symbol_path_lookup.get(qualified_name)
        if exact_match is not None:
            return exact_match

        # A qualified unresolved target such as demo.ghost.run must not be
        # resolved through a bare symbol named run in another file. Only allow
        # suffix matches against qualified keys such as service.run or
        # Service.execute, never against plain function names.
        suffix_matches = [
            path
            for key, path in symbol_path_lookup.items()
            if "." in key and qualified_name.endswith(f".{key}")
        ]
        unique_matches = sorted(set(suffix_matches))
        if len(unique_matches) == 1:
            return unique_matches[0]

        return None

    callee_name = getattr(edge, "callee_name", None)
    if isinstance(callee_name, str):
        return symbol_path_lookup.get(callee_name)

    return None


def _module_name_from_path(path: str | None) -> str | None:
    """Return a best-effort Python module name for a repository path."""

    if not path:
        return None

    normalized = Path(path).as_posix()
    if normalized.endswith("/__init__.py"):
        normalized = normalized[: -len("/__init__.py")]
    elif normalized.endswith(".py"):
        normalized = normalized[: -len(".py")]
    else:
        return None

    if normalized.startswith("src/"):
        normalized = normalized[len("src/") :]

    return normalized.replace("/", ".")


def _bounded_score(count: int, *, weight: int, maximum: int) -> int:
    """Return a capped linear score for count-based centrality signals."""

    if count <= 0:
        return 0
    return min(maximum, count * weight)


def _normalized_graph_path(path: object) -> str | None:
    """Return a normalized path from an import/call graph edge path."""

    if path is None:
        return None
    return Path(path).as_posix()


def _relative_path_from_file(file_info: object) -> Path | None:
    """Return a repository-relative path from a FileInfo-like object or path."""

    if isinstance(file_info, Path):
        return file_info

    if isinstance(file_info, str):
        return Path(file_info)

    relative_path = getattr(file_info, "relative_path", None)
    if relative_path is None:
        return None

    return Path(relative_path)


def _is_important_file_candidate(file_info: object, path: Path) -> bool:
    """Return True when a file may participate in important-file ranking."""

    normalized_path = path.as_posix().lower()
    filename = path.name.lower()

    if filename in GENERATED_EXPORT_FILENAMES:
        return False

    if normalized_path in NON_PROJECT_EXPORT_PATHS:
        return False

    if getattr(file_info, "is_binary", False) is True:
        return False

    if getattr(file_info, "is_text", True) is False:
        return False

    if getattr(file_info, "error", None) is not None:
        return False

    return True


def _score_path(
    file_info: object,
    path: Path,
    *,
    pyproject_entrypoint_paths: frozenset[str],
    import_centrality_by_path: dict[str, _ImportCentrality],
    call_centrality_by_path: dict[str, _CallCentrality],
) -> ImportantFileScore | None:
    """Score one file path and return an explainable ranking result."""

    path_key = path.as_posix()

    entrypoint_score, entrypoint_reasons = _score_entrypoint_path(
        path,
        pyproject_entrypoint_paths=pyproject_entrypoint_paths,
    )
    import_centrality = import_centrality_by_path.get(path_key, _ImportCentrality())
    call_centrality = call_centrality_by_path.get(path_key, _CallCentrality())
    documentation_score, documentation_reasons = _score_documentation_path(path)
    structural_score, structural_reasons = _score_structural_path(file_info, path)

    signals = ImportantFileSignals(
        entrypoint_score=entrypoint_score,
        import_centrality_score=import_centrality.score,
        call_centrality_score=call_centrality.score,
        documentation_score=documentation_score,
        structural_score=structural_score,
    )

    reasons = (
        *entrypoint_reasons,
        *import_centrality.reasons,
        *call_centrality.reasons,
        *documentation_reasons,
        *structural_reasons,
    )

    if signals.total <= 0 or not reasons:
        return None

    return ImportantFileScore(
        path=path_key,
        score=signals.total,
        reasons=tuple(reasons),
        signals=signals,
    )


def _score_entrypoint_path(
    path: Path,
    *,
    pyproject_entrypoint_paths: frozenset[str],
) -> tuple[int, tuple[str, ...]]:
    """Return entrypoint score and reasons for a Python file path."""

    normalized_path = path.as_posix()
    filename = path.name.lower()
    score = 0
    reasons: list[str] = []

    if normalized_path in pyproject_entrypoint_paths:
        score += 100
        reasons.append("Project script entry point")

    filename_score = PYTHON_ENTRYPOINT_FILENAMES.get(filename, 0)
    if filename_score:
        score += filename_score
        if filename == "__main__.py":
            reasons.append("Python module entry point")
        else:
            reasons.append("Likely Python entry point")

    return score, tuple(reasons)


def _score_documentation_path(path: Path) -> tuple[int, tuple[str, ...]]:
    """Return documentation score and reasons for a path."""

    normalized_path = path.as_posix().lower()
    filename = path.name.lower()
    suffix = path.suffix.lower()

    if filename == "license" or filename.startswith("license."):
        return 35, ("Project license",)

    if filename.startswith("readme"):
        return 90, ("Primary project documentation",)

    if "architecture" in filename or "architecture" in normalized_path:
        return 80, ("Architecture documentation",)

    if "spec" in filename:
        return 75, ("Project specification",)

    if "tasks" in filename or "roadmap" in filename or "milestone" in filename:
        return 55, ("Planning or roadmap documentation",)

    if "changelog" in filename:
        return 45, ("Changelog documentation",)

    if "contributing" in filename:
        return 40, ("Contribution documentation",)

    if normalized_path.startswith("docs/") and suffix in DOCUMENTATION_EXTENSIONS:
        return 25, ("Documentation file",)

    if normalized_path.startswith("planning/") and suffix in DOCUMENTATION_EXTENSIONS:
        return 20, ("Planning documentation file",)

    return 0, ()


def _score_structural_path(file_info: object, path: Path) -> tuple[int, tuple[str, ...]]:
    """Return structural project score and reasons for a path."""

    normalized_path = path.as_posix().lower()
    filename = path.name.lower()

    if filename == "pyproject.toml":
        return 70, ("Python project configuration",)

    if filename == "setup.py":
        return 65, ("Python packaging entry point",)

    if filename == "setup.cfg":
        return 60, ("Python package configuration",)

    if filename.startswith("requirements") and path.suffix.lower() == ".txt":
        return 50, ("Python dependency list",)

    if filename == "package.json":
        return 45, ("JavaScript project configuration",)

    if filename == "dockerfile":
        return 40, ("Container build configuration",)

    if filename == "makefile":
        return 40, ("Project automation entry point",)

    if filename == "__init__.py" or normalized_path.endswith("/__init__.py"):
        if _contains_public_package_api(file_info):
            return 20, ("Package initializer with public API",)
        return 5, ("Package initializer",)

    return 0, ()


def _contains_public_package_api(file_info: object) -> bool:
    """Return True when an __init__.py file appears to expose a package API."""

    content = getattr(file_info, "content", None)
    if not content:
        return False

    if "__all__" in content:
        return True

    meaningful_lines = []
    single_quote_docstring_delimiter = "'" * 3

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line in {'"""', single_quote_docstring_delimiter}:
            continue
        meaningful_lines.append(line)

    return len(meaningful_lines) > 2


def _important_file_sort_key(
    score: ImportantFileScore,
) -> tuple[int, int, str]:
    """Return deterministic sort key for ranking results."""

    return (
        -score.score,
        score.path.count("/"),
        score.path,
    )


__all__ = [
    "GENERATED_EXPORT_FILENAMES",
    "ImportantFileScore",
    "ImportantFileSignals",
    "rank_important_files",
]
