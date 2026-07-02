import repodossier.export_model_api as api


def test_public_api_e2e_selftest_export_roundtrip_readiness_and_manifest():
    export = api.make_export_model_selftest_export()

    json_text = api.repository_export_to_json(export)
    restored = api.repository_export_from_json(json_text)

    assert restored == export

    api.assert_repository_export_round_trips(restored)
    api.assert_repository_export_audit(restored)
    api.assert_repository_export_ready(restored)
    api.assert_export_model_contract(restored)

    readiness = api.repository_export_readiness_status(restored)
    manifest = api.repository_export_manifest(restored)
    comparison = api.compare_repository_exports(export, restored)

    assert readiness.valid
    assert readiness.title == "Full Repository Export"
    assert manifest.title == readiness.title
    assert manifest.fingerprint == readiness.fingerprint
    assert comparison.same
    assert comparison.same_fingerprint


def test_public_api_e2e_plain_data_without_content_stays_ready():
    export = api.make_export_model_selftest_export()

    data = api.repository_export_to_dict(export, include_content=False)
    restored = api.repository_export_from_dict(data)

    assert all(entry.content is None for entry in restored.files)
    assert all(entry.content is None for entry in restored.truncated_files)

    status = api.repository_export_readiness_status(
        restored,
        include_content=False,
    )

    assert status.valid
    assert status.issues == ()

    api.assert_repository_export_ready(
        restored,
        include_content=False,
    )


def test_public_api_e2e_lines_outputs_are_available_for_cli_or_docs():
    export = api.make_export_model_selftest_export()

    manifest_lines = api.repository_export_manifest_lines(export)
    inventory_lines = api.repository_export_file_inventory_lines(export)
    readiness_lines = api.repository_export_readiness_lines(export)
    audit_lines = api.repository_export_audit_lines(export)
    selftest_lines = api.export_model_selftest_lines()

    assert manifest_lines[0] == "mode: full"
    assert "title: Full Repository Export" in manifest_lines
    assert inventory_lines[0].startswith("README.md | group=files")
    assert readiness_lines[:4] == (
        "title=Full Repository Export",
        "valid=True",
        "contract_valid=True",
        "audit_valid=True",
    )
    assert audit_lines == (
        "valid=True",
        "summary_matches=True",
        "tree_matches=True",
        "inventory_matches=True",
        "round_trip_matches=True",
    )
    assert selftest_lines == (
        "valid=True",
        "contract_valid=True",
        "audit_valid=True",
        "readiness_valid=True",
        "round_trip_valid=True",
        "files=2",
        "omitted_files=1",
        "truncated_files=1",
        "warnings=2",
    )


def test_public_api_e2e_view_sections_and_inventory_are_consistent():
    export = api.make_export_model_selftest_export()

    view = api.repository_export_view(export)
    inventory = api.repository_export_file_inventory(export)

    assert view.export == export
    assert view.manifest.file_count == len(export.files)
    assert view.manifest.omitted_file_count == len(export.omitted_files)
    assert view.manifest.truncated_file_count == len(export.truncated_files)

    assert [entry.path for entry in inventory] == [
        "README.md",
        "assets/logo.png",
        "logs/large.log",
        "src/app.py",
    ]

    assert [
        entry.path
        for entry in api.repository_export_files_for_section(
            export,
            "source_export",
        )
    ] == [
        "README.md",
        "src/app.py",
    ]

    assert [
        entry.path
        for entry in api.repository_export_files_for_section(
            export,
            "omitted_files",
        )
    ] == [
        "assets/logo.png",
    ]

    assert [
        entry.path
        for entry in api.repository_export_files_for_section(
            export,
            "truncated_files",
        )
    ] == [
        "logs/large.log",
    ]
