from dataclasses import replace

import pytest

from repodossier.export_model import (
    ExportSummary,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.export_model_audit import (
    RepositoryExportAuditError,
    RepositoryExportAuditResult,
    assert_repository_export_audit,
    audit_repository_export,
    repository_export_audit_lines,
)
from repodossier.export_model_collector import repository_export_from_file_mappings


def make_export():
    return repository_export_from_file_mappings(
        mode="full",
        root_path="/repo",
        root_name="repo",
        mappings=(
            {
                "path": "src/app.py",
                "language": "python",
                "content": "print(1)\n",
            },
            {
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
                "size": 123,
                "skip_reason": "binary file",
            },
            {
                "path": "large.log",
                "language": "text",
                "content": "partial",
                "truncated": True,
            },
        ),
    )


def test_audit_repository_export_accepts_consistent_export():
    result = audit_repository_export(make_export())

    assert isinstance(result, RepositoryExportAuditResult)
    assert result.valid
    assert result.issues == ()
    assert result.validation_issues == ()
    assert result.summary_matches is True
    assert result.tree_matches is True
    assert result.inventory_matches is True
    assert result.round_trip_matches is True


def test_assert_repository_export_audit_accepts_consistent_export():
    assert_repository_export_audit(make_export())


def test_repository_export_audit_lines_are_stable_for_valid_export():
    lines = repository_export_audit_lines(make_export())

    assert lines == (
        "valid=True",
        "summary_matches=True",
        "tree_matches=True",
        "inventory_matches=True",
        "round_trip_matches=True",
    )


def test_audit_repository_export_detects_stale_summary():
    export = replace(
        make_export(),
        summary=ExportSummary(total_tracked_files=999),
    )

    result = audit_repository_export(export)

    assert not result.valid
    assert result.summary_matches is False
    assert "summary does not match exported file entries" in result.issues


def test_audit_repository_export_detects_stale_tree():
    export = replace(make_export(), tree=())

    result = audit_repository_export(export)

    assert not result.valid
    assert result.tree_matches is False
    assert "tree does not match exported file entries" in result.issues


def test_audit_repository_export_reports_validation_and_roundtrip_issues():
    export = RepositoryExport(
        mode="invalid",
        repository=RepositoryMetadata(root_path="", root_name=""),
    )

    result = audit_repository_export(export)

    assert not result.valid
    assert result.validation_issues
    assert any(issue.startswith("validation:") for issue in result.issues)
    assert any(issue.startswith("round trip:") for issue in result.issues)


def test_audit_repository_export_can_skip_round_trip_check():
    export = RepositoryExport(
        mode="invalid",
        repository=RepositoryMetadata(root_path="", root_name=""),
    )

    result = audit_repository_export(export, check_round_trip=False)

    assert not result.valid
    assert result.round_trip_matches is True
    assert not any(issue.startswith("round trip:") for issue in result.issues)


def test_assert_repository_export_audit_raises_useful_error():
    export = replace(
        make_export(),
        summary=ExportSummary(total_tracked_files=999),
    )

    with pytest.raises(RepositoryExportAuditError) as exc_info:
        assert_repository_export_audit(export)

    assert "RepositoryExport audit failed:" in str(exc_info.value)
    assert "summary does not match exported file entries" in str(exc_info.value)


def test_repository_export_audit_lines_include_issues():
    export = replace(make_export(), tree=())

    lines = repository_export_audit_lines(export)

    assert lines[:5] == (
        "valid=False",
        "summary_matches=True",
        "tree_matches=False",
        "inventory_matches=True",
        "round_trip_matches=True",
    )
    assert lines[5] == "issues:"
    assert "- tree does not match exported file entries" in lines
