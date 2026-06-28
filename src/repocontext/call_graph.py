"""Static call graph data structures.

This module contains the internal model used by later AST-based call analysis.
It intentionally does not parse Python code yet; it only stores, deduplicates,
sorts, groups, and serializes call graph edges.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import asdict, dataclass, field
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

class PythonCallVisitor(ast.NodeVisitor):
    """Collect function and method calls while tracking Python caller context."""

    def __init__(
        self,
        *,
        source_path: str | Path,
        module_name: str | None = None,
        known_class_names: set[str] | None = None,
        known_function_names: set[str] | None = None,
    ) -> None:
        self.source_path = Path(source_path).as_posix()
        self.module_name = module_name
        self.known_class_names = set(known_class_names or ())
        self.known_function_names = set(known_function_names or ())
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

        if callee_name in self.known_function_names:
            return self._qualify(callee_name), "local"

        return None, "unresolved"

    def _resolve_attribute_call(self, node: ast.Call) -> tuple[str | None, str]:
        """Resolve local class method calls when possible."""

        if not isinstance(node.func, ast.Attribute):
            return None, "unresolved"

        if self._is_self_method_call(node):
            class_name = ".".join(self._class_stack)
            return self._qualify(f"{class_name}.{node.func.attr}"), "local_method"

        cls_target = self._class_method_target(node)
        if cls_target is not None:
            return self._qualify(f"{cls_target}.{node.func.attr}"), "local_method"

        if self._is_chained_method_call(node):
            return None, "unresolved_method"

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


def _collect_class_names(tree: ast.AST) -> set[str]:
    """Return class names defined in a parsed Python AST."""

    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }


def _collect_top_level_function_names(tree: ast.AST) -> set[str]:
    """Return top-level function names defined in a parsed Python AST."""

    if not isinstance(tree, ast.Module):
        return set()

    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _function_names_from_symbol_index(
    symbol_index: object,
    *,
    source_path: str | Path,
) -> set[str]:
    """Return top-level function names for a file from an existing symbol index."""

    target_path = Path(source_path).as_posix()
    function_names: set[str] = set()

    for file_index in symbol_index or ():
        raw_file_path = getattr(file_index, "file_path", "")
        file_path = Path(str(raw_file_path)).as_posix()

        if file_path != target_path and not target_path.endswith(file_path) and not file_path.endswith(target_path):
            continue

        for symbol in getattr(file_index, "symbols", ()):
            if getattr(symbol, "kind", None) != "function":
                continue
            if getattr(symbol, "parent", None) is not None:
                continue

            name = getattr(symbol, "name", None)
            if isinstance(name, str) and name:
                function_names.add(name)

    return function_names


def build_call_graph_from_ast(
    tree: ast.AST,
    *,
    source_path: str | Path,
    module_name: str | None = None,
    symbol_index: object = None,
) -> CallGraph:
    """Build a call graph from a parsed Python AST."""

    known_function_names = _collect_top_level_function_names(tree)
    known_function_names.update(
        _function_names_from_symbol_index(
            symbol_index,
            source_path=source_path,
        )
    )

    visitor = PythonCallVisitor(
        source_path=source_path,
        module_name=module_name,
        known_class_names=_collect_class_names(tree),
        known_function_names=known_function_names,
    )
    visitor.visit(tree)
    return visitor.graph

def parse_calls_from_source(
    source: str,
    *,
    source_path: str | Path,
    module_name: str | None = None,
) -> CallGraph:
    """Parse Python source text and return direct function call edges."""

    tree = ast.parse(source, filename=str(source_path))
    return build_call_graph_from_ast(
        tree,
        source_path=source_path,
        module_name=module_name,
    )


def parse_calls_from_file(
    source_path: str | Path,
    *,
    module_name: str | None = None,
    encoding: str = "utf-8",
) -> CallGraph:
    """Read a Python file and return direct function call edges."""

    path = Path(source_path)
    source = path.read_text(encoding=encoding)
    return parse_calls_from_source(
        source,
        source_path=path,
        module_name=module_name,
    )


__all__ = [
    "CallEdge",
    "CallGraph",
    "PythonCallVisitor",
    "build_call_graph_from_ast",
    "parse_calls_from_file",
    "parse_calls_from_source",
]

