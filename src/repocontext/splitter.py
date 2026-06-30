"""Reusable text splitting helpers for multi-part exports."""

from __future__ import annotations

import re
from typing import Literal


SplitStrategy = Literal["plain", "heading"]

VALID_SPLIT_STRATEGIES = ("plain", "heading")

_MARKDOWN_HEADING_RE = re.compile(r"^ {0,3}#{1,6}\s+\S")


def split_text(text: str, max_chars: int, strategy: SplitStrategy | str = "heading") -> list[str]:
    """Split text into deterministic parts without losing content.

    The splitter returns raw content parts. It does not add part headers; that is
    the responsibility of the output writer.

    With strategy "plain", the text is split at fixed character boundaries.

    With strategy "heading", the splitter prefers Markdown heading boundaries
    where possible and falls back to plain splitting for oversized sections.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    normalized_max_chars = _validate_max_chars(max_chars)
    normalized_strategy = _validate_strategy(strategy)

    if text == "":
        return [""]

    if len(text) <= normalized_max_chars:
        return [text]

    if normalized_strategy == "plain":
        return _plain_split(text, normalized_max_chars)

    return _heading_split(text, normalized_max_chars)


def _validate_max_chars(max_chars: int) -> int:
    if isinstance(max_chars, bool) or not isinstance(max_chars, int):
        raise ValueError("max_chars must be a positive integer")

    if max_chars <= 0:
        raise ValueError("max_chars must be a positive integer")

    return max_chars


def _validate_strategy(strategy: str) -> str:
    if not isinstance(strategy, str):
        raise ValueError("strategy must be one of: plain, heading")

    normalized = strategy.strip().lower()
    if normalized not in VALID_SPLIT_STRATEGIES:
        raise ValueError("strategy must be one of: plain, heading")

    return normalized


def _plain_split(text: str, max_chars: int) -> list[str]:
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def _split_oversized_heading_section(section: str, max_chars: int) -> list[str]:
    """Split an oversized heading section while preserving its heading if possible."""

    lines = section.splitlines(keepends=True)
    if not lines:
        return [""]

    first_line = lines[0]
    if _is_markdown_heading(first_line) and len(first_line) <= max_chars:
        rest = "".join(lines[1:])
        if rest:
            return [first_line, *_plain_split(rest, max_chars)]
        return [first_line]

    return _plain_split(section, max_chars)


def _heading_split(text: str, max_chars: int) -> list[str]:
    sections = _split_into_heading_sections(text)
    parts: list[str] = []
    current = ""

    for section in sections:
        if section == "":
            continue

        if len(section) > max_chars:
            if current:
                parts.append(current)
                current = ""
            parts.extend(_split_oversized_heading_section(section, max_chars))
            continue

        if not current:
            current = section
            continue

        if len(current) + len(section) <= max_chars:
            current += section
            continue

        parts.append(current)
        current = section

    if current or not parts:
        parts.append(current)

    return parts


def _split_into_heading_sections(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    sections: list[str] = []
    current_lines: list[str] = []

    for line in lines:
        if _is_markdown_heading(line) and current_lines:
            sections.append("".join(current_lines))
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append("".join(current_lines))

    return sections


def _is_markdown_heading(line: str) -> bool:
    return bool(_MARKDOWN_HEADING_RE.match(line))
