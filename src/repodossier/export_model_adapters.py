"""Adapter helpers for migrating existing data into the export model."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from repodossier.export_model import FileEntry, FileStatus, TextStatus
from repodossier.export_model_content import make_file_entry_from_content
from repodossier.export_model_paths import normalize_export_path


def file_entry_from_mapping(values: Mapping[str, Any]) -> FileEntry:
    """Build a FileEntry from a dict-like scanner/exporter payload.

    This intentionally accepts several common legacy key names so existing
    code can migrate incrementally without duplicating model construction
    logic in every exporter.
    """

    path = _first_present(values, "path", "relative_path", "file_path", "name")
    if path is None:
        raise ValueError("file mapping must include a path")

    language = _first_present(values, "language", "lang")
    if language is None:
        language = "unknown"

    content = _first_present(values, "content", "text", "source")
    masked_content = _first_present(values, "masked_content", "redacted_content")

    text_status = _text_status_from_mapping(values)
    status = _file_status_from_mapping(values)

    return make_file_entry_from_content(
        path=normalize_export_path(str(path)),
        language=str(language).strip() or "unknown",
        content=None if content is None else str(content),
        masked_content=(
            None if masked_content is None else str(masked_content)
        ),
        text_status=text_status,
        status=status,
        size_bytes=_optional_int(values, "size_bytes", "bytes", "size"),
        line_count=_optional_int(values, "line_count", "lines"),
        estimated_tokens=_optional_int(
            values,
            "estimated_tokens",
            "tokens",
            "token_estimate",
        ),
        reason=_optional_text(values, "reason", "skip_reason", "error"),
    )


def file_entries_from_mappings(
    values: Iterable[Mapping[str, Any]],
) -> tuple[FileEntry, ...]:
    """Build deterministic FileEntry objects from mapping payloads."""

    entries = tuple(file_entry_from_mapping(value) for value in values)
    return tuple(sorted(entries, key=lambda entry: entry.path))


def file_entry_from_object(value: object) -> FileEntry:
    """Build a FileEntry from an object with scanner-like attributes."""

    return file_entry_from_mapping(_object_to_mapping(value))


def file_entries_from_objects(values: Iterable[object]) -> tuple[FileEntry, ...]:
    """Build deterministic FileEntry objects from object payloads."""

    entries = tuple(file_entry_from_object(value) for value in values)
    return tuple(sorted(entries, key=lambda entry: entry.path))


def _object_to_mapping(value: object) -> dict[str, Any]:
    names = (
        "path",
        "relative_path",
        "file_path",
        "name",
        "language",
        "lang",
        "content",
        "text",
        "source",
        "masked_content",
        "redacted_content",
        "text_status",
        "is_binary",
        "binary",
        "status",
        "skipped",
        "truncated",
        "error",
        "size_bytes",
        "bytes",
        "size",
        "line_count",
        "lines",
        "estimated_tokens",
        "tokens",
        "token_estimate",
        "reason",
        "skip_reason",
    )

    return {
        name: getattr(value, name)
        for name in names
        if hasattr(value, name)
    }


def _first_present(values: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in values and values[key] is not None:
            return values[key]

    return None


def _optional_text(values: Mapping[str, Any], *keys: str) -> str | None:
    value = _first_present(values, *keys)
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _optional_int(values: Mapping[str, Any], *keys: str) -> int | None:
    value = _first_present(values, *keys)
    if value is None:
        return None

    return int(value)


def _text_status_from_mapping(values: Mapping[str, Any]) -> TextStatus:
    explicit = _optional_text(values, "text_status")
    if explicit in {"text", "binary"}:
        return explicit  # type: ignore[return-value]

    if bool(values.get("is_binary")) or bool(values.get("binary")):
        return "binary"

    return "text"


def _file_status_from_mapping(values: Mapping[str, Any]) -> FileStatus:
    explicit = _optional_text(values, "status")
    if explicit in {"included", "skipped", "truncated", "error"}:
        return explicit  # type: ignore[return-value]

    if bool(values.get("error")):
        return "error"

    if bool(values.get("truncated")):
        return "truncated"

    if bool(values.get("skipped")):
        return "skipped"

    return "included"
