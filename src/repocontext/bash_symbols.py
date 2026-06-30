from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


BASH_FUNCTION_NAME_RE = r"[A-Za-z_][A-Za-z0-9_]*"

_FUNCTION_DEFINITION_RE = re.compile(
    r"^\s*(?:function\s+)?"
    rf"(?P<name>{BASH_FUNCTION_NAME_RE})"
    r"\s*(?:\(\s*\))?\s*\{(?:\s|$)"
)

_RESERVED_FUNCTION_NAMES = {
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
    "echo",
    "printf",
    "test",
}


@dataclass(frozen=True)
class BashFunction:
    """A statically discovered Bash function."""

    name: str
    start_line: int
    end_line: int
    body_start_line: int
    body_end_line: int
    path: str | None = None

    @property
    def symbol_type(self) -> str:
        return "function"

    @property
    def language(self) -> str:
        return "bash"

    @property
    def signature(self) -> str:
        return f"{self.name}()"


def discover_bash_functions(
    content: str,
    path: str | Path | None = None,
) -> list[BashFunction]:
    """Discover Bash function definitions without executing shell code."""

    path_text = str(path) if path is not None else None
    lines = _mask_bash_heredoc_lines(content.splitlines())
    functions: list[BashFunction] = []

    line_index = 0
    while line_index < len(lines):
        raw_line = lines[line_index]
        code_line = _strip_unquoted_comment(raw_line)
        match = _FUNCTION_DEFINITION_RE.match(code_line)

        if match is None:
            line_index += 1
            continue

        name = match.group("name")
        if name in _RESERVED_FUNCTION_NAMES:
            line_index += 1
            continue

        start_line = line_index + 1
        end_index = _find_function_end(lines, line_index)
        end_line = end_index + 1

        functions.append(
            BashFunction(
                name=name,
                start_line=start_line,
                end_line=end_line,
                body_start_line=start_line,
                body_end_line=end_line,
                path=path_text,
            )
        )

        line_index = max(end_index + 1, line_index + 1)

    return functions


def extract_bash_functions(
    content: str,
    path: str | Path | None = None,
) -> list[BashFunction]:
    """Compatibility alias for Bash function discovery."""

    return discover_bash_functions(content, path=path)


def _find_function_end(lines: list[str], start_index: int) -> int:
    balance = 0
    saw_opening_brace = False

    for line_index in range(start_index, len(lines)):
        code_line = _strip_unquoted_comment(lines[line_index])
        for char in _iter_code_chars(code_line):
            if char == "{":
                balance += 1
                saw_opening_brace = True
            elif char == "}":
                balance -= 1

        if saw_opening_brace and balance <= 0:
            return line_index

    return start_index


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


def _iter_code_chars(line: str):
    single_quoted = False
    double_quoted = False
    escaped = False

    for char in line:
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if char == "'" and not double_quoted:
            single_quoted = not single_quoted
            continue

        if char == '"' and not single_quoted:
            double_quoted = not double_quoted
            continue

        if single_quoted or double_quoted:
            continue

        yield char


def _mask_bash_heredoc_lines(lines: list[str]) -> list[str]:
    """Blank heredoc bodies so fake functions inside heredocs are ignored."""

    masked: list[str] = []
    active_delimiter: str | None = None

    for line in lines:
        if active_delimiter is not None:
            if line.strip() == active_delimiter:
                active_delimiter = None
            masked.append("")
            continue

        delimiter = _extract_bash_heredoc_delimiter(line)
        masked.append(line)

        if delimiter is not None:
            active_delimiter = delimiter

    return masked


def _extract_bash_heredoc_delimiter(line: str) -> str | None:
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

