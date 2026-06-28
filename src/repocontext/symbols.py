"""Symbol extraction helpers for RepoContext.

This module provides static symbol extraction for Python source files.
It intentionally does not execute project code.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
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


def _extract_top_level_functions(
    tree: ast.Module,
    *,
    file_path: str,
) -> list[SymbolInfo]:
    """Extract top-level function symbols from a parsed Python module.

    Nested functions and methods are intentionally ignored in this MVP
    step. Methods are handled separately by Method Discovery.
    """

    symbols: list[SymbolInfo] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(_symbol_from_function_node(node, file_path=file_path))

    return symbols


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

    symbols = _extract_top_level_functions(tree, file_path=file_path_str)
    return FileSymbolIndex(file_path=file_path_str, symbols=symbols)
