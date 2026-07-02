import json

import repodossier.export_model_api as api


def test_export_model_selftest_json_snapshot_is_deterministic():
    export = api.make_export_model_selftest_export()

    first = api.repository_export_to_json(export)
    second = api.repository_export_to_json(export)

    assert first == second

    data = json.loads(first)

    assert data["mode"] == "full"
    assert data["repository"] == {
        "git_branch": None,
        "git_commit": None,
        "git_dirty": None,
        "root_name": "repo",
        "root_path": "/repo",
    }
    assert [entry["path"] for entry in data["files"]] == [
        "README.md",
        "src/app.py",
    ]
    assert [entry["path"] for entry in data["omitted_files"]] == [
        "assets/logo.png",
    ]
    assert [entry["path"] for entry in data["truncated_files"]] == [
        "logs/large.log",
    ]
    assert [warning["code"] for warning in data["warnings"]] == [
        "binary",
        "truncated",
    ]


def test_export_model_selftest_fingerprint_is_stable_for_same_content():
    export = api.make_export_model_selftest_export()

    assert api.repository_export_fingerprint(export) == api.repository_export_fingerprint(
        api.repository_export_from_json(api.repository_export_to_json(export))
    )

    without_content = api.repository_export_fingerprint(
        export,
        include_content=False,
    )
    restored_without_content = api.repository_export_from_dict(
        api.repository_export_to_dict(export, include_content=False)
    )

    assert without_content == api.repository_export_fingerprint(
        restored_without_content,
        include_content=False,
    )


def test_export_model_selftest_snapshot_header_is_stable_shape():
    export = api.make_export_model_selftest_export()

    header = api.repository_export_snapshot_header(export)

    assert header["mode"] == "full"
    assert header["root_name"] == "repo"
    assert len(header["fingerprint"]) == 64
    assert "root_path" not in header
    assert "include_content" not in header


def test_export_model_selftest_manifest_and_readiness_align():
    export = api.make_export_model_selftest_export()

    manifest = api.repository_export_manifest(export)
    readiness = api.repository_export_readiness_status(export)

    assert readiness.valid
    assert readiness.fingerprint == manifest.fingerprint
    assert readiness.title == manifest.title
    assert manifest.mode == export.mode
    assert manifest.file_count == len(export.files)
    assert manifest.omitted_file_count == len(export.omitted_files)
    assert manifest.truncated_file_count == len(export.truncated_files)
    assert manifest.warning_count == len(export.warnings)


def test_export_model_selftest_plain_dict_without_content_is_safe_for_ai_metadata():
    export = api.make_export_model_selftest_export()

    data = api.repository_export_to_dict(export, include_content=False)

    assert all("content" not in entry for entry in data["files"])
    assert all("masked_content" not in entry for entry in data["files"])
    assert all("content" not in entry for entry in data["truncated_files"])
    assert all(
        "masked_content" not in entry
        for entry in data["truncated_files"]
    )

    restored = api.repository_export_from_dict(data)

    assert all(entry.content is None for entry in restored.files)
    assert all(entry.masked_content is None for entry in restored.files)
    assert all(entry.content is None for entry in restored.truncated_files)
    assert all(
        entry.masked_content is None
        for entry in restored.truncated_files
    )
