from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import re

from .bash_symbols import BashFunction
from .bash_symbols import discover_bash_functions


_BASH_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_BASH_COMMAND_SEPARATORS_RE = re.compile(r"\s*(?:&&|\|\||[;|])\s*")

_BASH_IGNORED_COMMANDS = {
    "case",
    "do",
    "done",
    "elif",
    "else",
    "esac",
    "fi",
    "for",
    "function",
    "if",
    "in",
    "select",
    "then",
    "until",
    "while",
    "return",
    "exit",
    "local",
    "declare",
    "export",
    "readonly",
    "typeset",
    "echo",
    "printf",
    "cd",
    "pwd",
    "test",
    "source",
    "command",
    "builtin",
    "true",
    "false",
    "grep",
    "sed",
    "awk",
    "cat",
    "tee",
}

_BASH_LEADING_KEYWORDS = {
    "if",
    "elif",
    "while",
    "until",
    "then",
    "do",
    "else",
}

_BASH_PREFIX_WORDS = {
    "!",
    "time",
    "command",
    "builtin",
}


@dataclass(frozen=True)
class BashCallEdge:
    """A statically discovered Bash function call edge."""

    caller: str
    callee: str
    call_line: int
    caller_line: int
    callee_line: int | None = None
    caller_path: str | None = None
    callee_path: str | None = None


def discover_bash_call_graph(
    content: str,
    path: str | Path | None = None,
    known_functions: list[BashFunction] | None = None,
) -> list[BashCallEdge]:
    """Discover simple Bash function call edges without executing shell code."""

    local_functions = discover_bash_functions(content, path=path)
    known = known_functions if known_functions is not None else local_functions
    known_by_name = _known_function_map(known)

    return _discover_edges_for_functions(
        content=content,
        functions=local_functions,
        known_by_name=known_by_name,
    )


def discover_bash_call_graph_for_files(
    files: Mapping[str | Path, str],
) -> list[BashCallEdge]:
    """Discover Bash function call edges across multiple shell source files."""

    functions_by_path: dict[str, list[BashFunction]] = {}
    all_functions: list[BashFunction] = []

    for path, content in files.items():
        path_text = str(path)
        functions = discover_bash_functions(content, path=path_text)
        functions_by_path[path_text] = functions
        all_functions.extend(functions)

    known_by_name = _known_function_map(all_functions)

    edges: list[BashCallEdge] = []
    for path, content in files.items():
        edges.extend(
            _discover_edges_for_functions(
                content=content,
                functions=functions_by_path[str(path)],
                known_by_name=known_by_name,
            )
        )

    return _deduplicate_edges(edges)


def _known_function_map(functions: list[BashFunction]) -> dict[str, BashFunction]:
    known_by_name: dict[str, BashFunction] = {}

    for function in functions:
        known_by_name.setdefault(function.name, function)

    return known_by_name


def _discover_edges_for_functions(
    content: str,
    functions: list[BashFunction],
    known_by_name: dict[str, BashFunction],
) -> list[BashCallEdge]:
    lines = _mask_bash_call_graph_heredoc_lines(content.splitlines())
    edges: list[BashCallEdge] = []

    for caller in functions:
        for line_number, code_line in _function_code_lines(lines, caller):
            for command_name in _candidate_command_names(code_line):
                callee = known_by_name.get(command_name)
                if callee is None:
                    continue

                edges.append(
                    BashCallEdge(
                        caller=caller.name,
                        callee=callee.name,
                        call_line=line_number,
                        caller_line=caller.start_line,
                        callee_line=callee.start_line,
                        caller_path=caller.path,
                        callee_path=callee.path,
                    )
                )

    return _deduplicate_edges(edges)


def _deduplicate_edges(edges: list[BashCallEdge]) -> list[BashCallEdge]:
    seen: set[tuple[str | None, str, str | None, str, int]] = set()
    unique: list[BashCallEdge] = []

    for edge in edges:
        key = (
            edge.caller_path,
            edge.caller,
            edge.callee_path,
            edge.callee,
            edge.call_line,
        )
        if key in seen:
            continue

        seen.add(key)
        unique.append(edge)

    return unique


def _function_code_lines(
    lines: list[str],
    function: BashFunction,
):
    start = max(function.start_line - 1, 0)
    end = min(function.end_line, len(lines))

    for index in range(start, end):
        line = lines[index]

        if index == start and "{" in line:
            line = line.split("{", 1)[1]

        if index == end - 1 and "}" in line:
            line = line.rsplit("}", 1)[0]

        yield index + 1, line


def _candidate_command_names(line: str) -> list[str]:
    code_line = _replace_quoted_text_with_spaces(_strip_unquoted_comment(line))
    commands: list[str] = []

    for segment in _BASH_COMMAND_SEPARATORS_RE.split(code_line):
        command = _candidate_command_from_segment(segment)
        if command is not None:
            commands.append(command)

    return commands


def _candidate_command_from_segment(segment: str) -> str | None:
    stripped = segment.strip()
    if not stripped:
        return None

    stripped = stripped.strip("(){} ")
    if not stripped:
        return None

    tokens = _BASH_NAME_RE.findall(stripped)
    if not tokens:
        return None

    index = 0

    if tokens[index] in _BASH_LEADING_KEYWORDS:
        index += 1

    while index < len(tokens) and tokens[index] in _BASH_PREFIX_WORDS:
        index += 1

    if index >= len(tokens):
        return None

    command = tokens[index]
    if command in _BASH_IGNORED_COMMANDS:
        return None

    return command


def _strip_unquoted_comment(line: str) -> str:
    result: list[str] = []
    single_quoted = False
    double_quoted = False
    escaped = False

    for char in line:
        if escaped:
            result.append(char)
            escaped = False
            continue

        if char == "\\":
            result.append(char)
            escaped = True
            continue

        if char == "'" and not double_quoted:
            single_quoted = not single_quoted
            result.append(char)
            continue

        if char == '"' and not single_quoted:
            double_quoted = not double_quoted
            result.append(char)
            continue

        if char == "#" and not single_quoted and not double_quoted:
            break

        result.append(char)

    return "".join(result)


def _replace_quoted_text_with_spaces(line: str) -> str:
    result: list[str] = []
    single_quoted = False
    double_quoted = False
    escaped = False

    for char in line:
        if escaped:
            result.append(" ")
            escaped = False
            continue

        if char == "\\":
            result.append(" ")
            escaped = True
            continue

        if char == "'" and not double_quoted:
            single_quoted = not single_quoted
            result.append(" ")
            continue

        if char == '"' and not single_quoted:
            double_quoted = not double_quoted
            result.append(" ")
            continue

        if single_quoted or double_quoted:
            result.append(" ")
            continue

        result.append(char)

    return "".join(result)


def _mask_bash_call_graph_heredoc_lines(lines: list[str]) -> list[str]:
    """Blank heredoc bodies so fake calls inside heredocs are ignored."""

    masked: list[str] = []
    active_delimiter: str | None = None

    for line in lines:
        if active_delimiter is not None:
            if line.strip() == active_delimiter:
                active_delimiter = None
            masked.append("")
            continue

        delimiter = _extract_bash_call_graph_heredoc_delimiter(line)
        masked.append(line)

        if delimiter is not None:
            active_delimiter = delimiter

    return masked


def _extract_bash_call_graph_heredoc_delimiter(line: str) -> str | None:
    code_line = _strip_unquoted_comment(line)
    index = code_line.find("<<")

    if index == -1:
        return None

    index += 2
    if index < len(code_line) and code_line[index] == "-":
        index += 1

    while index < len(code_line) and code_line[index].isspace():
        index += 1

    if index >= len(code_line):
        return None

    quote = code_line[index] if code_line[index] in {"'", '"'} else ""
    if quote:
        index += 1
        end = code_line.find(quote, index)
        if end == -1:
            return None
        delimiter = code_line[index:end]
    else:
        end = index
        while end < len(code_line) and not code_line[end].isspace() and code_line[end] not in ";|&":
            end += 1
        delimiter = code_line[index:end]

    delimiter = delimiter.strip()
    return delimiter or None

