"""Consistency audit helpers for RepoDossier's structured export model."""

from __future__ import annotations

from dataclasses import dataclass

from repodossier.export_model import RepositoryExport, validate_repository_export
from repodossier.export_model_inventory import repository_export_file_inventory
from repodossier.export_model_roundtrip import repository_export_round_trip_status
from repodossier.export_model_summary import build_export_summary_from_export
from repodossier.export_model_tree import build_file_tree_from_export


@dataclass(frozen=True)
class RepositoryExportAuditResult:
    """Detailed result of a RepositoryExport consistency audit."""

    valid: bool
    issues: tuple[str, ...]
    validation_issues: tuple[str, ...]
    summary_matches: bool
    tree_matches: bool
    inventory_matches: bool
    round_trip_matches: bool


class RepositoryExportAuditError(AssertionError):
    """Raised when a RepositoryExport audit fails."""


def audit_repository_export(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    check_round_trip: bool = True,
) -> RepositoryExportAuditResult:
    """Audit validation, derived sections, inventory, and round-trip safety."""

    issues: list[str] = []

    validation_issues = validate_repository_export(export)
    for issue in validation_issues:
        issues.append(f"validation: {issue}")

    summary_matches = _summary_matches(export, issues)
    tree_matches = _tree_matches(export, issues)
    inventory_matches = _inventory_matches(export, issues)
    round_trip_matches = _round_trip_matches(
        export,
        issues,
        include_content=include_content,
        check_round_trip=check_round_trip,
    )

    return RepositoryExportAuditResult(
        valid=not issues,
        issues=tuple(issues),
        validation_issues=tuple(validation_issues),
        summary_matches=summary_matches,
        tree_matches=tree_matches,
        inventory_matches=inventory_matches,
        round_trip_matches=round_trip_matches,
    )


def assert_repository_export_audit(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    check_round_trip: bool = True,
) -> None:
    """Raise if a RepositoryExport audit finds inconsistencies."""

    result = audit_repository_export(
        export,
        include_content=include_content,
        check_round_trip=check_round_trip,
    )

    if result.valid:
        return

    formatted = "\n".join(f"- {issue}" for issue in result.issues)
    raise RepositoryExportAuditError(
        f"RepositoryExport audit failed:\n{formatted}"
    )


def repository_export_audit_lines(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    check_round_trip: bool = True,
) -> tuple[str, ...]:
    """Return a stable human-readable audit summary."""

    result = audit_repository_export(
        export,
        include_content=include_content,
        check_round_trip=check_round_trip,
    )

    lines = [
        f"valid={result.valid}",
        f"summary_matches={result.summary_matches}",
        f"tree_matches={result.tree_matches}",
        f"inventory_matches={result.inventory_matches}",
        f"round_trip_matches={result.round_trip_matches}",
    ]

    if result.issues:
        lines.append("issues:")
        lines.extend(f"- {issue}" for issue in result.issues)

    return tuple(lines)


def _summary_matches(export: RepositoryExport, issues: list[str]) -> bool:
    expected = build_export_summary_from_export(export)

    if expected == export.summary:
        return True

    issues.append("summary does not match exported file entries")
    return False


def _tree_matches(export: RepositoryExport, issues: list[str]) -> bool:
    try:
        expected = build_file_tree_from_export(export)
    except Exception as exc:
        issues.append(f"tree could not be rebuilt: {exc}")
        return False

    if expected == export.tree:
        return True

    issues.append("tree does not match exported file entries")
    return False


def _inventory_matches(export: RepositoryExport, issues: list[str]) -> bool:
    expected_paths = tuple(
        sorted(
            entry.path
            for entry in (
                export.files
                + export.omitted_files
                + export.truncated_files
            )
        )
    )
    inventory_paths = tuple(
        entry.path
        for entry in repository_export_file_inventory(export)
    )

    if inventory_paths == expected_paths:
        return True

    issues.append("file inventory does not match known file entries")
    return False


def _round_trip_matches(
    export: RepositoryExport,
    issues: list[str],
    *,
    include_content: bool,
    check_round_trip: bool,
) -> bool:
    if not check_round_trip:
        return True

    status = repository_export_round_trip_status(
        export,
        include_content=include_content,
    )

    if status.valid:
        return True

    for issue in status.issues:
        issues.append(f"round trip: {issue}")

    return False
