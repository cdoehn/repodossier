"""Split export configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


DEFAULT_SPLIT_MAX_CHARS = 200_000
DEFAULT_SPLIT_STRATEGY = "heading"
VALID_SPLIT_STRATEGIES = ("plain", "heading")


@dataclass(frozen=True)
class SplitExportConfig:
    """Configuration for optional multi-part export output."""

    enabled: bool = False
    max_chars: int = DEFAULT_SPLIT_MAX_CHARS
    strategy: str = DEFAULT_SPLIT_STRATEGY

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_chars": self.max_chars,
            "strategy": self.strategy,
        }


def parse_split_export_config(raw_config: Mapping[str, Any] | None = None) -> SplitExportConfig:
    """Parse split export configuration from a full RepoDossier config mapping.

    Expected shape:

        exports:
          split:
            enabled: false
            max_chars: 200000
            strategy: heading

    For convenience and future CLI integration, this function also accepts the
    split mapping directly.
    """

    if raw_config is None:
        return SplitExportConfig()

    if not isinstance(raw_config, Mapping):
        raise ValueError("config must be a mapping")

    if _looks_like_split_mapping(raw_config):
        split_config = raw_config
    else:
        exports_config = raw_config.get("exports", {})
        if exports_config is None:
            exports_config = {}
        if not isinstance(exports_config, Mapping):
            raise ValueError("exports must be a mapping")

        split_config = exports_config.get("split", {})
        if split_config is None:
            split_config = {}

    if not isinstance(split_config, Mapping):
        raise ValueError("exports.split must be a mapping")

    enabled = _parse_bool(
        split_config.get("enabled", SplitExportConfig.enabled),
        "exports.split.enabled",
    )
    max_chars = _parse_positive_int(
        split_config.get("max_chars", SplitExportConfig.max_chars),
        "exports.split.max_chars",
    )
    strategy = _parse_strategy(
        split_config.get("strategy", SplitExportConfig.strategy),
        "exports.split.strategy",
    )

    return SplitExportConfig(
        enabled=enabled,
        max_chars=max_chars,
        strategy=strategy,
    )


def _looks_like_split_mapping(raw_config: Mapping[str, Any]) -> bool:
    split_keys = {"enabled", "max_chars", "strategy"}
    return any(key in raw_config for key in split_keys)


def _parse_bool(value: Any, path: str) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "on", "1"}:
            return True
        if normalized in {"false", "no", "off", "0"}:
            return False

    raise ValueError(f"{path} must be a boolean")


def _parse_positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{path} must be a positive integer")

    if value <= 0:
        raise ValueError(f"{path} must be a positive integer")

    return value


def _parse_strategy(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be one of: {', '.join(VALID_SPLIT_STRATEGIES)}")

    normalized = value.strip().lower()
    if normalized not in VALID_SPLIT_STRATEGIES:
        raise ValueError(f"{path} must be one of: {', '.join(VALID_SPLIT_STRATEGIES)}")

    return normalized
