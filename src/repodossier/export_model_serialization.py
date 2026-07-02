"""Deterministic serialization helpers for the structured export model."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from repodossier.export_model import RepositoryExport


def repository_export_to_dict(
    export: RepositoryExport,
    *,
    include_content: bool = True,
) -> dict[str, Any]:
    """Convert a RepositoryExport into deterministic plain Python data.

    The result contains only dictionaries, lists and scalar values. This is
    useful for renderer tests, snapshot-style assertions and future machine
    format renderers.

    Set include_content to False for metadata-only comparisons that should
    not include potentially large file bodies.
    """

    omit_fields = frozenset() if include_content else frozenset(
        {"content", "masked_content"}
    )
    data = to_plain_data(export, omit_fields=omit_fields)

    if not isinstance(data, dict):
        raise TypeError("RepositoryExport did not serialize to a dictionary")

    return data


def to_plain_data(
    value: Any,
    *,
    omit_fields: frozenset[str] = frozenset(),
) -> Any:
    """Recursively convert dataclass-based model data to plain data.

    Dictionary keys are sorted by their string representation to keep output
    deterministic across runs.
    """

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_plain_data(
                getattr(value, field.name),
                omit_fields=omit_fields,
            )
            for field in fields(value)
            if field.name not in omit_fields
        }

    if isinstance(value, tuple | list):
        return [
            to_plain_data(item, omit_fields=omit_fields)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: to_plain_data(value[key], omit_fields=omit_fields)
            for key in sorted(value, key=lambda item: str(item))
        }

    return value
