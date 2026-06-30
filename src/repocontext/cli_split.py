"""CLI helpers for split export options."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping

from .output_writer import build_part_header, part_path_for
from .split_config import SplitExportConfig, parse_split_export_config
from .splitter import split_text


_ORIGINAL_PATH_WRITE_TEXT: Callable[..., int] | None = None


_SPLIT_OUTPUTS_BY_COMMAND: dict[str, tuple[str, ...]] = {
    "full": ("full.txt",),
    "export-ai": ("ai.txt",),
    "export-docs": ("docs.txt",),
    "changed": ("changed.txt",),
}


def add_split_export_options(parser: argparse.ArgumentParser) -> None:
    """Add common split export CLI options to an argparse parser."""

    split_group = parser.add_mutually_exclusive_group()
    split_group.add_argument(
        "--split",
        dest="split_enabled",
        action="store_true",
        default=None,
        help="Write additional split part files next to the complete export file.",
    )
    split_group.add_argument(
        "--no-split",
        dest="split_enabled",
        action="store_false",
        default=None,
        help="Disable split part files even when enabled in .repocontext.yml.",
    )
    parser.add_argument(
        "--split-max-chars",
        dest="split_max_chars",
        type=_positive_int,
        default=None,
        metavar="N",
        help="Maximum number of raw export characters per split part.",
    )
    parser.add_argument(
        "--split-strategy",
        dest="split_strategy",
        choices=("plain", "heading"),
        default=None,
        help="Split strategy for part files.",
    )


def resolve_split_export_config(
    base_config: SplitExportConfig | Mapping[str, Any] | None,
    args: argparse.Namespace,
) -> SplitExportConfig:
    """Resolve split export settings with CLI options overriding config values."""

    config = _normalize_base_config(base_config)

    enabled = getattr(args, "split_enabled", None)
    max_chars = getattr(args, "split_max_chars", None)
    strategy = getattr(args, "split_strategy", None)

    if enabled is not None:
        config = replace(config, enabled=enabled)
    if max_chars is not None:
        config = replace(config, max_chars=max_chars)
    if strategy is not None:
        config = replace(config, strategy=strategy)

    return config


def enable_split_write_interceptor_for_args(
    args: argparse.Namespace,
    *,
    base_config: SplitExportConfig | Mapping[str, Any] | None = None,
    output_names: tuple[str, ...] | None = None,
) -> Callable[[], None] | None:
    """Enable split part writing for supported export commands.

    The existing export commands already write the complete export files. This
    interceptor keeps that behavior intact and writes additional ``.partXX``
    files when the matching complete export file is written.

    Supported commands so far:

    - ``full`` -> ``full.partXX.txt``
    - ``export-ai`` -> ``ai.partXX.txt``
    - ``export-docs`` -> ``docs.partXX.txt``
    - ``changed`` -> ``changed.partXX.txt`` or custom ``--output`` parts
    """

    resolved_output_names = output_names
    if resolved_output_names is None:
        resolved_output_names = _output_names_for_args(args)

    if not resolved_output_names:
        return None

    effective_base_config = base_config
    if effective_base_config is None:
        effective_base_config = _load_split_config_from_file_safely(args)

    split_config = resolve_split_export_config(effective_base_config, args)
    if not split_config.enabled:
        return None

    return _enable_split_write_interceptor(
        split_config=split_config,
        output_names=resolved_output_names,
    )


def _output_names_for_args(args: argparse.Namespace) -> tuple[str, ...] | None:
    command_name = _selected_command_name(args)
    if command_name is None:
        return None

    if command_name == "changed":
        output = getattr(args, "output", None) or "changed.txt"
        return (Path(str(output)).name,)

    return _SPLIT_OUTPUTS_BY_COMMAND.get(command_name)


def _enable_split_write_interceptor(
    *,
    split_config: SplitExportConfig,
    output_names: tuple[str, ...],
) -> Callable[[], None]:
    global _ORIGINAL_PATH_WRITE_TEXT

    if _ORIGINAL_PATH_WRITE_TEXT is not None:
        original_write_text = _ORIGINAL_PATH_WRITE_TEXT
    else:
        original_write_text = Path.write_text
        _ORIGINAL_PATH_WRITE_TEXT = original_write_text

    def patched_write_text(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
        written = original_write_text(self, data, *args, **kwargs)

        path = Path(self)
        if path.name in output_names and isinstance(data, str):
            _write_split_parts_with_original_writer(
                output_path=path,
                text=data,
                split_config=split_config,
                original_write_text=original_write_text,
            )

        return written

    Path.write_text = patched_write_text  # type: ignore[method-assign]

    def restore() -> None:
        global _ORIGINAL_PATH_WRITE_TEXT

        if _ORIGINAL_PATH_WRITE_TEXT is not None:
            Path.write_text = _ORIGINAL_PATH_WRITE_TEXT  # type: ignore[method-assign]
            _ORIGINAL_PATH_WRITE_TEXT = None

    return restore


def _write_split_parts_with_original_writer(
    *,
    output_path: Path,
    text: str,
    split_config: SplitExportConfig,
    original_write_text: Callable[..., int],
) -> None:
    _remove_stale_part_files(output_path)

    raw_parts = split_text(
        text,
        max_chars=split_config.max_chars,
        strategy=split_config.strategy,
    )
    total_parts = len(raw_parts)

    for index, raw_part in enumerate(raw_parts, start=1):
        part_path = part_path_for(output_path, index, total_parts)
        header = build_part_header(output_path.name, index, total_parts)
        original_write_text(part_path, header + raw_part, encoding="utf-8")


def _remove_stale_part_files(output_path: Path) -> None:
    suffix = output_path.suffix
    stem = output_path.stem

    if suffix:
        pattern = f"{stem}.part*{suffix}"
    else:
        pattern = f"{output_path.name}.part*"

    for stale_part in output_path.parent.glob(pattern):
        if stale_part.is_file():
            stale_part.unlink()


def _selected_command_name(args: argparse.Namespace) -> str | None:
    for attr_name in ("command", "cmd", "subcommand", "action"):
        value = getattr(args, attr_name, None)
        if isinstance(value, str):
            return value

    return None


def _load_split_config_from_file_safely(args: argparse.Namespace) -> Mapping[str, Any] | None:
    config_path = _config_path_from_args(args)
    if config_path is None:
        return None

    try:
        import yaml  # type: ignore[import-untyped]
    except Exception:
        return None

    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if isinstance(loaded, Mapping):
        return loaded

    return None


def _config_path_from_args(args: argparse.Namespace) -> Path | None:
    explicit_config = getattr(args, "config", None) or getattr(args, "config_path", None)
    if explicit_config:
        path = Path(explicit_config)
        if path.exists():
            return path

    for candidate in (Path.cwd() / ".repocontext.yml", Path.cwd() / ".repocontext.yaml"):
        if candidate.exists():
            return candidate

    return None


def _normalize_base_config(base_config: SplitExportConfig | Mapping[str, Any] | None) -> SplitExportConfig:
    if base_config is None:
        return SplitExportConfig()

    if isinstance(base_config, SplitExportConfig):
        return base_config

    return parse_split_export_config(base_config)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed
