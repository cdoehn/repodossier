"""Acceptance contract checks for RepoDossier's structured export model."""

from __future__ import annotations

from dataclasses import dataclass

from repodossier.export_model import RepositoryExport, validate_repository_export
from repodossier.export_model_snapshot import repository_export_fingerprint


REQUIRED_EXPORT_MODEL_SECTIONS: tuple[str, ...] = (
    "mode",
    "repository",
    "configuration",
    "summary",
    "tree",
    "files",
    "omitted_files",
    "truncated_files",
    "warnings",
    "dependencies",
    "database_schema",
    "secret_detection",
    "symbol_index",
    "import_graph",
    "call_graph",
    "test_map",
    "recent_commits",
)

REQUIRED_EXPORT_MODEL_API_SYMBOLS: tuple[str, ...] = (
    "RepositoryExport",
    "RepositoryMetadata",
    "FileEntry",
    "FileTreeEntry",
    "ExportConfigurationSummary",
    "ExportSummary",
    "ExportWarning",
    "DependencyReport",
    "DatabaseSchemaReport",
    "SecretDetectionSummary",
    "SymbolIndex",
    "ImportGraphReport",
    "CallGraphReport",
    "TestMapReport",
    "RecentCommitReport",
    "make_repository_export",
    "make_minimal_repository_export",
    "make_file_entry_from_content",
    "make_export_configuration_summary",
    "make_export_warning",
    "make_dependency_report",
    "make_database_schema_report",
    "make_secret_detection_summary",
    "make_symbol_index",
    "make_import_graph_report",
    "make_call_graph_report",
    "make_test_map_report",
    "make_recent_commit_report",
    "repository_export_to_dict",
    "repository_export_to_json",
    "repository_export_fingerprint",
    "validate_repository_export",
    "assert_valid_repository_export",
)


class ExportModelContractError(AssertionError):
    """Raised when the export model contract is incomplete or invalid."""


@dataclass(frozen=True)
class ExportModelContractStatus:
    """Result of checking an export model against the Milestone 3 contract."""

    valid: bool
    issues: tuple[str, ...]
    missing_sections: tuple[str, ...]
    missing_api_symbols: tuple[str, ...]
    fingerprint: str


def export_model_section_presence(export: RepositoryExport) -> dict[str, bool]:
    """Return whether every required export model section is present."""

    return {
        section: hasattr(export, section) and getattr(export, section) is not None
        for section in REQUIRED_EXPORT_MODEL_SECTIONS
    }


def missing_export_model_sections(export: RepositoryExport) -> tuple[str, ...]:
    """Return required export model sections that are absent or None."""

    presence = export_model_section_presence(export)
    return tuple(
        section
        for section in REQUIRED_EXPORT_MODEL_SECTIONS
        if not presence[section]
    )


def missing_export_model_api_symbols() -> tuple[str, ...]:
    """Return required public facade symbols that are currently missing."""

    import repodossier.export_model_api as api

    return tuple(
        symbol
        for symbol in REQUIRED_EXPORT_MODEL_API_SYMBOLS
        if not hasattr(api, symbol)
    )


def export_model_contract_status(
    export: RepositoryExport,
    *,
    include_content_in_fingerprint: bool = False,
) -> ExportModelContractStatus:
    """Check an export model against the Milestone 3 internal model contract."""

    validation_issues = validate_repository_export(export)
    missing_sections = missing_export_model_sections(export)
    missing_api_symbols = missing_export_model_api_symbols()

    issues = tuple(
        list(validation_issues)
        + [
            f"missing export model section: {section}"
            for section in missing_sections
        ]
        + [
            f"missing export model API symbol: {symbol}"
            for symbol in missing_api_symbols
        ]
    )

    return ExportModelContractStatus(
        valid=not issues,
        issues=issues,
        missing_sections=missing_sections,
        missing_api_symbols=missing_api_symbols,
        fingerprint=repository_export_fingerprint(
            export,
            include_content=include_content_in_fingerprint,
        ),
    )


def assert_export_model_contract(export: RepositoryExport) -> None:
    """Raise ExportModelContractError if the export model contract is not met."""

    status = export_model_contract_status(export)
    if status.valid:
        return

    formatted = "\n".join(f"- {issue}" for issue in status.issues)
    raise ExportModelContractError(
        f"Export model contract is not satisfied:\n{formatted}"
    )

REQUIRED_EXPORT_MODEL_API_SYMBOLS = tuple(sorted(REQUIRED_EXPORT_MODEL_API_SYMBOLS))

REQUIRED_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        set(REQUIRED_EXPORT_MODEL_API_SYMBOLS)
        | {
            "repository_export_from_dict",
            "repository_export_from_json",
        }
    )
)

REQUIRED_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        set(REQUIRED_EXPORT_MODEL_API_SYMBOLS)
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

CONTRACT_HELPER_API_SYMBOLS = tuple(
    sorted(
        {
            "FILE_COMPARE_FIELDS",
            "FileEntryChange",
            "FileInventoryEntry",
            "FileInventoryGroup",
            "RepositoryExportComparison",
            "RepositoryExportManifest",
            "RepositoryExportRoundTripError",
            "RepositoryExportRoundTripStatus",
            "RepositoryExportView",
            "assert_repository_export_round_trips",
            "compare_file_entries",
            "compare_repository_exports",
            "repository_export_canonical_dict",
            "repository_export_file_inventory",
            "repository_export_file_inventory_by_group",
            "repository_export_file_inventory_lines",
            "repository_export_file_inventory_to_dicts",
            "repository_export_files_for_section",
            "repository_export_from_dict",
            "repository_export_from_json",
            "repository_export_manifest",
            "repository_export_manifest_lines",
            "repository_export_manifest_to_dict",
            "repository_export_path_delta",
            "repository_export_round_trip",
            "repository_export_round_trip_status",
            "repository_export_section_titles",
            "repository_export_view",
            "repository_export_warning_lines",
            "repository_exports_have_same_paths",
        }
    )
)


REQUIRED_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        set(REQUIRED_EXPORT_MODEL_API_SYMBOLS)
        | set(CONTRACT_HELPER_API_SYMBOLS)
    )
)

AUDIT_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        {
            "RepositoryExportAuditError",
            "RepositoryExportAuditResult",
            "assert_repository_export_audit",
            "audit_repository_export",
            "repository_export_audit_lines",
        }
    )
)


CONTRACT_HELPER_API_SYMBOLS = tuple(
    sorted(
        set(globals().get("CONTRACT_HELPER_API_SYMBOLS", ()))
        | set(AUDIT_EXPORT_MODEL_API_SYMBOLS)
    )
)


REQUIRED_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        set(REQUIRED_EXPORT_MODEL_API_SYMBOLS)
        | set(AUDIT_EXPORT_MODEL_API_SYMBOLS)
    )
)

READINESS_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        {
            "RepositoryExportReadinessError",
            "RepositoryExportReadinessStatus",
            "assert_repository_export_ready",
            "repository_export_readiness_lines",
            "repository_export_readiness_status",
        }
    )
)


CONTRACT_HELPER_API_SYMBOLS = tuple(
    sorted(
        set(globals().get("CONTRACT_HELPER_API_SYMBOLS", ()))
        | set(READINESS_EXPORT_MODEL_API_SYMBOLS)
    )
)


REQUIRED_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        set(REQUIRED_EXPORT_MODEL_API_SYMBOLS)
        | set(READINESS_EXPORT_MODEL_API_SYMBOLS)
    )
)

SELFTEST_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        {
            "ExportModelSelfTestError",
            "ExportModelSelfTestResult",
            "assert_export_model_selftest",
            "export_model_selftest_lines",
            "make_export_model_selftest_export",
            "run_export_model_selftest",
        }
    )
)


CONTRACT_HELPER_API_SYMBOLS = tuple(
    sorted(
        set(globals().get("CONTRACT_HELPER_API_SYMBOLS", ()))
        | set(SELFTEST_EXPORT_MODEL_API_SYMBOLS)
    )
)


REQUIRED_EXPORT_MODEL_API_SYMBOLS = tuple(
    sorted(
        set(REQUIRED_EXPORT_MODEL_API_SYMBOLS)
        | set(SELFTEST_EXPORT_MODEL_API_SYMBOLS)
    )
)
