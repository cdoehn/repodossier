"""Report normalization helpers for RepoDossier's structured export model."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from repodossier.export_model import (
    CallGraphReport,
    DatabaseSchemaReport,
    DependencyReport,
    ImportGraphReport,
    RecentCommitReport,
    SecretDetectionSummary,
    SymbolIndex,
    TestMapReport,
)
from repodossier.export_model_paths import normalize_export_path


def normalize_report_items(
    items: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Return deterministic plain report items.

    The structured export model intentionally stores analyzer payloads as
    plain dictionaries for now. These helpers keep those dictionaries stable
    and renderer-friendly until richer typed report models are introduced.
    """

    normalized = tuple(normalize_report_mapping(item) for item in items)
    return tuple(sorted(normalized, key=_report_item_sort_key))


def normalize_report_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic deep plain-data copy of a mapping."""

    return {
        str(key): _normalize_report_value(values[key])
        for key in sorted(values, key=lambda item: str(item))
    }


def make_dependency_report(
    items: Iterable[Mapping[str, Any]] = (),
) -> DependencyReport:
    """Create a deterministic dependency report."""

    return DependencyReport(items=normalize_report_items(items))


def make_database_schema_report(
    items: Iterable[Mapping[str, Any]] = (),
) -> DatabaseSchemaReport:
    """Create a deterministic database schema report."""

    return DatabaseSchemaReport(items=normalize_report_items(items))


def make_secret_detection_summary(
    *,
    findings: Iterable[Mapping[str, Any]] = (),
    masked_files: Iterable[str] = (),
) -> SecretDetectionSummary:
    """Create a deterministic secret detection summary."""

    return SecretDetectionSummary(
        findings=normalize_report_items(findings),
        masked_files=tuple(
            sorted({normalize_export_path(path) for path in masked_files})
        ),
    )


def make_symbol_index(
    symbols: Iterable[Mapping[str, Any]] = (),
) -> SymbolIndex:
    """Create a deterministic symbol index."""

    return SymbolIndex(symbols=normalize_report_items(symbols))


def make_import_graph_report(
    edges: Iterable[Mapping[str, Any]] = (),
) -> ImportGraphReport:
    """Create a deterministic import graph report."""

    return ImportGraphReport(edges=normalize_report_items(edges))


def make_call_graph_report(
    edges: Iterable[Mapping[str, Any]] = (),
) -> CallGraphReport:
    """Create a deterministic call graph report."""

    return CallGraphReport(edges=normalize_report_items(edges))


def make_test_map_report(
    mappings: Iterable[Mapping[str, Any]] = (),
) -> TestMapReport:
    """Create a deterministic test map report."""

    return TestMapReport(mappings=normalize_report_items(mappings))


def make_recent_commit_report(
    commits: Iterable[Mapping[str, Any]] = (),
) -> RecentCommitReport:
    """Create a deterministic recent commit report."""

    return RecentCommitReport(commits=normalize_report_items(commits))


def _normalize_report_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return normalize_report_mapping(value)

    if isinstance(value, tuple | list | set):
        return [
            _normalize_report_value(item)
            for item in sorted(value, key=lambda item: str(item))
        ]

    return value


def _report_item_sort_key(item: Mapping[str, Any]) -> tuple[str, ...]:
    preferred_keys = (
        "path",
        "file",
        "table",
        "source",
        "target",
        "name",
        "kind",
        "type",
        "message",
        "hash",
        "short_hash",
    )

    preferred_values = tuple(str(item.get(key, "")) for key in preferred_keys)
    fallback = repr(sorted(item.items(), key=lambda pair: str(pair[0])))
    return preferred_values + (fallback,)
