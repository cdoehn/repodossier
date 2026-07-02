"""Deserialization helpers for RepoDossier's structured export model."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from repodossier.export_model import (
    CallGraphReport,
    DatabaseSchemaReport,
    DependencyReport,
    ExportConfigurationSummary,
    ExportSummary,
    ExportWarning,
    FileEntry,
    FileTreeEntry,
    ImportGraphReport,
    LanguageStatistics,
    RecentCommitReport,
    RepositoryExport,
    RepositoryMetadata,
    SecretDetectionSummary,
    SymbolIndex,
    TestMapReport,
    assert_valid_repository_export,
)


def repository_export_from_dict(
    data: Mapping[str, Any],
    *,
    validate: bool = True,
) -> RepositoryExport:
    """Build a RepositoryExport dataclass tree from plain mapping data."""

    export = RepositoryExport(
        mode=str(_required(data, "mode")),
        repository=_repository_metadata_from_dict(
            _mapping(_required(data, "repository"), "repository")
        ),
        configuration=_configuration_from_dict(
            _mapping(data.get("configuration", {}), "configuration")
        ),
        summary=_summary_from_dict(_mapping(data.get("summary", {}), "summary")),
        tree=_tree_entries_from_data(data.get("tree", ())),
        files=_file_entries_from_data(data.get("files", ())),
        omitted_files=_file_entries_from_data(data.get("omitted_files", ())),
        truncated_files=_file_entries_from_data(data.get("truncated_files", ())),
        warnings=_warnings_from_data(data.get("warnings", ())),
        dependencies=_dependency_report_from_dict(
            _mapping(data.get("dependencies", {}), "dependencies")
        ),
        database_schema=_database_schema_report_from_dict(
            _mapping(data.get("database_schema", {}), "database_schema")
        ),
        secret_detection=_secret_detection_summary_from_dict(
            _mapping(data.get("secret_detection", {}), "secret_detection")
        ),
        symbol_index=_symbol_index_from_dict(
            _mapping(data.get("symbol_index", {}), "symbol_index")
        ),
        import_graph=_import_graph_report_from_dict(
            _mapping(data.get("import_graph", {}), "import_graph")
        ),
        call_graph=_call_graph_report_from_dict(
            _mapping(data.get("call_graph", {}), "call_graph")
        ),
        test_map=_test_map_report_from_dict(
            _mapping(data.get("test_map", {}), "test_map")
        ),
        recent_commits=_recent_commit_report_from_dict(
            _mapping(data.get("recent_commits", {}), "recent_commits")
        ),
    )

    if validate:
        assert_valid_repository_export(export)

    return export


def repository_export_from_json(
    text: str,
    *,
    validate: bool = True,
) -> RepositoryExport:
    """Build a RepositoryExport from JSON text."""

    loaded = json.loads(text)

    if not isinstance(loaded, Mapping):
        raise ValueError("repository export JSON must contain an object")

    return repository_export_from_dict(loaded, validate=validate)


def _repository_metadata_from_dict(data: Mapping[str, Any]) -> RepositoryMetadata:
    return RepositoryMetadata(
        root_path=str(_required(data, "root_path")),
        root_name=str(_required(data, "root_name")),
        git_branch=_optional_str(data.get("git_branch")),
        git_commit=_optional_str(data.get("git_commit")),
        git_dirty=_optional_bool(data.get("git_dirty")),
    )


def _configuration_from_dict(
    data: Mapping[str, Any],
) -> ExportConfigurationSummary:
    return ExportConfigurationSummary(
        config_active=bool(data.get("config_active", False)),
        config_path=_optional_str(data.get("config_path")),
        include_paths=_str_tuple(data.get("include_paths", ())),
        include_globs=_str_tuple(data.get("include_globs", ())),
        exclude_paths=_str_tuple(data.get("exclude_paths", ())),
        exclude_globs=_str_tuple(data.get("exclude_globs", ())),
        limits=dict(data.get("limits", {}) or {}),
        split_settings=dict(data.get("split_settings", {}) or {}),
    )


def _summary_from_dict(data: Mapping[str, Any]) -> ExportSummary:
    return ExportSummary(
        total_tracked_files=int(data.get("total_tracked_files", 0)),
        scanned_files=int(data.get("scanned_files", 0)),
        exported_text_files=int(data.get("exported_text_files", 0)),
        skipped_binary_files=int(data.get("skipped_binary_files", 0)),
        errored_files=int(data.get("errored_files", 0)),
        total_lines=int(data.get("total_lines", 0)),
        estimated_tokens=int(data.get("estimated_tokens", 0)),
        file_type_statistics=dict(data.get("file_type_statistics", {}) or {}),
        language_statistics=_language_statistics_from_dict(
            _mapping(data.get("language_statistics", {}), "language_statistics")
        ),
    )


def _language_statistics_from_dict(
    data: Mapping[str, Any],
) -> LanguageStatistics:
    return LanguageStatistics(
        counts={
            str(key): int(value)
            for key, value in dict(data.get("counts", {}) or {}).items()
        }
    )


def _file_entry_from_dict(data: Mapping[str, Any]) -> FileEntry:
    return FileEntry(
        path=str(_required(data, "path")),
        language=str(_required(data, "language")),
        size_bytes=int(data.get("size_bytes", 0)),
        line_count=int(data.get("line_count", 0)),
        estimated_tokens=int(data.get("estimated_tokens", 0)),
        text_status=str(data.get("text_status", "text")),  # type: ignore[arg-type]
        status=str(data.get("status", "included")),  # type: ignore[arg-type]
        content=_optional_str(data.get("content")),
        masked_content=_optional_str(data.get("masked_content")),
        reason=_optional_str(data.get("reason")),
    )


def _file_entries_from_data(value: Any) -> tuple[FileEntry, ...]:
    return tuple(
        _file_entry_from_dict(_mapping(item, "file entry"))
        for item in _sequence(value, "file entries")
    )


def _tree_entry_from_dict(data: Mapping[str, Any]) -> FileTreeEntry:
    return FileTreeEntry(
        path=str(_required(data, "path")),
        entry_type=str(data.get("entry_type", "file")),  # type: ignore[arg-type]
        children=tuple(
            _tree_entry_from_dict(_mapping(item, "tree entry"))
            for item in _sequence(data.get("children", ()), "tree children")
        ),
    )


def _tree_entries_from_data(value: Any) -> tuple[FileTreeEntry, ...]:
    return tuple(
        _tree_entry_from_dict(_mapping(item, "tree entry"))
        for item in _sequence(value, "tree")
    )


def _warning_from_dict(data: Mapping[str, Any]) -> ExportWarning:
    return ExportWarning(
        message=str(_required(data, "message")),
        path=_optional_str(data.get("path")),
        code=_optional_str(data.get("code")),
    )


def _warnings_from_data(value: Any) -> tuple[ExportWarning, ...]:
    return tuple(
        _warning_from_dict(_mapping(item, "warning"))
        for item in _sequence(value, "warnings")
    )


def _dependency_report_from_dict(data: Mapping[str, Any]) -> DependencyReport:
    return DependencyReport(items=_mapping_tuple(data.get("items", ())))


def _database_schema_report_from_dict(
    data: Mapping[str, Any],
) -> DatabaseSchemaReport:
    return DatabaseSchemaReport(items=_mapping_tuple(data.get("items", ())))


def _secret_detection_summary_from_dict(
    data: Mapping[str, Any],
) -> SecretDetectionSummary:
    return SecretDetectionSummary(
        findings=_mapping_tuple(data.get("findings", ())),
        masked_files=_str_tuple(data.get("masked_files", ())),
    )


def _symbol_index_from_dict(data: Mapping[str, Any]) -> SymbolIndex:
    return SymbolIndex(symbols=_mapping_tuple(data.get("symbols", ())))


def _import_graph_report_from_dict(
    data: Mapping[str, Any],
) -> ImportGraphReport:
    return ImportGraphReport(edges=_mapping_tuple(data.get("edges", ())))


def _call_graph_report_from_dict(data: Mapping[str, Any]) -> CallGraphReport:
    return CallGraphReport(edges=_mapping_tuple(data.get("edges", ())))


def _test_map_report_from_dict(data: Mapping[str, Any]) -> TestMapReport:
    return TestMapReport(mappings=_mapping_tuple(data.get("mappings", ())))


def _recent_commit_report_from_dict(
    data: Mapping[str, Any],
) -> RecentCommitReport:
    return RecentCommitReport(commits=_mapping_tuple(data.get("commits", ())))


def _mapping_tuple(value: Any) -> tuple[dict[str, Any], ...]:
    return tuple(
        dict(_mapping(item, "report item"))
        for item in _sequence(value, "report items")
    )


def _str_tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in _sequence(value, "string sequence"))


def _required(data: Mapping[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"missing required field: {key}")

    return data[key]


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None

    return str(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None

    return bool(value)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")

    return value


def _sequence(value: Any, name: str) -> tuple[Any, ...]:
    if value is None:
        return ()

    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError(f"{name} must be a sequence")

    return tuple(value)
