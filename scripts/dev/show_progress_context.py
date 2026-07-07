#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_patch_metadata import MetaRecord, parse_metadata_lines, validate_records


STATUS_PRIORITY = {"todo": 1, "done": 2, "partial": 3, "active": 4}
STATUS_ICON = {"done": "🟩", "active": "🟪", "partial": "🟨", "todo": "🟥", None: "  "}
STATUS_COLOR = {
    "done": "\033[0;32m",
    "active": "\033[0;35m",
    "partial": "\033[1;33m",
    "todo": "\033[0;31m",
}
RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
ACCENT = "\033[38;5;45m"


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


def _use_color() -> bool:
    return not os.environ.get("NO_COLOR")


def _color(text: str, status: str | None = None, *, bold: bool = False, dim: bool = False) -> str:
    if not _use_color():
        return text
    prefix = ""
    if bold:
        prefix += BOLD
    if dim:
        prefix += DIM
    if status:
        prefix += STATUS_COLOR.get(status, "")
    return f"{prefix}{text}{RESET}" if prefix else text


def _accent(text: str) -> str:
    if not _use_color():
        return text
    return f"{ACCENT}{BOLD}{text}{RESET}"


def _records_to_progress(records: list[MetaRecord]) -> tuple[list[ProgressRange], DisplayOptions]:
    ranges: list[ProgressRange] = []
    display = DisplayOptions()

    for record in records:
        data = record.data
        if data.get("type") == "progress":
            ranges.append(
                ProgressRange(
                    panel=str(data["panel"]),
                    status=str(data["status"]),
                    file=str(data["file"]),
                    start=int(data["start"]),
                    end=int(data["end"]),
                )
            )
        elif data.get("type") == "display":
            display = DisplayOptions(
                context=int(data.get("context", display.context)),
                layout=str(data.get("layout", display.layout)),
                frame=bool(data.get("frame", display.frame)),
            )

    return ranges, display


def _status_for_line(ranges: list[ProgressRange], file_name: str, line_number: int) -> str | None:
    best_status: str | None = None
    best_priority = 0

    for item in ranges:
        if item.file != file_name:
            continue
        if item.start <= line_number <= item.end:
            priority = STATUS_PRIORITY[item.status]
            if priority > best_priority:
                best_status = item.status
                best_priority = priority

    return best_status


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 1:
        return value[:width]
    return value[: width - 1] + "…"


def _render_panel(
    *,
    title: str,
    panel: str,
    ranges: list[ProgressRange],
    repo_root: Path,
    context: int,
    width: int,
) -> list[str]:
    panel_ranges = [item for item in ranges if item.panel == panel]
    if not panel_ranges:
        return [_accent(title), ""]

    by_file: dict[str, list[ProgressRange]] = {}
    for item in panel_ranges:
        by_file.setdefault(item.file, []).append(item)

    rows: list[str] = [_accent(title), _color("─" * min(width, 48), bold=False)]

    for file_index, (file_name, file_ranges) in enumerate(sorted(by_file.items())):
        file_path = repo_root / file_name
        lines = file_path.read_text(encoding="utf-8").splitlines()

        first = max(1, min(item.start for item in file_ranges) - context)
        last = min(len(lines), max(item.end for item in file_ranges) + context)

        if file_index > 0:
            rows.append("")

        rows.append(_color(f"📄 {file_name}", bold=True))

        for line_number in range(first, last + 1):
            status = _status_for_line(file_ranges, file_name, line_number)
            icon = STATUS_ICON[status]
            content = lines[line_number - 1]
            raw = f"{icon}{line_number:>4}  {content}"
            raw = _truncate(raw, width)

            if status:
                rows.append(_color(raw, status))
            else:
                rows.append(_color(raw, dim=True))

    return rows


def _pad_plain(text: str, width: int) -> str:
    plain = _strip_ansi(text)
    visible_len = len(plain)
    if visible_len >= width:
        return text
    return text + " " * (width - visible_len)


def _strip_ansi(text: str) -> str:
    result = []
    index = 0
    while index < len(text):
        if text[index] == "\033":
            end = text.find("m", index)
            if end == -1:
                break
            index = end + 1
            continue
        result.append(text[index])
        index += 1
    return "".join(result)


def _active_indices(rows: list[str]) -> list[int]:
    return [
        index
        for index, row in enumerate(rows)
        if "🟪" in _strip_ansi(row)
    ]


def _active_center(rows: list[str]) -> float | None:
    indices = _active_indices(rows)
    if not indices:
        return None
    return (indices[0] + indices[-1]) / 2


def _pad_before_active(rows: list[str], count: int) -> list[str]:
    if count <= 0:
        return rows

    indices = _active_indices(rows)
    if not indices:
        return rows

    insert_at = indices[0]
    return rows[:insert_at] + [""] * count + rows[insert_at:]


def _align_active_midpoints(left: list[str], right: list[str]) -> tuple[list[str], list[str]]:
    left_center = _active_center(left)
    right_center = _active_center(right)

    if left_center is None or right_center is None:
        return left, right

    delta = int(round(abs(left_center - right_center)))
    if delta <= 0:
        return left, right

    if left_center < right_center:
        return _pad_before_active(left, delta), right

    return left, _pad_before_active(right, delta)


def render_side_by_side(left: list[str], right: list[str], *, width: int) -> str:
    left, right = _align_active_midpoints(left, right)

    gap = "    "
    rows: list[str] = []
    max_rows = max(len(left), len(right))
    for index in range(max_rows):
        left_value = left[index] if index < len(left) else ""
        right_value = right[index] if index < len(right) else ""
        rows.append(f"{_pad_plain(left_value, width)}{gap}{right_value}".rstrip())
    return "\n".join(rows)


def render_stacked(left: list[str], right: list[str]) -> str:
    return "\n".join(left + [""] + right)


def render_progress(records: list[MetaRecord], *, repo_root: Path) -> str:
    ranges, display = _records_to_progress(records)
    if not ranges:
        return ""

    terminal_width = shutil.get_terminal_size((120, 20)).columns
    column_width = max(44, min(72, (terminal_width - 6) // 2))

    roadmap = _render_panel(
        title="ROADMAP",
        panel="roadmap",
        ranges=ranges,
        repo_root=repo_root,
        context=display.context,
        width=column_width,
    )
    milestone = _render_panel(
        title="MILESTONE",
        panel="milestone",
        ranges=ranges,
        repo_root=repo_root,
        context=display.context,
        width=column_width,
    )

    if display.layout == "stacked" or terminal_width < 100:
        return render_stacked(roadmap, milestone)

    return render_side_by_side(roadmap, milestone, width=column_width)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render repodossier progress context from patch metadata.")
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--repo", default=Path.cwd(), type=Path)
    args = parser.parse_args(argv)

    script_path = args.script.expanduser().resolve()
    repo_root = args.repo.expanduser().resolve()

    records, parse_errors = parse_metadata_lines(script_path)
    errors = parse_errors + validate_records(
        records,
        script_path=script_path,
        repo_root=repo_root,
        require_metadata=True,
    )

    if errors:
        print("Cannot render progress context because metadata is invalid:")
        for error in errors:
            print(f"  - {error}")
        return 10

    rendered = render_progress(records, repo_root=repo_root)
    if rendered:
        print(_accent("c · Progress Context"))
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
