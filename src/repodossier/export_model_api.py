"""Public facade for RepoDossier's structured export model.

This module gives future exporter and renderer migration code one stable
import surface while the internal helper modules remain small and focused.
"""

from __future__ import annotations

from repodossier.export_model_adapters import (
    file_entries_from_mappings,
    file_entries_from_objects,
    file_entry_from_mapping,
    file_entry_from_object,
)
from repodossier.export_model import (
    CallGraphReport,
    DatabaseSchemaReport,
    DependencyReport,
    ExportConfigurationSummary,
    ExportMode,
    ExportModelValidationError,
    ExportSummary,
    ExportWarning,
    FileEntry,
    FileStatus,
    FileTreeEntry,
    ImportGraphReport,
    LanguageStatistics,
    RecentCommitReport,
    RepositoryExport,
    RepositoryMetadata,
    SecretDetectionSummary,
    SymbolIndex,
    TestMapReport,
    TextStatus,
    assert_valid_repository_export,
    empty_repository_export,
    validate_repository_export,
)
from repodossier.export_model_audit import (
    RepositoryExportAuditError,
    RepositoryExportAuditResult,
    assert_repository_export_audit,
    audit_repository_export,
    repository_export_audit_lines,
)
from repodossier.export_model_collector import (
    FileEntryPartitions,
    partition_file_entries,
    repository_export_from_file_entries,
    repository_export_from_file_mappings,
    repository_export_from_file_objects,
)
from repodossier.export_model_compare import (
    FILE_COMPARE_FIELDS,
    FileEntryChange,
    RepositoryExportComparison,
    compare_file_entries,
    compare_repository_exports,
    repository_export_path_delta,
    repository_exports_have_same_paths,
)
from repodossier.export_model_configuration import (
    make_export_configuration_summary,
    merge_configuration_summaries,
    normalize_configuration_mapping,
    normalize_configuration_paths,
    normalize_configuration_patterns,
)
from repodossier.export_model_contract import (
    REQUIRED_EXPORT_MODEL_API_SYMBOLS,
    REQUIRED_EXPORT_MODEL_SECTIONS,
    ExportModelContractError,
    ExportModelContractStatus,
    assert_export_model_contract,
    export_model_contract_status,
    export_model_section_presence,
    missing_export_model_api_symbols,
    missing_export_model_sections,
)
from repodossier.export_model_content import (
    content_line_count,
    content_size_bytes,
    estimate_tokens_from_content,
    file_entry_content_for_rendering,
    file_entry_has_exportable_content,
    make_file_entry_from_content,
)
from repodossier.export_model_deserialization import (
    repository_export_from_dict,
    repository_export_from_json,
)
from repodossier.export_model_factory import (
    make_minimal_repository_export,
    make_repository_export,
)
from repodossier.export_model_finalize import (
    finalize_repository_export,
    refresh_repository_export_derived_sections,
    replace_repository_export_files,
    repository_export_with_files,
)
from repodossier.export_model_index import (
    file_index_by_path,
    files_by_language,
    files_by_status,
    filter_files_by_language,
    filter_files_by_status,
    get_file_entry,
    iter_known_files,
    language_counts_from_export,
    status_counts_from_export,
)
from repodossier.export_model_inventory import (
    FileInventoryEntry,
    FileInventoryGroup,
    repository_export_file_inventory,
    repository_export_file_inventory_by_group,
    repository_export_file_inventory_lines,
    repository_export_file_inventory_to_dicts,
)
from repodossier.export_model_manifest import (
    RepositoryExportManifest,
    repository_export_manifest,
    repository_export_manifest_lines,
    repository_export_manifest_to_dict,
)
from repodossier.export_model_modes import (
    MODE_DEFAULT_SECTIONS,
    MODE_TITLES,
    VALID_EXPORT_MODES,
    export_mode_default_sections,
    export_mode_includes_source_content,
    export_mode_is_review_focused,
    export_mode_title,
    is_valid_export_mode,
    normalize_export_mode,
    repository_export_default_sections,
    repository_export_title,
)
from repodossier.export_model_paths import (
    ancestor_export_paths,
    export_path_depth,
    export_path_name,
    export_path_parent,
    export_path_sort_key,
    normalize_export_path,
    normalize_export_paths,
    sort_export_paths,
)
from repodossier.export_model_repository import (
    make_repository_metadata,
    normalize_optional_text,
    normalize_repository_root_name,
    normalize_repository_root_path,
    repository_metadata_display_name,
    repository_metadata_has_git,
    repository_name_from_root_path,
    update_repository_git_metadata,
)
from repodossier.export_model_reports import (
    make_call_graph_report,
    make_database_schema_report,
    make_dependency_report,
    make_import_graph_report,
    make_recent_commit_report,
    make_secret_detection_summary,
    make_symbol_index,
    make_test_map_report,
    normalize_report_items,
    normalize_report_mapping,
)
from repodossier.export_model_readiness import (
    RepositoryExportReadinessError,
    RepositoryExportReadinessStatus,
    assert_repository_export_ready,
    repository_export_readiness_lines,
    repository_export_readiness_status,
)
from repodossier.export_model_roundtrip import (
    RepositoryExportRoundTripError,
    RepositoryExportRoundTripStatus,
    assert_repository_export_round_trips,
    repository_export_canonical_dict,
    repository_export_round_trip,
    repository_export_round_trip_status,
)
from repodossier.export_model_sections import (
    SECTION_TITLES,
    export_mode_sections,
    export_section_title,
    known_export_sections,
    normalize_export_section,
    repository_export_has_section,
    repository_export_populated_sections,
    repository_export_section_presence,
    repository_export_sections,
)
from repodossier.export_model_serialization import (
    repository_export_to_dict,
    to_plain_data,
)
from repodossier.export_model_snapshot import (
    repository_export_fingerprint,
    repository_export_snapshot_header,
    repository_export_snapshot_lines,
    repository_export_to_json,
)
from repodossier.export_model_summary import (
    build_export_summary,
    build_export_summary_from_export,
    count_files_by_language,
    count_files_by_status,
    file_type_statistics_from_files,
    language_statistics_from_files,
)
from repodossier.export_model_tree import (
    build_file_tree,
    build_file_tree_from_entries,
    build_file_tree_from_export,
    flatten_file_tree,
    tree_paths,
)
from repodossier.export_model_view import (
    RepositoryExportView,
    repository_export_files_for_section,
    repository_export_section_titles,
    repository_export_view,
    repository_export_warning_lines,
)
from repodossier.export_model_warnings import (
    append_export_warnings,
    make_export_warning,
    normalize_export_warnings,
    warning_counts_by_code,
    warning_messages,
    warnings_by_path,
)


__all__ = (
    "CallGraphReport",
    "DatabaseSchemaReport",
    "DependencyReport",
    "ExportConfigurationSummary",
    "ExportMode",
    "ExportModelValidationError",
    "ExportSummary",
    "ExportWarning",
    "FileEntry",
    "FileStatus",
    "FileTreeEntry",
    "ImportGraphReport",
    "LanguageStatistics",
    "MODE_DEFAULT_SECTIONS",
    "MODE_TITLES",
    "RecentCommitReport",
    "RepositoryExport",
    "RepositoryMetadata",
    "SecretDetectionSummary",
    "SymbolIndex",
    "TestMapReport",
    "TextStatus",
    "VALID_EXPORT_MODES",
    "ancestor_export_paths",
    "append_export_warnings",
    "assert_valid_repository_export",
    "build_export_summary",
    "build_export_summary_from_export",
    "build_file_tree",
    "build_file_tree_from_entries",
    "build_file_tree_from_export",
    "content_line_count",
    "content_size_bytes",
    "count_files_by_language",
    "count_files_by_status",
    "empty_repository_export",
    "estimate_tokens_from_content",
    "export_mode_default_sections",
    "export_mode_includes_source_content",
    "export_mode_is_review_focused",
    "export_mode_title",
    "export_path_depth",
    "export_path_name",
    "export_path_parent",
    "export_path_sort_key",
    "file_entry_content_for_rendering",
    "file_entry_has_exportable_content",
    "file_index_by_path",
    "file_type_statistics_from_files",
    "files_by_language",
    "files_by_status",
    "filter_files_by_language",
    "filter_files_by_status",
    "finalize_repository_export",
    "flatten_file_tree",
    "get_file_entry",
    "is_valid_export_mode",
    "iter_known_files",
    "language_counts_from_export",
    "language_statistics_from_files",
    "make_call_graph_report",
    "make_database_schema_report",
    "make_dependency_report",
    "make_export_configuration_summary",
    "make_export_warning",
    "make_file_entry_from_content",
    "make_import_graph_report",
    "make_minimal_repository_export",
    "make_recent_commit_report",
    "make_repository_export",
    "make_repository_metadata",
    "make_secret_detection_summary",
    "make_symbol_index",
    "make_test_map_report",
    "merge_configuration_summaries",
    "normalize_configuration_mapping",
    "normalize_configuration_paths",
    "normalize_configuration_patterns",
    "normalize_export_mode",
    "normalize_export_path",
    "normalize_export_paths",
    "normalize_export_warnings",
    "normalize_optional_text",
    "normalize_repository_root_name",
    "normalize_repository_root_path",
    "normalize_report_items",
    "normalize_report_mapping",
    "refresh_repository_export_derived_sections",
    "replace_repository_export_files",
    "repository_export_default_sections",
    "repository_export_title",
    "repository_export_to_dict",
    "repository_export_with_files",
    "repository_metadata_display_name",
    "repository_metadata_has_git",
    "repository_name_from_root_path",
    "sort_export_paths",
    "status_counts_from_export",
    "to_plain_data",
    "tree_paths",
    "update_repository_git_metadata",
    "validate_repository_export",
    "warning_counts_by_code",
    "warning_messages",
    "warnings_by_path",
)

__all__ = tuple(sorted(__all__))

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "file_entries_from_mappings",
            "file_entries_from_objects",
            "file_entry_from_mapping",
            "file_entry_from_object",
            "repository_export_fingerprint",
            "repository_export_snapshot_header",
            "repository_export_snapshot_lines",
            "repository_export_to_json",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "REQUIRED_EXPORT_MODEL_API_SYMBOLS",
            "REQUIRED_EXPORT_MODEL_SECTIONS",
            "ExportModelContractError",
            "ExportModelContractStatus",
            "assert_export_model_contract",
            "export_model_contract_status",
            "export_model_section_presence",
            "missing_export_model_api_symbols",
            "missing_export_model_sections",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "SECTION_TITLES",
            "export_mode_sections",
            "export_section_title",
            "known_export_sections",
            "normalize_export_section",
            "repository_export_has_section",
            "repository_export_populated_sections",
            "repository_export_section_presence",
            "repository_export_sections",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "FileEntryPartitions",
            "partition_file_entries",
            "repository_export_from_file_entries",
            "repository_export_from_file_mappings",
            "repository_export_from_file_objects",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "FILE_COMPARE_FIELDS",
            "FileEntryChange",
            "RepositoryExportComparison",
            "compare_file_entries",
            "compare_repository_exports",
            "repository_export_path_delta",
            "repository_exports_have_same_paths",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "RepositoryExportManifest",
            "repository_export_manifest",
            "repository_export_manifest_lines",
            "repository_export_manifest_to_dict",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "RepositoryExportView",
            "repository_export_files_for_section",
            "repository_export_section_titles",
            "repository_export_view",
            "repository_export_warning_lines",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "FileInventoryEntry",
            "FileInventoryGroup",
            "repository_export_file_inventory",
            "repository_export_file_inventory_by_group",
            "repository_export_file_inventory_lines",
            "repository_export_file_inventory_to_dicts",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "repository_export_from_dict",
            "repository_export_from_json",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "RepositoryExportRoundTripError",
            "RepositoryExportRoundTripStatus",
            "assert_repository_export_round_trips",
            "repository_export_canonical_dict",
            "repository_export_round_trip",
            "repository_export_round_trip_status",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "RepositoryExportAuditError",
            "RepositoryExportAuditResult",
            "assert_repository_export_audit",
            "audit_repository_export",
            "repository_export_audit_lines",
        }
    )
)

__all__ = tuple(
    sorted(
        set(__all__)
        | {
            "RepositoryExportReadinessError",
            "RepositoryExportReadinessStatus",
            "assert_repository_export_ready",
            "repository_export_readiness_lines",
            "repository_export_readiness_status",
        }
    )
)
