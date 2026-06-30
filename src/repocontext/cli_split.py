"""CLI helpers for split export options."""

from __future__ import annotations

import argparse
from dataclasses import replace
from typing import Any, Mapping

from .split_config import SplitExportConfig, parse_split_export_config


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
