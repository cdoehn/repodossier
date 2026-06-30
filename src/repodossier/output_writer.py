"""Split-aware export output writing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .split_config import SplitExportConfig, parse_split_export_config
from .splitter import split_text


@dataclass(frozen=True)
class ExportWriteResult:
    """Result metadata for a written export."""

    output_path: Path
    part_paths: tuple[Path, ...]


def write_export_output(
    output_path: str | Path,
    text: str,
    split_config: SplitExportConfig | Mapping[str, Any] | None = None,
) -> ExportWriteResult:
    """Write an export file and optional split part files.

    The main export file is always written completely. When split output is
    enabled, additional ``name.partXX.ext`` files are written next to it.

    Stale part files for the same export basename are removed before writing, so
    reruns do not leave obsolete parts behind.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    config = _normalize_split_config(split_config)

    _remove_stale_part_files(path)
    path.write_text(text, encoding="utf-8")

    if not config.enabled:
        return ExportWriteResult(output_path=path, part_paths=())

    raw_parts = split_text(text, max_chars=config.max_chars, strategy=config.strategy)
    part_paths = _write_part_files(path, raw_parts)

    return ExportWriteResult(output_path=path, part_paths=tuple(part_paths))


def build_part_header(source_name: str, part_number: int, total_parts: int) -> str:
    """Return the short header prepended to split export part files."""

    if part_number < 1:
        raise ValueError("part_number must be greater than or equal to 1")
    if total_parts < 1:
        raise ValueError("total_parts must be greater than or equal to 1")
    if part_number > total_parts:
        raise ValueError("part_number must not be greater than total_parts")

    return (
        f"# RepoDossier Export Part {part_number}/{total_parts}\n\n"
        f"Source export: {source_name}\n"
        f"Part: {part_number} of {total_parts}\n\n"
    )


def part_path_for(output_path: str | Path, part_number: int, total_parts: int) -> Path:
    """Return the deterministic path for an export part file."""

    if part_number < 1:
        raise ValueError("part_number must be greater than or equal to 1")
    if total_parts < 1:
        raise ValueError("total_parts must be greater than or equal to 1")
    if part_number > total_parts:
        raise ValueError("part_number must not be greater than total_parts")

    path = Path(output_path)
    width = max(2, len(str(total_parts)))
    suffix = path.suffix
    stem = path.stem

    if suffix:
        filename = f"{stem}.part{part_number:0{width}d}{suffix}"
    else:
        filename = f"{path.name}.part{part_number:0{width}d}"

    return path.with_name(filename)


def _normalize_split_config(
    split_config: SplitExportConfig | Mapping[str, Any] | None,
) -> SplitExportConfig:
    if split_config is None:
        return SplitExportConfig()

    if isinstance(split_config, SplitExportConfig):
        return split_config

    return parse_split_export_config(split_config)


def _write_part_files(output_path: Path, raw_parts: list[str]) -> list[Path]:
    total_parts = len(raw_parts)
    part_paths: list[Path] = []

    for index, raw_part in enumerate(raw_parts, start=1):
        part_path = part_path_for(output_path, index, total_parts)
        header = build_part_header(output_path.name, index, total_parts)
        part_path.write_text(header + raw_part, encoding="utf-8")
        part_paths.append(part_path)

    return part_paths


def _remove_stale_part_files(output_path: Path) -> None:
    part_glob = _part_glob_for(output_path)

    for stale_part in output_path.parent.glob(part_glob):
        if stale_part.is_file():
            stale_part.unlink()


def _part_glob_for(output_path: Path) -> str:
    suffix = output_path.suffix
    stem = output_path.stem

    if suffix:
        return f"{stem}.part*{suffix}"

    return f"{output_path.name}.part*"
