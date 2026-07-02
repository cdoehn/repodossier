"""Self-test helpers for RepoDossier's structured export model."""

from __future__ import annotations

from dataclasses import dataclass

from repodossier.export_model import RepositoryExport
from repodossier.export_model_audit import audit_repository_export
from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_contract import export_model_contract_status
from repodossier.export_model_readiness import repository_export_readiness_status
from repodossier.export_model_roundtrip import repository_export_round_trip_status
from repodossier.export_model_warnings import make_export_warning


@dataclass(frozen=True)
class ExportModelSelfTestResult:
    """Result of the built-in structured export model self-test."""

    valid: bool
    issues: tuple[str, ...]
    export: RepositoryExport
    contract_valid: bool
    audit_valid: bool
    readiness_valid: bool
    round_trip_valid: bool


class ExportModelSelfTestError(AssertionError):
    """Raised when the structured export model self-test fails."""


def make_export_model_selftest_export() -> RepositoryExport:
    """Create a small representative RepositoryExport for self-tests."""

    return repository_export_from_file_mappings(
        mode="full",
        root_path="/repo",
        root_name="repo",
        mappings=(
            {
                "path": "README.md",
                "language": "markdown",
                "content": "# Repo\n",
            },
            {
                "path": "src/app.py",
                "language": "python",
                "content": "print('hello')\n",
            },
            {
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
                "size": 128,
                "skip_reason": "binary file",
            },
            {
                "path": "logs/large.log",
                "language": "text",
                "content": "partial log",
                "truncated": True,
                "skip_reason": "too large",
            },
        ),
        warnings=(
            make_export_warning(
                "Binary file skipped",
                path="assets/logo.png",
                code="binary",
            ),
            make_export_warning(
                "Large file truncated",
                path="logs/large.log",
                code="truncated",
            ),
        ),
    )


def run_export_model_selftest() -> ExportModelSelfTestResult:
    """Run contract, audit, readiness, and round-trip checks."""

    export = make_export_model_selftest_export()
    contract_status = export_model_contract_status(export)
    audit_result = audit_repository_export(export)
    readiness_status = repository_export_readiness_status(export)
    round_trip_status = repository_export_round_trip_status(export)

    issues = tuple(
        [f"contract: {issue}" for issue in contract_status.issues]
        + [f"audit: {issue}" for issue in audit_result.issues]
        + [f"readiness: {issue}" for issue in readiness_status.issues]
        + [f"round trip: {issue}" for issue in round_trip_status.issues]
    )

    return ExportModelSelfTestResult(
        valid=(
            contract_status.valid
            and audit_result.valid
            and readiness_status.valid
            and round_trip_status.valid
        ),
        issues=issues,
        export=export,
        contract_valid=contract_status.valid,
        audit_valid=audit_result.valid,
        readiness_valid=readiness_status.valid,
        round_trip_valid=round_trip_status.valid,
    )


def assert_export_model_selftest() -> None:
    """Raise if the structured export model self-test fails."""

    result = run_export_model_selftest()

    if result.valid:
        return

    formatted = "\n".join(f"- {issue}" for issue in result.issues)
    raise ExportModelSelfTestError(
        f"Export model self-test failed:\n{formatted}"
    )


def export_model_selftest_lines() -> tuple[str, ...]:
    """Return stable human-readable self-test lines."""

    result = run_export_model_selftest()

    lines = [
        f"valid={result.valid}",
        f"contract_valid={result.contract_valid}",
        f"audit_valid={result.audit_valid}",
        f"readiness_valid={result.readiness_valid}",
        f"round_trip_valid={result.round_trip_valid}",
        f"files={len(result.export.files)}",
        f"omitted_files={len(result.export.omitted_files)}",
        f"truncated_files={len(result.export.truncated_files)}",
        f"warnings={len(result.export.warnings)}",
    ]

    if result.issues:
        lines.append("issues:")
        lines.extend(f"- {issue}" for issue in result.issues)

    return tuple(lines)
