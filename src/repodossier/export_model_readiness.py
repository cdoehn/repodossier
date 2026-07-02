"""Readiness checks for RepoDossier's structured export model."""

from __future__ import annotations

from dataclasses import dataclass

from repodossier.export_model import RepositoryExport
from repodossier.export_model_audit import audit_repository_export
from repodossier.export_model_contract import export_model_contract_status
from repodossier.export_model_modes import repository_export_title
from repodossier.export_model_snapshot import repository_export_fingerprint


@dataclass(frozen=True)
class RepositoryExportReadinessStatus:
    """Combined readiness status for a structured repository export."""

    valid: bool
    issues: tuple[str, ...]
    title: str
    fingerprint: str
    contract_valid: bool
    audit_valid: bool
    contract_issues: tuple[str, ...]
    audit_issues: tuple[str, ...]


class RepositoryExportReadinessError(AssertionError):
    """Raised when a RepositoryExport is not ready for rendering."""


def repository_export_readiness_status(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    include_content_in_fingerprint: bool = False,
    check_round_trip: bool = True,
) -> RepositoryExportReadinessStatus:
    """Return a combined contract and audit readiness status."""

    contract_status = export_model_contract_status(
        export,
        include_content_in_fingerprint=include_content_in_fingerprint,
    )
    audit_result = audit_repository_export(
        export,
        include_content=include_content,
        check_round_trip=check_round_trip,
    )

    issues = tuple(
        [f"contract: {issue}" for issue in contract_status.issues]
        + [f"audit: {issue}" for issue in audit_result.issues]
    )

    return RepositoryExportReadinessStatus(
        valid=contract_status.valid and audit_result.valid,
        issues=issues,
        title=_safe_repository_export_title(export),
        fingerprint=repository_export_fingerprint(
            export,
            include_content=include_content_in_fingerprint,
        ),
        contract_valid=contract_status.valid,
        audit_valid=audit_result.valid,
        contract_issues=contract_status.issues,
        audit_issues=audit_result.issues,
    )


def assert_repository_export_ready(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    include_content_in_fingerprint: bool = False,
    check_round_trip: bool = True,
) -> None:
    """Raise if a structured export is not ready for rendering."""

    status = repository_export_readiness_status(
        export,
        include_content=include_content,
        include_content_in_fingerprint=include_content_in_fingerprint,
        check_round_trip=check_round_trip,
    )

    if status.valid:
        return

    formatted = "\n".join(f"- {issue}" for issue in status.issues)
    raise RepositoryExportReadinessError(
        f"RepositoryExport is not ready:\n{formatted}"
    )


def repository_export_readiness_lines(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    include_content_in_fingerprint: bool = False,
    check_round_trip: bool = True,
) -> tuple[str, ...]:
    """Return stable human-readable readiness lines."""

    status = repository_export_readiness_status(
        export,
        include_content=include_content,
        include_content_in_fingerprint=include_content_in_fingerprint,
        check_round_trip=check_round_trip,
    )

    lines = [
        f"title={status.title}",
        f"valid={status.valid}",
        f"contract_valid={status.contract_valid}",
        f"audit_valid={status.audit_valid}",
        f"fingerprint={status.fingerprint}",
    ]

    if status.issues:
        lines.append("issues:")
        lines.extend(f"- {issue}" for issue in status.issues)

    return tuple(lines)


def _safe_repository_export_title(export: RepositoryExport) -> str:
    try:
        return repository_export_title(export)
    except ValueError:
        return f"{export.mode} repository export"
