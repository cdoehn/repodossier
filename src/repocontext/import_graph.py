"""Data models and parsers for Python import analysis and dependency graphs."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal


ImportType = Literal["import", "from"]


@dataclass(frozen=True, slots=True)
class ImportReference:
    """A single import statement discovered in a Python source file."""

    source_path: Path
    source_module: str
    imported_module: str | None
    imported_name: str | None = None
    alias: str | None = None
    import_type: ImportType = "import"
    level: int = 0
    line_number: int = 0
    is_relative: bool = False
    is_local: bool | None = None
    resolved_module: str | None = None
    resolved_path: Path | None = None

    def __post_init__(self) -> None:
        if self.import_type not in {"import", "from"}:
            raise ValueError("import_type must be 'import' or 'from'")
        if self.level < 0:
            raise ValueError("level must not be negative")
        if self.line_number < 0:
            raise ValueError("line_number must not be negative")
        if not isinstance(self.source_path, Path):
            object.__setattr__(self, "source_path", Path(self.source_path))
        if self.resolved_path is not None and not isinstance(self.resolved_path, Path):
            object.__setattr__(self, "resolved_path", Path(self.resolved_path))


@dataclass(frozen=True, slots=True)
class ImportEdge:
    """A local module dependency derived from an import reference."""

    source_module: str
    target_module: str
    source_path: Path
    target_path: Path
    import_type: ImportType
    imported_name: str | None = None
    line_number: int = 0

    def __post_init__(self) -> None:
        if self.import_type not in {"import", "from"}:
            raise ValueError("import_type must be 'import' or 'from'")
        if self.line_number < 0:
            raise ValueError("line_number must not be negative")
        if not isinstance(self.source_path, Path):
            object.__setattr__(self, "source_path", Path(self.source_path))
        if not isinstance(self.target_path, Path):
            object.__setattr__(self, "target_path", Path(self.target_path))


@dataclass(frozen=True, slots=True)
class ImportAnalysisError:
    """A non-fatal error encountered while analyzing imports in a file."""

    source_path: Path
    message: str
    error_type: str = "ImportAnalysisError"
    line_number: int | None = None

    def __post_init__(self) -> None:
        if self.line_number is not None and self.line_number < 0:
            raise ValueError("line_number must not be negative")
        if not isinstance(self.source_path, Path):
            object.__setattr__(self, "source_path", Path(self.source_path))


@dataclass(frozen=True, slots=True)
class ImportGraph:
    """Complete import graph analysis result for a repository."""

    modules: Mapping[str, str | Path]
    edges: tuple[ImportEdge, ...] = ()
    external_imports: tuple[ImportReference, ...] = ()
    unresolved_imports: tuple[ImportReference, ...] = ()
    errors: tuple[ImportAnalysisError, ...] = ()

    def __post_init__(self) -> None:
        normalized_modules = {
            module_name: Path(module_path)
            for module_name, module_path in self.modules.items()
        }
        object.__setattr__(self, "modules", normalized_modules)
        object.__setattr__(self, "edges", tuple(self.edges))
        object.__setattr__(self, "external_imports", tuple(self.external_imports))
        object.__setattr__(self, "unresolved_imports", tuple(self.unresolved_imports))
        object.__setattr__(self, "errors", tuple(self.errors))


class _ImportVisitor(ast.NodeVisitor):
    """Collect import references from a parsed Python AST."""

    def __init__(self, source_path: Path, source_module: str) -> None:
        self.source_path = source_path
        self.source_module = source_module
        self.references: list[ImportReference] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.references.append(
                ImportReference(
                    source_path=self.source_path,
                    source_module=self.source_module,
                    imported_module=alias.name,
                    imported_name=None,
                    alias=alias.asname,
                    import_type="import",
                    level=0,
                    line_number=getattr(node, "lineno", 0),
                    is_relative=False,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        level = node.level or 0
        for alias in node.names:
            self.references.append(
                ImportReference(
                    source_path=self.source_path,
                    source_module=self.source_module,
                    imported_module=node.module,
                    imported_name=alias.name,
                    alias=alias.asname,
                    import_type="from",
                    level=level,
                    line_number=getattr(node, "lineno", 0),
                    is_relative=level > 0,
                )
            )



def _path_relative_to_root(path: Path, repo_root: Path) -> Path:
    """Return a best-effort repository-relative path without requiring files to exist."""

    if path.is_absolute() and not repo_root.is_absolute():
        repo_root = repo_root.resolve()

    try:
        return path.relative_to(repo_root)
    except ValueError:
        pass

    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
    except ValueError:
        return path


def module_name_from_python_path(
    source_path: str | Path,
    *,
    repo_root: str | Path = ".",
) -> str | None:
    """Convert a Python file path into its canonical dotted module name.

    Examples:
    - src/repocontext/scanner.py -> repocontext.scanner
    - src/repocontext/__init__.py -> repocontext
    - tests/test_scanner.py -> tests.test_scanner
    """

    path = Path(source_path)
    if path.suffix != ".py":
        return None

    relative_path = _path_relative_to_root(path, Path(repo_root))
    parts = list(relative_path.with_suffix("").parts)

    if parts and parts[0] == "src":
        parts = parts[1:]

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    if not parts:
        return None

    if not all(part.isidentifier() for part in parts):
        return None

    return ".".join(parts)


def build_python_module_map(
    source_paths: list[str | Path] | tuple[str | Path, ...],
    *,
    repo_root: str | Path = ".",
) -> dict[str, Path]:
    """Build a deterministic local module-name to file-path map for Python files."""

    module_map: dict[str, Path] = {}

    for source_path in sorted((Path(path) for path in source_paths), key=lambda path: path.as_posix()):
        module_name = module_name_from_python_path(source_path, repo_root=repo_root)
        if module_name is None:
            continue
        module_map.setdefault(module_name, source_path)

    return module_map


def _absolute_local_import_candidates(reference: ImportReference) -> list[str]:
    """Return local module candidates for an absolute import reference."""

    if reference.import_type == "import":
        if reference.imported_module is None:
            return []
        return [reference.imported_module]

    if reference.import_type == "from":
        candidates: list[str] = []
        if reference.imported_module:
            if reference.imported_name and reference.imported_name != "*":
                candidates.append(f"{reference.imported_module}.{reference.imported_name}")
            candidates.append(reference.imported_module)
        return candidates

    return []


def _lookup_local_module(
    module_name: str,
    module_map: Mapping[str, str | Path],
) -> tuple[str, Path] | None:
    """Look up a module name in a local module map."""

    target_path = module_map.get(module_name)
    if target_path is None:
        return None
    return module_name, Path(target_path)


def resolve_absolute_import_reference(
    reference: ImportReference,
    module_map: Mapping[str, str | Path],
) -> ImportReference:
    """Resolve one absolute import reference against known local modules.

    Relative imports are intentionally left unchanged here. They are handled in
    the dedicated relative-import resolver step.
    """

    if reference.is_relative or reference.level > 0:
        return reference

    for candidate in _absolute_local_import_candidates(reference):
        resolved = _lookup_local_module(candidate, module_map)
        if resolved is None:
            continue

        resolved_module, resolved_path = resolved
        return replace(
            reference,
            is_local=True,
            resolved_module=resolved_module,
            resolved_path=resolved_path,
        )

    return replace(
        reference,
        is_local=False,
        resolved_module=None,
        resolved_path=None,
    )


def resolve_absolute_imports(
    references: list[ImportReference] | tuple[ImportReference, ...],
    module_map: Mapping[str, str | Path],
) -> list[ImportReference]:
    """Resolve absolute import references against known local modules."""

    return [
        resolve_absolute_import_reference(reference, module_map)
        for reference in references
    ]


def _source_package_parts(reference: ImportReference) -> list[str]:
    """Return package parts for resolving relative imports from a source module."""

    source_parts = reference.source_module.split(".") if reference.source_module else []

    if reference.source_path.name == "__init__.py":
        return source_parts

    return source_parts[:-1]


def _relative_import_base_parts(reference: ImportReference) -> list[str] | None:
    """Return base package parts after applying a relative import level."""

    if reference.level <= 0:
        return None

    package_parts = _source_package_parts(reference)
    parent_hops = reference.level - 1

    if parent_hops > len(package_parts):
        return None

    if parent_hops == 0:
        return package_parts

    return package_parts[:-parent_hops]


def _relative_local_import_candidates(reference: ImportReference) -> list[str]:
    """Return local module candidates for a relative import reference."""

    base_parts = _relative_import_base_parts(reference)
    if base_parts is None:
        return []

    candidates: list[str] = []

    if reference.imported_module:
        module_parts = base_parts + reference.imported_module.split(".")
        module_name = ".".join(module_parts)

        if reference.imported_name and reference.imported_name != "*":
            candidates.append(f"{module_name}.{reference.imported_name}")

        candidates.append(module_name)
        return candidates

    if reference.imported_name and reference.imported_name != "*":
        candidates.append(".".join(base_parts + [reference.imported_name]))

    return candidates


def resolve_relative_import_reference(
    reference: ImportReference,
    module_map: Mapping[str, str | Path],
) -> ImportReference:
    """Resolve one relative import reference against known local modules."""

    if not reference.is_relative and reference.level <= 0:
        return reference

    for candidate in _relative_local_import_candidates(reference):
        resolved = _lookup_local_module(candidate, module_map)
        if resolved is None:
            continue

        resolved_module, resolved_path = resolved
        return replace(
            reference,
            is_local=True,
            resolved_module=resolved_module,
            resolved_path=resolved_path,
        )

    return replace(
        reference,
        is_local=False,
        resolved_module=None,
        resolved_path=None,
    )


def resolve_relative_imports(
    references: list[ImportReference] | tuple[ImportReference, ...],
    module_map: Mapping[str, str | Path],
) -> list[ImportReference]:
    """Resolve relative import references against known local modules."""

    return [
        resolve_relative_import_reference(reference, module_map)
        for reference in references
    ]


def resolve_import_reference(
    reference: ImportReference,
    module_map: Mapping[str, str | Path],
) -> ImportReference:
    """Resolve an import reference to a local file target when possible.

    This is the unified resolver for callers that do not want to care whether
    an import was absolute or relative. Local imports receive resolved_module
    and resolved_path. External or unresolved imports are marked as not local.
    """

    if reference.is_relative or reference.level > 0:
        return resolve_relative_import_reference(reference, module_map)

    return resolve_absolute_import_reference(reference, module_map)


def resolve_imports(
    references: list[ImportReference] | tuple[ImportReference, ...],
    module_map: Mapping[str, str | Path],
) -> list[ImportReference]:
    """Resolve absolute and relative imports against known local modules."""

    return [
        resolve_import_reference(reference, module_map)
        for reference in references
    ]


def resolved_import_target(reference: ImportReference) -> tuple[str, Path] | None:
    """Return the resolved local module and path for an import reference."""

    if not reference.is_local:
        return None

    if reference.resolved_module is None or reference.resolved_path is None:
        return None

    return reference.resolved_module, reference.resolved_path


def import_edge_from_reference(reference: ImportReference) -> ImportEdge | None:
    """Create a local dependency edge from a resolved import reference."""

    target = resolved_import_target(reference)
    if target is None:
        return None

    target_module, target_path = target
    return ImportEdge(
        source_module=reference.source_module,
        target_module=target_module,
        source_path=reference.source_path,
        target_path=target_path,
        import_type=reference.import_type,
        imported_name=reference.imported_name,
        line_number=reference.line_number,
    )



def _import_edge_dependency_key(edge: ImportEdge) -> tuple[str, str]:
    """Return the graph-level identity of a local module dependency edge."""

    return edge.source_module, edge.target_module


def deduplicate_import_edges(
    edges: list[ImportEdge] | tuple[ImportEdge, ...],
) -> tuple[ImportEdge, ...]:
    """Remove duplicate module dependency edges while keeping first-seen metadata.

    The dependency graph is module-to-module. If one source module imports the
    same target module multiple ways, the first edge is kept and later duplicate
    source-target edges are omitted.
    """

    seen: set[tuple[str, str]] = set()
    deduplicated_edges: list[ImportEdge] = []

    for edge in edges:
        key = _import_edge_dependency_key(edge)
        if key in seen:
            continue
        seen.add(key)
        deduplicated_edges.append(edge)

    return tuple(deduplicated_edges)


def _normalize_module_names(modules: Iterable[str] | None) -> list[str]:
    """Return deterministic module names for adjacency-list initialization."""

    if modules is None:
        return []

    return sorted(set(modules))


def build_depends_on_adjacency(
    edges: list[ImportEdge] | tuple[ImportEdge, ...],
    *,
    modules: Iterable[str] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Build module -> imported local modules adjacency from import edges."""

    adjacency: dict[str, set[str]] = {
        module_name: set()
        for module_name in _normalize_module_names(modules)
    }

    for edge in edges:
        adjacency.setdefault(edge.source_module, set()).add(edge.target_module)

    return {
        module_name: tuple(sorted(target_modules))
        for module_name, target_modules in sorted(adjacency.items())
    }


def build_used_by_adjacency(
    edges: list[ImportEdge] | tuple[ImportEdge, ...],
    *,
    modules: Iterable[str] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Build module -> local modules importing it adjacency from import edges."""

    adjacency: dict[str, set[str]] = {
        module_name: set()
        for module_name in _normalize_module_names(modules)
    }

    for edge in edges:
        adjacency.setdefault(edge.target_module, set()).add(edge.source_module)

    return {
        module_name: tuple(sorted(source_modules))
        for module_name, source_modules in sorted(adjacency.items())
    }


def import_graph_depends_on(graph: ImportGraph) -> dict[str, tuple[str, ...]]:
    """Return depends_on adjacency for all modules in an import graph."""

    return build_depends_on_adjacency(
        graph.edges,
        modules=graph.modules.keys(),
    )


def import_graph_used_by(graph: ImportGraph) -> dict[str, tuple[str, ...]]:
    """Return used_by adjacency for all modules in an import graph."""

    return build_used_by_adjacency(
        graph.edges,
        modules=graph.modules.keys(),
    )

def build_import_graph(
    source_paths: list[str | Path] | tuple[str | Path, ...],
    *,
    repo_root: str | Path = ".",
) -> ImportGraph:
    """Build an import graph for the given Python source files.

    The builder parses imports, resolves them against local modules, converts
    local imports into graph edges, and keeps external imports, unresolved
    imports, and analysis errors separate.
    """

    module_map = build_python_module_map(source_paths, repo_root=repo_root)
    edges: list[ImportEdge] = []
    external_imports: list[ImportReference] = []
    unresolved_imports: list[ImportReference] = []
    errors: list[ImportAnalysisError] = []

    for source_path in sorted((Path(path) for path in source_paths), key=lambda path: path.as_posix()):
        source_module = module_name_from_python_path(source_path, repo_root=repo_root)
        if source_module is None:
            continue

        references, parse_errors = parse_imports_from_file(
            source_path,
            source_module=source_module,
        )
        errors.extend(parse_errors)

        resolved_references = resolve_imports(references, module_map)
        for reference in resolved_references:
            edge = import_edge_from_reference(reference)
            if edge is not None:
                edges.append(edge)
                continue

            if reference.is_relative or reference.level > 0:
                unresolved_imports.append(reference)
            else:
                external_imports.append(reference)

    return ImportGraph(
        modules=module_map,
        edges=deduplicate_import_edges(edges),
        external_imports=tuple(external_imports),
        unresolved_imports=tuple(unresolved_imports),
        errors=tuple(errors),
    )

def parse_imports_from_source(
    source: str,
    *,
    source_path: str | Path,
    source_module: str,
) -> tuple[list[ImportReference], list[ImportAnalysisError]]:
    """Parse Python source text and return discovered imports plus non-fatal errors."""

    normalized_source_path = Path(source_path)

    try:
        tree = ast.parse(source, filename=str(normalized_source_path))
    except SyntaxError as exc:
        return [], [
            ImportAnalysisError(
                source_path=normalized_source_path,
                message=exc.msg or str(exc),
                error_type="SyntaxError",
                line_number=exc.lineno,
            )
        ]
    except ValueError as exc:
        return [], [
            ImportAnalysisError(
                source_path=normalized_source_path,
                message=str(exc),
                error_type=type(exc).__name__,
                line_number=None,
            )
        ]

    visitor = _ImportVisitor(
        source_path=normalized_source_path,
        source_module=source_module,
    )
    visitor.visit(tree)
    return visitor.references, []


def parse_imports_from_file(
    source_path: str | Path,
    *,
    source_module: str,
    encoding: str = "utf-8",
) -> tuple[list[ImportReference], list[ImportAnalysisError]]:
    """Read a Python file and return discovered imports plus non-fatal errors."""

    normalized_source_path = Path(source_path)

    try:
        source = normalized_source_path.read_text(encoding=encoding)
    except OSError as exc:
        return [], [
            ImportAnalysisError(
                source_path=normalized_source_path,
                message=str(exc),
                error_type=type(exc).__name__,
                line_number=None,
            )
        ]
    except UnicodeDecodeError as exc:
        return [], [
            ImportAnalysisError(
                source_path=normalized_source_path,
                message=str(exc),
                error_type=type(exc).__name__,
                line_number=None,
            )
        ]

    return parse_imports_from_source(
        source,
        source_path=normalized_source_path,
        source_module=source_module,
    )


__all__ = [
    "ImportAnalysisError",
    "ImportEdge",
    "ImportGraph",
    "ImportReference",
    "ImportType",
    "build_depends_on_adjacency",
    "build_import_graph",
    "build_python_module_map",
    "build_used_by_adjacency",
    "deduplicate_import_edges",
    "import_edge_from_reference",
    "import_graph_depends_on",
    "import_graph_used_by",
    "module_name_from_python_path",
    "parse_imports_from_file",
    "parse_imports_from_source",
    "resolve_absolute_import_reference",
    "resolve_absolute_imports",
    "resolve_import_reference",
    "resolve_imports",
    "resolve_relative_import_reference",
    "resolve_relative_imports",
    "resolved_import_target",
]
