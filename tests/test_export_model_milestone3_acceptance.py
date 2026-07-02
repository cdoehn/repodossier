import repodossier.export_model_api as api


def test_milestone3_structured_export_model_acceptance_flow():
    export = api.make_export_model_selftest_export()

    api.assert_export_model_contract(export)
    api.assert_repository_export_audit(export)
    api.assert_repository_export_ready(export)
    api.assert_repository_export_round_trips(export)
    api.assert_export_model_selftest()

    readiness = api.repository_export_readiness_status(export)
    manifest = api.repository_export_manifest(export)
    inventory = api.repository_export_file_inventory(export)
    view = api.repository_export_view(export)
    roundtrip_status = api.repository_export_round_trip_status(export)
    selftest = api.run_export_model_selftest()

    assert readiness.valid
    assert manifest.root_name == "repo"
    assert manifest.mode == "full"
    assert manifest.file_count == 2
    assert manifest.omitted_file_count == 1
    assert manifest.truncated_file_count == 1
    assert manifest.warning_count == 2

    assert [entry.path for entry in inventory] == [
        "README.md",
        "assets/logo.png",
        "logs/large.log",
        "src/app.py",
    ]
    assert view.manifest == manifest
    assert "source_export" in view.sections
    assert "source_export" in view.populated_sections
    assert roundtrip_status.valid
    assert selftest.valid


def test_milestone3_public_api_can_json_roundtrip_and_compare_exports():
    export = api.make_export_model_selftest_export()
    json_text = api.repository_export_to_json(export)

    restored = api.repository_export_from_json(json_text)
    comparison = api.compare_repository_exports(export, restored)

    assert restored == export
    assert comparison.same
    assert comparison.same_fingerprint
    assert comparison.added_paths == ()
    assert comparison.removed_paths == ()
    assert comparison.changed_files == ()

    data_without_content = api.repository_export_to_dict(
        export,
        include_content=False,
    )
    restored_without_content = api.repository_export_from_dict(
        data_without_content,
    )

    assert restored_without_content.files[0].content is None
    assert restored_without_content.truncated_files[0].content is None


def test_milestone3_contract_requires_all_acceptance_api_symbols():
    required = {
        "RepositoryExport",
        "RepositoryMetadata",
        "FileEntry",
        "FileTreeEntry",
        "ExportSummary",
        "repository_export_to_dict",
        "repository_export_to_json",
        "repository_export_from_dict",
        "repository_export_from_json",
        "repository_export_manifest",
        "repository_export_file_inventory",
        "repository_export_view",
        "repository_export_readiness_status",
        "repository_export_round_trip_status",
        "audit_repository_export",
        "run_export_model_selftest",
        "make_export_model_selftest_export",
        "assert_export_model_selftest",
    }

    missing = sorted(symbol for symbol in required if symbol not in api.__all__)

    assert missing == []
    for symbol in required:
        assert hasattr(api, symbol)

    contract_status = api.export_model_contract_status(
        api.make_export_model_selftest_export()
    )

    assert contract_status.valid
    assert contract_status.issues == ()
    assert contract_status.missing_api_symbols == ()


def test_milestone3_lines_helpers_are_stable_and_human_readable():
    export = api.make_export_model_selftest_export()

    manifest_lines = api.repository_export_manifest_lines(export)
    inventory_lines = api.repository_export_file_inventory_lines(export)
    readiness_lines = api.repository_export_readiness_lines(export)
    selftest_lines = api.export_model_selftest_lines()

    assert manifest_lines[0] == "mode: full"
    assert "title: Full Repository Export" in manifest_lines
    assert "root_name: repo" in manifest_lines
    assert "root_path: /repo" in manifest_lines
    assert inventory_lines[0].startswith("README.md | group=files")
    assert inventory_lines[-1].startswith("src/app.py | group=files")
    assert readiness_lines[:4] == (
        "title=Full Repository Export",
        "valid=True",
        "contract_valid=True",
        "audit_valid=True",
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
