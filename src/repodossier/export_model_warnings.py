"""Warning helpers for RepoDossier's structured export model."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from repodossier.export_model import ExportWarning, RepositoryExport
from repodossier.export_model_paths import normalize_export_path


def make_export_warning(
    message: str,
    *,
    path: str | None = None,
    code: str | None = None,
) -> ExportWarning:
    """Create a normalized export warning."""

    normalized_message = str(message).strip()
    if not normalized_message:
        raise ValueError("warning message must not be empty")

    normalized_path = None
    if path is not None:
        normalized_path = normalize_export_path(path)

    normalized_code = _normalize_optional_text(code)

    return ExportWarning(
        message=normalized_message,
        path=normalized_path,
        code=normalized_code,
    )


def normalize_export_warnings(
    warnings: Iterable[ExportWarning],
) -> tuple[ExportWarning, ...]:
    """Deduplicate and sort warnings deterministically."""

    unique = {
        _warning_key(warning): warning
        for warning in warnings
        if warning.message.strip()
    }

    return tuple(
        unique[key]
        for key in sorted(unique)
    )


def append_export_warnings(
    export: RepositoryExport,
    warnings: Iterable[ExportWarning],
) -> RepositoryExport:
    """Return a copy of export with additional normalized warnings."""

    merged = normalize_export_warnings(
        tuple(export.warnings) + tuple(warnings)
    )

    return replace(export, warnings=merged)


def warning_counts_by_code(
    warnings: Iterable[ExportWarning],
) -> dict[str, int]:
    """Return deterministic warning counts grouped by code."""

    counts: dict[str, int] = {}

    for warning in warnings:
        code = warning.code or "uncategorized"
        counts[code] = counts.get(code, 0) + 1

    return dict(sorted(counts.items()))


def warnings_by_path(
    warnings: Iterable[ExportWarning],
) -> dict[str, tuple[ExportWarning, ...]]:
    """Return deterministic warnings grouped by path."""

    grouped: dict[str, list[ExportWarning]] = {}

    for warning in warnings:
        path = warning.path or "<repository>"
        grouped.setdefault(path, []).append(warning)

    return {
        path: tuple(sorted(items, key=_warning_key))
        for path, items in sorted(grouped.items())
    }


def warning_messages(
    warnings: Iterable[ExportWarning],
) -> tuple[str, ...]:
    """Return warning messages in deterministic normalized order."""

    return tuple(
        warning.message
        for warning in normalize_export_warnings(warnings)
    )


def _warning_key(warning: ExportWarning) -> tuple[str, str, str]:
    return (
        warning.path or "",
        warning.code or "",
        warning.message.strip(),
    )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    stripped = str(value).strip()
    return stripped or None
