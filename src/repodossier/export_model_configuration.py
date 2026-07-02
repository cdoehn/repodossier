"""Configuration summary helpers for RepoDossier's structured export model."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from repodossier.export_model import ExportConfigurationSummary
from repodossier.export_model_paths import normalize_export_path


def make_export_configuration_summary(
    *,
    config_active: bool = False,
    config_path: str | None = None,
    include_paths: Iterable[str] = (),
    include_globs: Iterable[str] = (),
    exclude_paths: Iterable[str] = (),
    exclude_globs: Iterable[str] = (),
    limits: Mapping[str, Any] | None = None,
    split_settings: Mapping[str, Any] | None = None,
) -> ExportConfigurationSummary:
    """Build a deterministic configuration summary for export models."""

    return ExportConfigurationSummary(
        config_active=config_active,
        config_path=_normalize_optional_text(config_path),
        include_paths=normalize_configuration_paths(include_paths),
        include_globs=normalize_configuration_patterns(include_globs),
        exclude_paths=normalize_configuration_paths(exclude_paths),
        exclude_globs=normalize_configuration_patterns(exclude_globs),
        limits=normalize_configuration_mapping(limits),
        split_settings=normalize_configuration_mapping(split_settings),
    )


def normalize_configuration_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """Normalize, deduplicate and sort repository-relative config paths."""

    return tuple(sorted({normalize_export_path(path) for path in paths}))


def normalize_configuration_patterns(patterns: Iterable[str]) -> tuple[str, ...]:
    """Normalize, deduplicate and sort glob-like config patterns."""

    normalized: set[str] = set()

    for pattern in patterns:
        value = str(pattern).strip().replace("\\", "/")
        if value:
            normalized.add(value)

    return tuple(sorted(normalized))


def normalize_configuration_mapping(
    values: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a deterministic plain mapping copy for config metadata."""

    if not values:
        return {}

    return {
        str(key): _plain_config_value(values[key])
        for key in sorted(values, key=lambda item: str(item))
    }


def merge_configuration_summaries(
    base: ExportConfigurationSummary,
    override: ExportConfigurationSummary,
) -> ExportConfigurationSummary:
    """Merge two summaries, using override values when they are present."""

    return ExportConfigurationSummary(
        config_active=base.config_active or override.config_active,
        config_path=override.config_path or base.config_path,
        include_paths=_merge_tuples(base.include_paths, override.include_paths),
        include_globs=_merge_tuples(base.include_globs, override.include_globs),
        exclude_paths=_merge_tuples(base.exclude_paths, override.exclude_paths),
        exclude_globs=_merge_tuples(base.exclude_globs, override.exclude_globs),
        limits={
            **base.limits,
            **override.limits,
        },
        split_settings={
            **base.split_settings,
            **override.split_settings,
        },
    )


def _merge_tuples(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(left) | set(right)))


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    stripped = str(value).strip()
    return stripped or None


def _plain_config_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return normalize_configuration_mapping(value)

    if isinstance(value, tuple | list | set):
        return [
            _plain_config_value(item)
            for item in sorted(value, key=lambda item: str(item))
        ]

    return value
