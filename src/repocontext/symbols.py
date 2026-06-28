"""Symbol extraction helpers for RepoContext.

This module provides the foundation for static symbol extraction.
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


def extract_symbols_from_file(path: str | Path) -> FileSymbolIndex:
    """Parse one Python file and return its symbol extraction result.

    Milestone 5.1 only establishes the stable parsing entrypoint and
    error handling. Actual function, class, and method discovery is
    implemented in the following milestone steps.
    """

    file_path = Path(path)

    try:
        source = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return FileSymbolIndex(
            file_path=str(file_path),
            errors=[_format_exception(error)],
        )
    except OSError as error:
        return FileSymbolIndex(
            file_path=str(file_path),
            errors=[_format_exception(error)],
        )

    try:
        ast.parse(source, filename=str(file_path))
    except SyntaxError as error:
        return FileSymbolIndex(
            file_path=str(file_path),
            errors=[_format_syntax_error(error)],
        )

    return FileSymbolIndex(file_path=str(file_path))
