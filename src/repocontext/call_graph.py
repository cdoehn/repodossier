"""Static call graph data structures.

This module contains the internal model used by later AST-based call analysis.
It intentionally does not parse Python code yet; it only stores, deduplicates,
sorts, groups, and serializes call graph edges.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
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
