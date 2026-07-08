#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PANELS = ("roadmap", "milestone")
STATUSES = ("done", "active", "partial", "todo")
STATUS_SYMBOLS = {
    "done": "✓",
    "active": "■",
    "partial": "~",
    "todo": "!",
}
STATUS_COLORS = {
    "done": "\033[0;32m",
    "active": "\033[0;35m",
    "partial": "\033[1;33m",
    "todo": "\033[0;31m",
}
STATUS_PRIORITY = {
    "done": 10,
    "partial": 20,
    "todo": 30,
    "active": 40,
}
DIM = "\033[2m"
ACCENT = "\033[38;5;45m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass(frozen=True)
class MetaRecord:
    line_number: int
    data: dict[str, Any]


@dataclass(frozen=True)
class ProgressRange:
    panel: str
    status: str
    file: str
    start: int
    end: int


@dataclass(frozen=True)
class DisplayOptions:
    context: int = 4
    layout: str = "side-by-side"
    frame: bool = False


@dataclass(frozen=True)
class RenderLine:
    file: str
    number: int | None
    text: str
    status: str | None = None
    dim: bool = False
    header: bool = False


def _use_color() -> bool:
    return "NO_COLOR" not in os.environ


def _color(text: str, code: str) -> str:
    if not _use_color():
        return text
    return f"{code}{text}{RESET}"


def _parse_metadata(script_path: Path) -> list[MetaRecord]:
    records: list[MetaRecord] = []
    prefix = "# repodossier-meta:"

    for line_number, line in enumerate(script_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.startswith(prefix):
            continue

        raw = line[len(prefix):].strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid metadata JSON on line {line_number}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"metadata line {line_number} is not an object")
        records.append(MetaRecord(line_number=line_number, data=data))

    return records


def _markdown_heading_level(line: str) -> int | None:
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return None

    level = 0
    for char in stripped:
        if char != "#":
            break
        level += 1

    if level == 0 or level > 6:
        return None
    if len(stripped) > level and stripped[level] not in {" ", "\t"}:
        return None
    return level


def _find_anchor_line(lines: list[str], anchor: str) -> int:
    normalized = anchor.strip()

    for index, line in enumerate(lines, start=1):
        if line.strip() == normalized:
            return index

    for index, line in enumerate(lines, start=1):
        if normalized and normalized in line:
            return index

    raise ValueError(f"anchor not found: {anchor!r}")


def _resolve_anchor_range(file_path: Path, anchor: str) -> tuple[int, int]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    start = _find_anchor_line(lines, anchor)
    heading_level = _markdown_heading_level(lines[start - 1])

    if heading_level is None:
        return start, start

    end = len(lines)
    for index in range(start + 1, len(lines) + 1):
        candidate_level = _markdown_heading_level(lines[index - 1])
        if candidate_level is not None and candidate_level <= heading_level:
            end = index - 1
            break

    return start, max(start, min(end, start + 80))


def _records_to_progress(records: list[MetaRecord], *, repo_root: Path) -> tuple[list[ProgressRange], DisplayOptions]:
    ranges: list[ProgressRange] = []
    display = DisplayOptions()

    for record in records:
        data = record.data
        data_type = data.get("type")
        if data_type == "progress":
            file_name = str(data["file"])
            if "start" in data and "end" in data:
                start = int(data["start"])
                end = int(data["end"])
            else:
                start, end = _resolve_anchor_range(repo_root / file_name, str(data["anchor"]))

            ranges.append(
                ProgressRange(
                    panel=str(data["panel"]),
                    status=str(data["status"]),
                    file=file_name,
                    start=start,
                    end=end,
                )
            )
        elif data_type == "display":
            display = DisplayOptions(
                context=int(data.get("context", display.context)),
                layout=str(data.get("layout", display.layout)),
                frame=bool(data.get("frame", display.frame)),
            )

    return ranges, display


def _line_status(line_number: int, ranges: list[ProgressRange]) -> str | None:
    result: str | None = None
    result_priority = -1

    for progress in ranges:
        if not (progress.start <= line_number <= progress.end):
            continue

        priority = STATUS_PRIORITY.get(progress.status, 0)
        if priority >= result_priority:
            result = progress.status
            result_priority = priority

    return result


def _selected_line_numbers(ranges: list[ProgressRange], *, total_lines: int, context: int) -> list[int]:
    selected: set[int] = set()
    for progress in ranges:
        start = max(1, progress.start - context)
        end = min(total_lines, progress.end + context)
        selected.update(range(start, end + 1))
    return sorted(selected)


def _append_fill_lines(
    selected: list[int],
    *,
    total_lines: int,
    target_count: int,
) -> list[int]:
    if len(selected) >= target_count:
        return selected

    result = list(selected)
    seen = set(result)

    next_line = result[-1] + 1 if result else 1
    while len(result) < target_count and next_line <= total_lines:
        if next_line not in seen:
            result.append(next_line)
            seen.add(next_line)
        next_line += 1

    previous_line = result[0] - 1 if result else total_lines
    prepend: list[int] = []
    while len(result) + len(prepend) < target_count and previous_line >= 1:
        if previous_line not in seen:
            prepend.append(previous_line)
            seen.add(previous_line)
        previous_line -= 1

    return sorted(prepend) + result


def _panel_files(progress_ranges: list[ProgressRange]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for progress in progress_ranges:
        if progress.file not in seen:
            seen.add(progress.file)
            result.append(progress.file)
    return result


def _build_panel_stream(
    *,
    panel: str,
    ranges: list[ProgressRange],
    repo_root: Path,
    display: DisplayOptions,
    target_body_lines: int | None = None,
) -> list[RenderLine]:
    panel_ranges = [progress for progress in ranges if progress.panel == panel]
    if not panel_ranges:
        return []

    stream: list[RenderLine] = []
    for file_name in _panel_files(panel_ranges):
        file_path = repo_root / file_name
        lines = file_path.read_text(encoding="utf-8").splitlines()
        file_ranges = [progress for progress in panel_ranges if progress.file == file_name]
        line_numbers = _selected_line_numbers(file_ranges, total_lines=len(lines), context=display.context)
        if target_body_lines is not None:
            line_numbers = _append_fill_lines(line_numbers, total_lines=len(lines), target_count=target_body_lines)

        if stream:
            stream.append(RenderLine(file="", number=None, text="", dim=True))
        stream.append(RenderLine(file=file_name, number=None, text=f"📄 {file_name}", header=True))

        for number in line_numbers:
            text = lines[number - 1] if 1 <= number <= len(lines) else ""
            status = _line_status(number, file_ranges)
            stream.append(
                RenderLine(
                    file=file_name,
                    number=number,
                    text=text,
                    status=status,
                    dim=status is None,
                )
            )

    return stream


def _body_line_count(stream: list[RenderLine]) -> int:
    return sum(1 for line in stream if line.number is not None)


def _format_line(line: RenderLine, *, width: int) -> str:
    if line.number is None:
        if line.header:
            text = _color(line.text, BOLD)
        else:
            text = line.text
    else:
        symbol = STATUS_SYMBOLS.get(line.status or "", " ")
        prefix = f"{symbol}{line.number:>4}  "
        text = prefix + line.text
        if line.status in STATUS_COLORS:
            text = _color(text, STATUS_COLORS[line.status])
        elif line.dim:
            text = _color(text, DIM)

    if len(text) > width:
        visible_padding = 1 if _use_color() else 0
        text = text[: max(1, width - visible_padding - 1)] + "…"
    return text


def _plain_len(text: str) -> int:
    length = 0
    in_escape = False
    for char in text:
        if char == "\033":
            in_escape = True
            continue
        if in_escape:
            if char == "m":
                in_escape = False
            continue
        length += 1
    return length


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _plain_len(text))


def _render_side_by_side(streams: dict[str, list[RenderLine]], *, terminal_width: int) -> list[str]:
    gap = "  "
    column_width = max(44, (terminal_width - len(gap)) // 2)

    left_title = _color("ROADMAP", ACCENT + BOLD)
    right_title = _color("MILESTONE", ACCENT + BOLD)
    lines = [
        _pad(left_title, column_width) + gap + right_title,
        "─" * min(column_width, 48) + gap + "─" * min(column_width, 48),
    ]

    left = streams.get("roadmap", [])
    right = streams.get("milestone", [])
    rows = max(len(left), len(right))

    for index in range(rows):
        left_text = _format_line(left[index], width=column_width) if index < len(left) else ""
        right_text = _format_line(right[index], width=column_width) if index < len(right) else ""
        lines.append(_pad(left_text, column_width) + gap + right_text)

    return lines


def _render_stacked(streams: dict[str, list[RenderLine]], *, terminal_width: int) -> list[str]:
    lines: list[str] = []
    width = max(60, terminal_width)

    for panel in PANELS:
        stream = streams.get(panel, [])
        if not stream:
            continue
        if lines:
            lines.append("")
        lines.append(_color(panel.upper(), ACCENT + BOLD))
        lines.append("─" * min(width, 96))
        lines.extend(_format_line(line, width=width) for line in stream)

    return lines


def render_progress_context(script_path: Path, repo_root: Path) -> str:
    records = _parse_metadata(script_path)
    ranges, display = _records_to_progress(records, repo_root=repo_root)

    initial_streams = {
        panel: _build_panel_stream(panel=panel, ranges=ranges, repo_root=repo_root, display=display)
        for panel in PANELS
    }

    target_body_lines = max((_body_line_count(stream) for stream in initial_streams.values()), default=0)
    streams = {
        panel: _build_panel_stream(
            panel=panel,
            ranges=ranges,
            repo_root=repo_root,
            display=display,
            target_body_lines=target_body_lines,
        )
        for panel in PANELS
    }

    terminal_width = shutil.get_terminal_size((140, 24)).columns
    lines = [_color("c · Progress Context", ACCENT + BOLD)]

    if display.layout == "stacked":
        lines.extend(_render_stacked(streams, terminal_width=terminal_width))
    else:
        lines.extend(_render_side_by_side(streams, terminal_width=terminal_width))

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render RepoDossier patch progress metadata.")
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        print(render_progress_context(args.script, args.repo))
    except Exception as exc:
        print(f"Progress context unavailable: {exc}")
        return 10
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
