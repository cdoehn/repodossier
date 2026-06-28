"""Static call graph data structures.

This module contains the internal model used by later AST-based call analysis.
It intentionally does not parse Python code yet; it only stores, deduplicates,
sorts, groups, and serializes call graph edges.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CallEdge:
    """A directed edge from one caller symbol to one callee symbol."""

    caller_file: str
    caller_name: str
    caller_qualified_name: str
    callee_name: str
    callee_qualified_name: str | None = None
    line_number: int | None = None
    call_type: str = "unknown"
    confidence: str = "unresolved"

    @property
    def caller_key(self) -> str:
        """Return the best stable key for the caller side of this edge."""

        return self.caller_qualified_name or self.caller_name

    @property
    def callee_key(self) -> str:
        """Return the best stable key for the callee side of this edge."""

        return self.callee_qualified_name or self.callee_name

    def sort_key(self) -> tuple[str, str, int, str, str, str]:
        """Return a deterministic sort key for stable exports and tests."""

        return (
            self.caller_file,
            self.caller_key,
            self.line_number if self.line_number is not None else -1,
            self.callee_key,
            self.call_type,
            self.confidence,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the edge."""

        return asdict(self)


@dataclass
class CallGraph:
    """A deterministic collection of call graph edges."""

    edges: list[CallEdge] = field(default_factory=list)
    _edge_set: set[CallEdge] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        original_edges = list(self.edges)
        self.edges.clear()
        for edge in original_edges:
            self.add_edge(edge)

    def add_edge(self, edge: CallEdge) -> bool:
        """Add an edge and return True when it was not already present."""

        if edge in self._edge_set:
            return False

        self._edge_set.add(edge)
        self.edges.append(edge)
        return True

    def sorted_edges(self) -> list[CallEdge]:
        """Return all edges in deterministic export order."""

        return sorted(self.edges, key=lambda edge: edge.sort_key())

    @property
    def callees_by_symbol(self) -> dict[str, tuple[CallEdge, ...]]:
        """Group outgoing calls by caller symbol."""

        grouped: dict[str, list[CallEdge]] = defaultdict(list)
        for edge in self.sorted_edges():
            grouped[edge.caller_key].append(edge)
        return {symbol: tuple(edges) for symbol, edges in grouped.items()}

    @property
    def callers_by_symbol(self) -> dict[str, tuple[CallEdge, ...]]:
        """Group incoming calls by callee symbol."""

        grouped: dict[str, list[CallEdge]] = defaultdict(list)
        for edge in self.sorted_edges():
            grouped[edge.callee_key].append(edge)
        return {symbol: tuple(edges) for symbol, edges in grouped.items()}

    def get_calls_from(self, symbol: str) -> tuple[CallEdge, ...]:
        """Return all outgoing calls from a caller symbol."""

        return tuple(
            edge
            for edge in self.sorted_edges()
            if edge.caller_key == symbol or edge.caller_name == symbol
        )

    def get_callers_of(self, symbol: str) -> tuple[CallEdge, ...]:
        """Return all incoming calls to a callee symbol."""

        return tuple(
            edge
            for edge in self.sorted_edges()
            if edge.callee_key == symbol or edge.callee_name == symbol
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the graph."""

        return {"edges": [edge.to_dict() for edge in self.sorted_edges()]}

    def to_text(self) -> str:
        """Return a compact deterministic text representation."""

        if not self.edges:
            return "No call graph edges found."

        lines: list[str] = []
        current_caller: str | None = None

        for edge in self.sorted_edges():
            caller = edge.caller_key
            if caller != current_caller:
                if lines:
                    lines.append("")
                lines.append(f"{caller} ({edge.caller_file})")
                current_caller = caller

            line = str(edge.line_number) if edge.line_number is not None else "unknown"
            lines.append(
                f"  - line {line}: calls {edge.callee_key} "
                f"[{edge.call_type}, {edge.confidence}]"
            )

        return "\n".join(lines)

@dataclass(frozen=True, slots=True)
class ImportAlias:
    """A local import binding discovered in a Python source file."""

    local_name: str
    qualified_name: str
    module_name: str | None
    imported_name: str | None = None
    alias: str | None = None
    import_type: str = "import"
    level: int = 0
    line_number: int = 0
    is_relative: bool = False
    is_local: bool | None = None
    resolved_module: str | None = None
    resolved_path: str | None = None

    def __post_init__(self) -> None:
        if self.import_type not in {"import", "from"}:
            raise ValueError("import_type must be 'import' or 'from'")
        if self.level < 0:
            raise ValueError("level must not be negative")
        if self.line_number < 0:
            raise ValueError("line_number must not be negative")
        if self.resolved_path is not None:
            object.__setattr__(
                self,
                "resolved_path",
                Path(self.resolved_path).as_posix(),
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the alias."""

        return asdict(self)


class PythonCallVisitor(ast.NodeVisitor):
    """Collect function and method calls while tracking Python caller context."""

    def __init__(
        self,
        *,
        source_path: str | Path,
        module_name: str | None = None,
        known_class_names: set[str] | None = None,
        known_function_counts: dict[str, int] | None = None,
        known_method_counts: dict[str, dict[str, int]] | None = None,
        import_aliases: dict[str, ImportAlias] | None = None,
    ) -> None:
        self.source_path = Path(source_path).as_posix()
        self.module_name = module_name
        self.known_class_names = set(known_class_names or ())
        self.known_function_counts = dict(known_function_counts or {})
        self.known_method_counts = {
            class_name: dict(method_counts)
            for class_name, method_counts in (known_method_counts or {}).items()
        }
        self.import_aliases = dict(import_aliases or {})
        self.graph = CallGraph()
        self._class_stack: list[str] = []
        self._function_stack: list[tuple[str, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class context while visiting class bodies."""

        self.known_class_names.add(node.name)
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track normal function context while visiting function bodies."""

        self._visit_function_node(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function context while visiting function bodies."""

        self._visit_function_node(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Record direct function calls and method calls."""

        caller_name, caller_qualified_name = self._current_caller()

        if isinstance(node.func, ast.Name):
            callee_qualified_name, confidence = self._resolve_function_call(node.func.id)
            self.graph.add_edge(
                CallEdge(
                    caller_file=self.source_path,
                    caller_name=caller_name,
                    caller_qualified_name=caller_qualified_name,
                    callee_name=node.func.id,
                    callee_qualified_name=callee_qualified_name,
                    line_number=getattr(node, "lineno", None),
                    call_type="function",
                    confidence=confidence,
                )
            )
        elif isinstance(node.func, ast.Attribute):
            callee_qualified_name, confidence = self._resolve_attribute_call(node)
            self.graph.add_edge(
                CallEdge(
                    caller_file=self.source_path,
                    caller_name=caller_name,
                    caller_qualified_name=caller_qualified_name,
                    callee_name=node.func.attr,
                    callee_qualified_name=callee_qualified_name,
                    line_number=getattr(node, "lineno", None),
                    call_type="method",
                    confidence=confidence,
                )
            )

        self.generic_visit(node)

    def _resolve_function_call(self, callee_name: str) -> tuple[str | None, str]:
        """Resolve direct calls to top-level functions in the same file."""

        candidate_count = self.known_function_counts.get(callee_name, 0)

        if candidate_count == 1:
            return self._qualify(callee_name), "local"

        if candidate_count > 1:
            return None, "ambiguous"

        return None, "unresolved"

    def _resolve_attribute_call(self, node: ast.Call) -> tuple[str | None, str]:
        """Resolve local class method calls when possible."""

        if not isinstance(node.func, ast.Attribute):
            return None, "unresolved"

        if self._is_self_method_call(node):
            class_name = ".".join(self._class_stack)
            return self._resolve_known_method(class_name, node.func.attr)

        cls_target = self._class_method_target(node)
        if cls_target is not None:
            return self._resolve_known_method(cls_target, node.func.attr)

        if self._is_chained_method_call(node):
            return None, "unresolved_method"

        return None, "unresolved"

    def _resolve_known_method(
        self,
        class_name: str,
        method_name: str,
    ) -> tuple[str | None, str]:
        """Resolve a method only when it is known and unambiguous."""

        method_counts = self.known_method_counts.get(class_name, {})
        candidate_count = method_counts.get(method_name, 0)

        if candidate_count == 1:
            return self._qualify(f"{class_name}.{method_name}"), "local_method"

        if candidate_count > 1:
            return None, "ambiguous"

        return None, "unresolved"

    def _is_chained_method_call(self, node: ast.Call) -> bool:
        """Return True for chained calls such as obj.load().parse()."""

        if not isinstance(node.func, ast.Attribute):
            return False

        return isinstance(node.func.value, ast.Call)

    def _is_self_method_call(self, node: ast.Call) -> bool:
        """Return True when the call is self.method() inside a class."""

        if not self._class_stack:
            return False

        if not isinstance(node.func, ast.Attribute):
            return False

        return isinstance(node.func.value, ast.Name) and node.func.value.id == "self"

    def _class_method_target(self, node: ast.Call) -> str | None:
        """Return the target class for cls.method() or ClassName.method()."""

        if not self._class_stack:
            return None

        if not isinstance(node.func, ast.Attribute):
            return None

        if not isinstance(node.func.value, ast.Name):
            return None

        base_name = node.func.value.id

        if base_name == "cls":
            return ".".join(self._class_stack)

        if base_name in self.known_class_names:
            return base_name

        return None

    def _visit_function_node(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        """Push function or method context while visiting a body."""

        caller_name, caller_qualified_name = self._function_context_for(node)
        self._function_stack.append((caller_name, caller_qualified_name))
        self.generic_visit(node)
        self._function_stack.pop()

    def _function_context_for(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> tuple[str, str]:
        """Return display and qualified context names for a function node."""

        if self._function_stack:
            parent_name, parent_qualified_name = self._function_stack[-1]
            caller_name = f"{parent_name}.{node.name}"
            caller_qualified_name = f"{parent_qualified_name}.{node.name}"
            return caller_name, caller_qualified_name

        if self._class_stack:
            class_name = ".".join(self._class_stack)
            caller_name = f"{class_name}.{node.name}"
            return caller_name, self._qualify(caller_name)

        return node.name, self._qualify(node.name)

    def _current_caller(self) -> tuple[str, str]:
        """Return the current caller context for a discovered call."""

        if self._function_stack:
            return self._function_stack[-1]

        caller_name = "<module>"
        return caller_name, self._qualify(caller_name)

    def _qualify(self, name: str) -> str:
        """Return a module-qualified name when a module name is known."""

        if self.module_name:
            return f"{self.module_name}.{name}"
        return name


def _increment_count(counter: dict[str, int], name: str) -> None:
    """Increment a string-keyed count dictionary in place."""

    counter[name] = counter.get(name, 0) + 1


def _collect_class_names(tree: ast.AST) -> set[str]:
    """Return class names defined in a parsed Python AST."""

    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }


def _collect_top_level_function_counts(tree: ast.AST) -> dict[str, int]:
    """Return top-level function name counts from a parsed Python AST."""

    counts: dict[str, int] = {}

    if not isinstance(tree, ast.Module):
        return counts

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _increment_count(counts, node.name)

    return counts


def _collect_class_method_counts(tree: ast.AST) -> dict[str, dict[str, int]]:
    """Return direct method name counts by class from a parsed Python AST."""

    counts: dict[str, dict[str, int]] = {}

    def visit_class(node: ast.ClassDef, parents: tuple[str, ...] = ()) -> None:
        class_name = ".".join((*parents, node.name))
        method_counts = counts.setdefault(class_name, {})

        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _increment_count(method_counts, child.name)

        for child in node.body:
            if isinstance(child, ast.ClassDef):
                visit_class(child, (*parents, node.name))

    for node in ast.walk(tree):
        if isinstance(node, ast.Module):
            for child in node.body:
                if isinstance(child, ast.ClassDef):
                    visit_class(child)

    return counts


def _merge_counts(target: dict[str, int], source: dict[str, int]) -> dict[str, int]:
    """Return merged count dictionaries."""

    merged = dict(target)
    for name, count in source.items():
        merged[name] = merged.get(name, 0) + count
    return merged


def _merge_method_counts(
    target: dict[str, dict[str, int]],
    source: dict[str, dict[str, int]],
) -> dict[str, dict[str, int]]:
    """Return merged class-method count dictionaries."""

    merged = {class_name: dict(method_counts) for class_name, method_counts in target.items()}

    for class_name, method_counts in source.items():
        class_target = merged.setdefault(class_name, {})
        for method_name, count in method_counts.items():
            class_target[method_name] = class_target.get(method_name, 0) + count

    return merged


def _paths_match_for_symbol_index(index_path: object, source_path: str | Path) -> bool:
    """Return True when a symbol-index path refers to the analyzed file."""

    file_path = Path(str(index_path)).as_posix()
    target_path = Path(source_path).as_posix()

    return (
        file_path == target_path
        or target_path.endswith(file_path)
        or file_path.endswith(target_path)
    )


def _function_counts_from_symbol_index(
    symbol_index: object,
    *,
    source_path: str | Path,
) -> dict[str, int]:
    """Return top-level function name counts for a file from an existing symbol index."""

    function_counts: dict[str, int] = {}

    for file_index in symbol_index or ():
        if not _paths_match_for_symbol_index(
            getattr(file_index, "file_path", ""),
            source_path,
        ):
            continue

        for symbol in getattr(file_index, "symbols", ()):
            if getattr(symbol, "kind", None) != "function":
                continue
            if getattr(symbol, "parent", None) is not None:
                continue

            name = getattr(symbol, "name", None)
            if isinstance(name, str) and name:
                _increment_count(function_counts, name)

    return function_counts


def _method_counts_from_symbol_index(
    symbol_index: object,
    *,
    source_path: str | Path,
) -> dict[str, dict[str, int]]:
    """Return method name counts by class for a file from an existing symbol index."""

    method_counts_by_class: dict[str, dict[str, int]] = {}

    for file_index in symbol_index or ():
        if not _paths_match_for_symbol_index(
            getattr(file_index, "file_path", ""),
            source_path,
        ):
            continue

        for symbol in getattr(file_index, "symbols", ()):
            if getattr(symbol, "kind", None) != "method":
                continue

            parent = getattr(symbol, "parent", None)
            name = getattr(symbol, "name", None)
            if not isinstance(parent, str) or not parent:
                continue
            if not isinstance(name, str) or not name:
                continue

            class_counts = method_counts_by_class.setdefault(parent, {})
            _increment_count(class_counts, name)

    return method_counts_by_class



def _relative_module_name(module: str | None, level: int) -> str | None:
    """Return a dotted module name including relative import prefixes."""

    prefix = "." * level
    if module:
        return f"{prefix}{module}"
    return prefix or None


def _qualified_import_name(module_name: str | None, imported_name: str | None) -> str:
    """Return a stable qualified name for an import binding."""

    if module_name and imported_name:
        return f"{module_name}.{imported_name}"
    if module_name:
        return module_name
    if imported_name:
        return imported_name
    return ""


class _ImportAliasVisitor(ast.NodeVisitor):
    """Collect local import bindings from a parsed Python AST."""

    def __init__(self) -> None:
        self.aliases: dict[str, ImportAlias] = {}

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            local_name = alias.asname or alias.name.split(".", 1)[0]
            self.aliases[local_name] = ImportAlias(
                local_name=local_name,
                qualified_name=alias.name,
                module_name=alias.name,
                imported_name=None,
                alias=alias.asname,
                import_type="import",
                level=0,
                line_number=getattr(node, "lineno", 0),
                is_relative=False,
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        level = node.level or 0
        module_name = _relative_module_name(node.module, level)

        for alias in node.names:
            if alias.name == "*":
                continue

            local_name = alias.asname or alias.name
            self.aliases[local_name] = ImportAlias(
                local_name=local_name,
                qualified_name=_qualified_import_name(module_name, alias.name),
                module_name=module_name,
                imported_name=alias.name,
                alias=alias.asname,
                import_type="from",
                level=level,
                line_number=getattr(node, "lineno", 0),
                is_relative=level > 0,
            )


def collect_import_aliases_from_ast(tree: ast.AST) -> dict[str, ImportAlias]:
    """Collect local import aliases from a parsed Python AST."""

    visitor = _ImportAliasVisitor()
    visitor.visit(tree)
    return {
        name: visitor.aliases[name]
        for name in sorted(visitor.aliases)
    }


def collect_import_aliases_from_source(source: str, *, source_path: str | Path = "<string>") -> dict[str, ImportAlias]:
    """Parse Python source text and collect local import aliases."""

    tree = ast.parse(source, filename=str(source_path))
    return collect_import_aliases_from_ast(tree)


def _import_graph_edges_for_source(
    import_graph: object,
    *,
    source_module: str | None = None,
    source_path: str | Path | None = None,
) -> tuple[object, ...]:
    """Return import graph edges matching a source module or path."""

    edges = tuple(getattr(import_graph, "edges", ()))
    if source_module is None and source_path is None:
        return edges

    normalized_source_path = (
        Path(source_path).as_posix()
        if source_path is not None
        else None
    )

    matching_edges: list[object] = []

    for edge in edges:
        edge_source_module = getattr(edge, "source_module", None)
        edge_source_path = getattr(edge, "source_path", None)

        module_matches = (
            source_module is not None
            and edge_source_module == source_module
        )

        path_matches = False
        if normalized_source_path is not None and edge_source_path is not None:
            normalized_edge_path = Path(edge_source_path).as_posix()
            path_matches = (
                normalized_edge_path == normalized_source_path
                or normalized_edge_path.endswith(normalized_source_path)
                or normalized_source_path.endswith(normalized_edge_path)
            )

        if module_matches or path_matches:
            matching_edges.append(edge)

    return tuple(matching_edges)


def _module_names_match(alias_module: str | None, target_module: str | None) -> bool:
    """Return True when an import alias module can refer to a graph target."""

    if not alias_module or not target_module:
        return False

    stripped_alias_module = alias_module.lstrip(".")
    return (
        stripped_alias_module == target_module
        or target_module.endswith(f".{stripped_alias_module}")
        or stripped_alias_module.endswith(f".{target_module}")
    )


def _resolve_from_import_alias_with_edges(
    import_alias: ImportAlias,
    edges: tuple[object, ...],
) -> ImportAlias | None:
    """Resolve a from-import alias using matching local import graph edges."""

    for edge in edges:
        edge_imported_name = getattr(edge, "imported_name", None)
        edge_target_module = getattr(edge, "target_module", None)

        imported_name_matches = (
            import_alias.imported_name is not None
            and edge_imported_name == import_alias.imported_name
        )

        module_matches = _module_names_match(
            import_alias.module_name,
            edge_target_module,
        )

        if not imported_name_matches or not module_matches:
            continue

        resolved_path = getattr(edge, "target_path", None)
        qualified_name = f"{edge_target_module}.{import_alias.imported_name}"

        return replace(
            import_alias,
            qualified_name=qualified_name,
            module_name=edge_target_module,
            is_local=True,
            resolved_module=edge_target_module,
            resolved_path=Path(resolved_path).as_posix() if resolved_path is not None else None,
        )

    return None


def _resolve_plain_import_alias_with_edges(
    import_alias: ImportAlias,
    edges: tuple[object, ...],
) -> ImportAlias | None:
    """Resolve a plain import alias using matching local import graph edges."""

    for edge in edges:
        edge_target_module = getattr(edge, "target_module", None)
        if not _module_names_match(import_alias.module_name, edge_target_module):
            continue

        resolved_path = getattr(edge, "target_path", None)

        return replace(
            import_alias,
            qualified_name=edge_target_module,
            module_name=edge_target_module,
            is_local=True,
            resolved_module=edge_target_module,
            resolved_path=Path(resolved_path).as_posix() if resolved_path is not None else None,
        )

    return None


def resolve_import_aliases_with_import_graph(
    import_aliases: dict[str, ImportAlias],
    import_graph: object,
    *,
    source_module: str | None = None,
    source_path: str | Path | None = None,
) -> dict[str, ImportAlias]:
    """Resolve collected import aliases against local edges from an ImportGraph."""

    edges = _import_graph_edges_for_source(
        import_graph,
        source_module=source_module,
        source_path=source_path,
    )

    resolved_aliases: dict[str, ImportAlias] = {}

    for local_name, import_alias in sorted(import_aliases.items()):
        resolved_alias: ImportAlias | None = None

        if import_alias.import_type == "from":
            resolved_alias = _resolve_from_import_alias_with_edges(import_alias, edges)
        elif import_alias.import_type == "import":
            resolved_alias = _resolve_plain_import_alias_with_edges(import_alias, edges)

        if resolved_alias is None:
            resolved_aliases[local_name] = replace(import_alias, is_local=False)
        else:
            resolved_aliases[local_name] = resolved_alias

    return resolved_aliases

def build_call_graph_from_ast(
    tree: ast.AST,
    *,
    source_path: str | Path,
    module_name: str | None = None,
    symbol_index: object = None,
    import_graph: object = None,
) -> CallGraph:
    """Build a call graph from a parsed Python AST."""

    known_function_counts = _merge_counts(
        _collect_top_level_function_counts(tree),
        _function_counts_from_symbol_index(
            symbol_index,
            source_path=source_path,
        ),
    )
    known_method_counts = _merge_method_counts(
        _collect_class_method_counts(tree),
        _method_counts_from_symbol_index(
            symbol_index,
            source_path=source_path,
        ),
    )

    import_aliases = collect_import_aliases_from_ast(tree)
    if import_graph is not None:
        import_aliases = resolve_import_aliases_with_import_graph(
            import_aliases,
            import_graph,
            source_module=module_name,
            source_path=source_path,
        )

    visitor = PythonCallVisitor(
        source_path=source_path,
        module_name=module_name,
        known_class_names=_collect_class_names(tree),
        known_function_counts=known_function_counts,
        known_method_counts=known_method_counts,
        import_aliases=import_aliases,
    )
    visitor.visit(tree)
    return visitor.graph

def parse_calls_from_source(
    source: str,
    *,
    source_path: str | Path,
    module_name: str | None = None,
    symbol_index: object = None,
    import_graph: object = None,
) -> CallGraph:
    """Parse Python source text and return direct function call edges."""

    tree = ast.parse(source, filename=str(source_path))
    return build_call_graph_from_ast(
        tree,
        source_path=source_path,
        module_name=module_name,
        symbol_index=symbol_index,
        import_graph=import_graph,
    )


def parse_calls_from_file(
    source_path: str | Path,
    *,
    module_name: str | None = None,
    symbol_index: object = None,
    import_graph: object = None,
    encoding: str = "utf-8",
) -> CallGraph:
    """Read a Python file and return direct function call edges."""

    path = Path(source_path)
    source = path.read_text(encoding=encoding)
    return parse_calls_from_source(
        source,
        source_path=path,
        module_name=module_name,
        symbol_index=symbol_index,
        import_graph=import_graph,
    )


__all__ = [
    "CallEdge",
    "CallGraph",
    "collect_import_aliases_from_source",
    "collect_import_aliases_from_ast",
    "ImportAlias",
    "PythonCallVisitor",
    "build_call_graph_from_ast",
    "parse_calls_from_file",
    "resolve_import_aliases_with_import_graph",
    "parse_calls_from_source",
]

