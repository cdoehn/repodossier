from dataclasses import replace

import pytest

from repodossier.export_model import (
    ExportSummary,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_readiness import (
    RepositoryExportReadinessError,
    RepositoryExportReadinessStatus,
    assert_repository_export_ready,
    repository_export_readiness_lines,
    repository_export_readiness_status,
)


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
        ),
    )


def test_repository_export_readiness_status_accepts_ready_export():
    status = repository_export_readiness_status(make_export())

    assert isinstance(status, RepositoryExportReadinessStatus)
    assert status.valid
    assert status.issues == ()
    assert status.title == "Full Repository Export"
    assert len(status.fingerprint) == 64
    assert status.contract_valid is True
    assert status.audit_valid is True
    assert status.contract_issues == ()
    assert status.audit_issues == ()


def test_assert_repository_export_ready_accepts_ready_export():
    assert_repository_export_ready(make_export())


def test_repository_export_readiness_lines_are_stable_for_ready_export():
    lines = repository_export_readiness_lines(make_export())

    assert lines[:4] == (
        "title=Full Repository Export",
        "valid=True",
        "contract_valid=True",
        "audit_valid=True",
    )
    assert lines[4].startswith("fingerprint=")
    assert len(lines[4].removeprefix("fingerprint=")) == 64


def test_repository_export_readiness_status_reports_audit_issues():
    export = replace(
        make_export(),
        summary=ExportSummary(total_tracked_files=999),
    )

    status = repository_export_readiness_status(export)

    assert not status.valid
    assert status.contract_valid is True
    assert status.audit_valid is False
    assert "summary does not match exported file entries" in status.audit_issues
    assert "audit: summary does not match exported file entries" in status.issues


def test_repository_export_readiness_status_reports_contract_and_audit_issues():
    export = RepositoryExport(
        mode="invalid",
        repository=RepositoryMetadata(root_path="", root_name=""),
    )

    status = repository_export_readiness_status(export)

    assert not status.valid
    assert status.contract_valid is False
    assert status.audit_valid is False
    assert status.contract_issues
    assert status.audit_issues
    assert any(issue.startswith("contract:") for issue in status.issues)
    assert any(issue.startswith("audit:") for issue in status.issues)


def test_assert_repository_export_ready_raises_useful_error():
    export = replace(
        make_export(),
        summary=ExportSummary(total_tracked_files=999),
    )

    with pytest.raises(RepositoryExportReadinessError) as exc_info:
        assert_repository_export_ready(export)

    assert "RepositoryExport is not ready:" in str(exc_info.value)
    assert "summary does not match exported file entries" in str(exc_info.value)


def test_repository_export_readiness_lines_include_issues():
    export = replace(
        make_export(),
        summary=ExportSummary(total_tracked_files=999),
    )

    lines = repository_export_readiness_lines(export)

    assert lines[0] == "title=Full Repository Export"
    assert lines[1] == "valid=False"
    assert lines[2] == "contract_valid=True"
    assert lines[3] == "audit_valid=False"
    assert lines[5] == "issues:"
    assert "- audit: summary does not match exported file entries" in lines


def test_repository_export_readiness_can_disable_roundtrip_check():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
    )

    status = repository_export_readiness_status(
        export,
        check_round_trip=False,
    )

    assert not status.valid
    assert not any("round trip:" in issue for issue in status.issues)
