import pytest

from repodossier.export_model import FileEntry, RepositoryExport, RepositoryMetadata
from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_reports import make_dependency_report
from repodossier.export_model_roundtrip import (
    RepositoryExportRoundTripError,
    RepositoryExportRoundTripStatus,
    assert_repository_export_round_trips,
    repository_export_canonical_dict,
    repository_export_round_trip,
    repository_export_round_trip_status,
)
from repodossier.export_model_serialization import repository_export_to_dict
from repodossier.export_model_warnings import make_export_warning


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
        warnings=(
            make_export_warning(
                "Large file truncated",
                path="large.log",
                code="truncated",
            ),
        ),
        dependencies=make_dependency_report(
            ({"package": "pytest", "source": "pyproject.toml"},)
        ),
    )


def test_repository_export_round_trip_restores_equivalent_model():
    original = make_export()

    restored = repository_export_round_trip(original)

    assert restored == original
    assert restored is not original


def test_repository_export_round_trip_can_omit_content():
    original = make_export()

    restored = repository_export_round_trip(
        original,
        include_content=False,
    )

    assert restored.files[0].path == original.files[0].path
    assert restored.files[0].content is None
    assert restored.truncated_files[0].content is None


def test_repository_export_canonical_dict_matches_serialized_data():
    export = make_export()

    assert repository_export_canonical_dict(export) == repository_export_to_dict(export)


def test_repository_export_round_trip_status_reports_success():
    status = repository_export_round_trip_status(make_export())

    assert isinstance(status, RepositoryExportRoundTripStatus)
    assert status.valid
    assert status.issues == ()
    assert len(status.before_fingerprint) == 64
    assert status.before_fingerprint == status.after_fingerprint
    assert status.same_fingerprint is True


def test_assert_repository_export_round_trips_accepts_valid_export():
    assert_repository_export_round_trips(make_export())


def test_repository_export_round_trip_status_reports_deserialization_failure():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
    )

    status = repository_export_round_trip_status(export)

    assert not status.valid
    assert status.after_fingerprint == ""
    assert status.same_fingerprint is False
    assert status.issues
    assert status.issues[0].startswith("deserialization failed:")


def test_assert_repository_export_round_trips_raises_useful_error():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
    )

    with pytest.raises(RepositoryExportRoundTripError) as exc_info:
        assert_repository_export_round_trips(export)

    assert "RepositoryExport does not round-trip cleanly:" in str(exc_info.value)


def test_repository_export_round_trip_status_can_skip_validation():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
        files=(
            FileEntry(path="", language="python"),
        ),
    )

    status = repository_export_round_trip_status(
        export,
        validate=False,
    )

    assert status.valid
    assert status.same_fingerprint is True
