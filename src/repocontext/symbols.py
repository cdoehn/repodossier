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


def _extract_bash_symbols_for_symbol_index(
    path: object,
    content: str | bytes | None = None,
):
    """Return Bash function symbols for shell sources, or None for other files."""

    if not _is_bash_symbol_source(path, content):
        return None

    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    if content is None:
        try:
            content = Path(path).read_text(encoding="utf-8", errors="ignore")
        except (OSError, TypeError, ValueError):
            content = ""

    from .bash_symbols import discover_bash_functions

    return [
        _build_bash_symbol_for_index(function)
        for function in discover_bash_functions(content, path=path)
    ]


def _is_bash_symbol_source(path: object, content: str | bytes | None = None) -> bool:
    path_text = str(path).lower()

    if path_text.endswith((".sh", ".bash")):
        return True

    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    if not content:
        return False

    first_line = content.splitlines()[0].strip() if content.splitlines() else ""
    if not first_line.startswith("#!"):
        return False

    parts = first_line[2:].strip().lower().replace("\\t", " ").split()
    if not parts:
        return False

    executable = parts[0].rsplit("/", 1)[-1]
    if executable in {"bash", "sh"}:
        return True

    if executable == "env":
        for part in parts[1:]:
            if part.startswith("-"):
                continue
            if part.rsplit("/", 1)[-1] in {"bash", "sh"}:
                return True

    return False




def _build_bash_symbol_index_result(path: object, symbols: list[object]):
    """Return Bash symbols in the same container shape as the symbol extractor."""

    result_class = globals().get("FileSymbolIndex")
    if result_class is None:
        return symbols

    return _construct_bash_symbol_index(result_class, path, symbols)


def _construct_bash_symbol_index(result_class, path: object, symbols: list[object]):
    from dataclasses import MISSING, fields, is_dataclass
    from inspect import Parameter, signature

    values = {}

    if is_dataclass(result_class):
        definitions = [
            (field.name, field.default, field.default_factory)
            for field in fields(result_class)
        ]
    else:
        definitions = [
            (name, parameter.default, MISSING)
            for name, parameter in signature(result_class).parameters.items()
            if name != "self"
        ]

    annotations = getattr(result_class, "__annotations__", {})

    for name, default, default_factory in definitions:
        value = _bash_symbol_index_field_value(name, path, symbols, annotations.get(name))
        if value is not _MISSING_BASH_SYMBOL_FIELD:
            values[name] = value
            continue

        has_default = default is not MISSING and default is not Parameter.empty
        has_factory = default_factory is not MISSING

        if has_default or has_factory:
            continue

        values[name] = _bash_symbol_fallback_value(name, annotations.get(name))

    return result_class(**values)


def _bash_symbol_index_field_value(name: str, path: object, symbols: list[object], annotation):
    lower = name.lower()

    if lower in {"path", "file", "filepath", "file_path", "relative_path", "source_path"}:
        return str(path)

    if lower in {"symbols", "items", "entries", "all_symbols"}:
        return symbols

    if lower in {"functions", "function_symbols"}:
        return symbols

    if lower in {"classes", "class_symbols", "methods", "method_symbols"}:
        return []

    if lower in {"symbol_count", "total_symbols", "count"}:
        return len(symbols)

    if lower in {"language", "source_language"}:
        return _bash_language_value()

    if lower in {"errors", "warnings"}:
        return []

    if lower in {"has_symbols", "contains_symbols"}:
        return bool(symbols)

    return _MISSING_BASH_SYMBOL_FIELD

def _build_bash_symbol_for_index(function):
    from dataclasses import MISSING, fields, is_dataclass
    from inspect import Parameter, signature
    from pathlib import Path

    symbol_class = SymbolInfo
    values = {}

    if is_dataclass(symbol_class):
        definitions = [
            (field.name, field.default, field.default_factory)
            for field in fields(symbol_class)
        ]
    else:
        definitions = [
            (name, parameter.default, MISSING)
            for name, parameter in signature(symbol_class).parameters.items()
            if name != "self"
        ]

    annotations = getattr(symbol_class, "__annotations__", {})

    for name, default, default_factory in definitions:
        value = _bash_symbol_field_value(name, function, annotations.get(name))
        if value is not _MISSING_BASH_SYMBOL_FIELD:
            values[name] = value
            continue

        has_default = default is not MISSING and default is not Parameter.empty
        has_factory = default_factory is not MISSING

        if has_default or has_factory:
            continue

        values[name] = _bash_symbol_fallback_value(name, annotations.get(name))

    return symbol_class(**values)


_MISSING_BASH_SYMBOL_FIELD = object()


def _bash_symbol_field_value(name: str, function, annotation):
    lower = name.lower()

    if lower == "name":
        return function.name

    if lower in {"kind", "type", "symbol_type", "category"}:
        return _bash_function_kind_value()

    if lower == "language":
        return _bash_language_value()

    if lower in {"path", "file", "filepath", "file_path", "relative_path", "source_path"}:
        return function.path or ""

    if lower in {"line", "lineno", "line_number", "start_line"}:
        return function.start_line

    if lower in {"end_line", "stop_line"}:
        return function.end_line

    if lower in {"body_start_line", "body_start"}:
        return function.body_start_line

    if lower in {"body_end_line", "body_end"}:
        return function.body_end_line

    if lower == "signature":
        return function.signature

    if lower in {"qualname", "qualified_name", "full_name"}:
        return function.name

    if lower in {"parent", "container", "scope", "module", "class_name"}:
        return None

    if lower in {"children", "members", "decorators", "calls"}:
        return []

    return _MISSING_BASH_SYMBOL_FIELD


def _bash_function_kind_value():
    for enum_name in ("SymbolKind", "SymbolType", "SymbolCategory", "Kind"):
        enum_class = globals().get(enum_name)
        if enum_class is None:
            continue

        for member_name in ("FUNCTION", "Function", "function"):
            if hasattr(enum_class, member_name):
                return getattr(enum_class, member_name)

    return "function"


def _bash_language_value():
    for enum_name in ("Language", "SourceLanguage"):
        enum_class = globals().get(enum_name)
        if enum_class is None:
            continue

        for member_name in ("BASH", "SHELL", "SH", "Bash", "Shell", "bash", "shell", "sh"):
            if hasattr(enum_class, member_name):
                return getattr(enum_class, member_name)

    return "bash"


def _bash_symbol_fallback_value(name: str, annotation):
    lower = name.lower()
    annotation_text = str(annotation).lower()

    if "line" in lower or "count" in lower or annotation_text in {"<class 'int'>", "int"}:
        return 0

    if lower.startswith("is_") or annotation_text in {"<class 'bool'>", "bool"}:
        return False

    if any(marker in lower for marker in ("children", "members", "decorators", "calls")):
        return []

    if "list" in annotation_text or "sequence" in annotation_text:
        return []

    if "tuple" in annotation_text:
        return ()

    if "set" in annotation_text:
        return set()

    if annotation_text in {"<class 'str'>", "str"}:
        return ""

    return None


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


def _format_symbol_line(symbol: SymbolInfo) -> str:
    """Return one human-readable symbol index line."""

    if symbol.kind == "method" and symbol.parent:
        display_name = f"{symbol.parent}.{symbol.name}"
    else:
        display_name = symbol.name

    return f"  {symbol.kind} {display_name}:{symbol.line_start}"


def format_symbol_index(symbol_index: Iterable[FileSymbolIndex]) -> str:
    """Format a symbol index for later human-readable exports.

    Files are grouped by path. Files without symbols are intentionally
    omitted to keep future exports compact.
    """

    lines: list[str] = []

    for file_index in sorted(symbol_index, key=lambda index: index.file_path):
        symbols = _sort_symbols(file_index.symbols)

        if not symbols:
            continue

        lines.append(file_index.file_path)
        lines.extend(_format_symbol_line(symbol) for symbol in symbols)

    return "\n".join(lines)


def extract_symbols_from_file(path: str | Path) -> FileSymbolIndex:
    """Parse one Python file and return its symbol extraction result.

    This function performs static parsing only. It does not import or
    execute the analyzed file.
    """
    bash_symbols = _extract_bash_symbols_for_symbol_index(path, None)
    if bash_symbols is not None:
        return _build_bash_symbol_index_result(path, bash_symbols)


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
