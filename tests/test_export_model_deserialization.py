import json

import pytest

from repodossier.export_model import ExportModelValidationError, RepositoryExport
from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_deserialization import (
    repository_export_from_dict,
    repository_export_from_json,
)
from repodossier.export_model_reports import (
    make_dependency_report,
    make_recent_commit_report,
)
from repodossier.export_model_serialization import repository_export_to_dict
from repodossier.export_model_snapshot import repository_export_to_json
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
        recent_commits=make_recent_commit_report(
            ({"short_hash": "abc1234", "message": "Example"},)
        ),
    )


def test_repository_export_from_dict_round_trips_serialized_export():
    original = make_export()
    data = repository_export_to_dict(original)

    restored = repository_export_from_dict(data)

    assert isinstance(restored, RepositoryExport)
    assert restored == original


def test_repository_export_from_json_round_trips_snapshot_json():
    original = make_export()
    text = repository_export_to_json(original)

    restored = repository_export_from_json(text)

    assert restored == original


def test_repository_export_from_dict_defaults_optional_sections():
    restored = repository_export_from_dict(
        {
            "mode": "full",
            "repository": {
                "root_path": "/repo",
                "root_name": "repo",
            },
        }
    )

    assert restored.mode == "full"
    assert restored.repository.root_path == "/repo"
    assert restored.configuration.config_active is False
    assert restored.summary.total_tracked_files == 0
    assert restored.files == ()
    assert restored.dependencies.items == ()
    assert restored.recent_commits.commits == ()


def test_repository_export_from_dict_can_skip_validation():
    data = {
        "mode": "full",
        "repository": {
            "root_path": "",
            "root_name": "repo",
        },
    }

    with pytest.raises(ExportModelValidationError):
        repository_export_from_dict(data)

    restored = repository_export_from_dict(data, validate=False)

    assert restored.repository.root_path == ""


def test_repository_export_from_json_requires_top_level_object():
    with pytest.raises(ValueError, match="must contain an object"):
        repository_export_from_json(json.dumps([]))


def test_repository_export_from_dict_requires_mode_and_repository():
    with pytest.raises(ValueError, match="missing required field: mode"):
        repository_export_from_dict(
            {
                "repository": {
                    "root_path": "/repo",
                    "root_name": "repo",
                }
            }
        )

    with pytest.raises(ValueError, match="missing required field: repository"):
        repository_export_from_dict({"mode": "full"})


def test_repository_export_from_dict_rejects_non_sequence_files():
    with pytest.raises(ValueError, match="file entries must be a sequence"):
        repository_export_from_dict(
            {
                "mode": "full",
                "repository": {
                    "root_path": "/repo",
                    "root_name": "repo",
                },
                "files": "not-a-sequence",
            }
        )


def test_repository_export_from_dict_restores_nested_tree_and_reports():
    data = repository_export_to_dict(make_export())

    restored = repository_export_from_dict(data)

    assert restored.tree
    assert restored.tree[0].children
    assert restored.dependencies.items == (
        {"package": "pytest", "source": "pyproject.toml"},
    )
    assert restored.recent_commits.commits == (
        {"short_hash": "abc1234", "message": "Example"},
    )
