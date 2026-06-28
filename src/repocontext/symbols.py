"""Symbol extraction helpers for RepoContext.

This module provides static symbol extraction for Python source files.
It intentionally does not execute project code.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field, replace
from collections.abc import Iterable
from pathlib import Path


@dataclass(frozen=True)
class SymbolInfo:
    """Information about a discovered source-code symbol."""

    name: str
    kind: str
    file_path: str
    line_start: int
    line_end: int | None = None
    parent: str | None = None


@dataclass(frozen=True)
class FileSymbolIndex:
    """Symbol extraction result for one file."""

    file_path: str
    symbols: list[SymbolInfo] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _format_syntax_error(error: SyntaxError) -> str:
    """Return a compact, stable syntax error message."""

    location = ""
    if error.lineno is not None:
        location = f" at line {error.lineno}"
        if error.offset is not None:
            location += f", column {error.offset}"

    message = error.msg or str(error)
    return f"SyntaxError{location}: {message}"


def _format_exception(error: BaseException) -> str:
    """Return a compact error message for extraction failures."""

    return f"{type(error).__name__}: {error}"


def _symbol_from_function_node(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    file_path: str,
) -> SymbolInfo:
    """Create symbol information for a top-level function node."""

    return SymbolInfo(
        name=node.name,
        kind="function",
        file_path=file_path,
        line_start=node.lineno,
        line_end=getattr(node, "end_lineno", None),
    )


def _symbol_from_class_node(
    node: ast.ClassDef,
    *,
    file_path: str,
) -> SymbolInfo:
    """Create symbol information for a top-level class node."""

    return SymbolInfo(
        name=node.name,
        kind="class",
        file_path=file_path,
        line_start=node.lineno,
        line_end=getattr(node, "end_lineno", None),
    )


def _symbol_from_method_node(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    file_path: str,
    parent: str,
) -> SymbolInfo:
    """Create symbol information for a direct class method node."""

    return SymbolInfo(
        name=node.name,
        kind="method",
        file_path=file_path,
        line_start=node.lineno,
        line_end=getattr(node, "end_lineno", None),
        parent=parent,
    )


def _extract_methods_from_class_node(
    node: ast.ClassDef,
    *,
    file_path: str,
) -> list[SymbolInfo]:
    """Extract direct methods from a class node.

    Nested classes and nested functions remain intentionally ignored for
    the Milestone 5 MVP. Only direct FunctionDef and AsyncFunctionDef
    children of the class body are treated as methods.
    """

    methods: list[SymbolInfo] = []

    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(
                _symbol_from_method_node(
                    child,
                    file_path=file_path,
                    parent=node.name,
                )
            )

    return methods


def _extract_top_level_symbols(
    tree: ast.Module,
    *,
    file_path: str,
) -> list[SymbolInfo]:
    """Extract top-level symbols from a Python module.

    Top-level functions and classes are extracted in source order. Direct
    methods are emitted immediately after their parent class symbol.
    Nested functions and nested classes remain intentionally ignored.
    """

    symbols: list[SymbolInfo] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(_symbol_from_function_node(node, file_path=file_path))
        elif isinstance(node, ast.ClassDef):
            symbols.append(_symbol_from_class_node(node, file_path=file_path))
            symbols.extend(_extract_methods_from_class_node(node, file_path=file_path))

    return symbols


def _is_python_file(path: Path) -> bool:
    """Return True when path should be parsed as Python source."""

    return path.suffix == ".py"


def _sort_symbols(symbols: list[SymbolInfo]) -> list[SymbolInfo]:
    """Return symbols in a deterministic order."""

    return sorted(
        symbols,
        key=lambda symbol: (
            symbol.line_start,
            symbol.kind,
            symbol.name,
            symbol.parent or "",
        ),
    )


def _display_path(path: Path, *, base_path: str | Path | None = None) -> str:
    """Return a stable display path for symbol index output.

    When base_path is given and path is inside it, the returned path is
    relative and POSIX-style. Otherwise the original path string is kept.
    """

    if base_path is None:
        return str(path)

    try:
        return path.resolve().relative_to(Path(base_path).resolve()).as_posix()
    except (OSError, ValueError):
        return str(path)


def _with_file_path(index: FileSymbolIndex, file_path: str) -> FileSymbolIndex:
    """Return an index whose file path is applied to all contained symbols."""

    return FileSymbolIndex(
        file_path=file_path,
        symbols=[
            replace(symbol, file_path=file_path)
            for symbol in _sort_symbols(index.symbols)
        ],
        errors=list(index.errors),
    )


def build_symbol_index(
    files: Iterable[str | Path],
    *,
    base_path: str | Path | None = None,
) -> list[FileSymbolIndex]:
    """Build a deterministic symbol index for a collection of files.

    Only Python files are analyzed. Non-Python paths are skipped.
    Each Python file produces one FileSymbolIndex, including files that
    contain syntax errors or cannot be read, so one bad file does not
    abort the full index build.

    If base_path is provided, file paths in the returned index are made
    relative to that base path when possible.
    """

    python_files = sorted(
        (Path(file) for file in files if _is_python_file(Path(file))),
        key=lambda path: _display_path(path, base_path=base_path),
    )

    indexes: list[FileSymbolIndex] = []

    for path in python_files:
        display_path = _display_path(path, base_path=base_path)
        indexes.append(_with_file_path(extract_symbols_from_file(path), display_path))

    return sorted(indexes, key=lambda index: index.file_path)


def extract_symbols_from_file(path: str | Path) -> FileSymbolIndex:
    """Parse one Python file and return its symbol extraction result.

    This function performs static parsing only. It does not import or
    execute the analyzed file.
    """

    file_path = Path(path)
    file_path_str = str(file_path)

    try:
        source = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return FileSymbolIndex(
            file_path=file_path_str,
            errors=[_format_exception(error)],
        )
    except OSError as error:
        return FileSymbolIndex(
            file_path=file_path_str,
            errors=[_format_exception(error)],
        )

    try:
        tree = ast.parse(source, filename=file_path_str)
    except SyntaxError as error:
        return FileSymbolIndex(
            file_path=file_path_str,
            errors=[_format_syntax_error(error)],
        )

    symbols = _sort_symbols(_extract_top_level_symbols(tree, file_path=file_path_str))
    return FileSymbolIndex(file_path=file_path_str, symbols=symbols)
