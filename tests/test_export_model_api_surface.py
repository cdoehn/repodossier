import inspect

import repodossier.export_model_api as api


def test_export_model_api_all_is_sorted_unique_and_resolvable():
    names = api.__all__

    assert isinstance(names, tuple)
    assert names == tuple(sorted(names))
    assert len(names) == len(set(names))

    unresolved = [name for name in names if not hasattr(api, name)]

    assert unresolved == []


def test_export_model_api_does_not_export_private_symbols():
    assert not any(name.startswith("_") for name in api.__all__)


def test_export_model_api_exports_core_model_types():
    required_types = {
        "RepositoryExport",
        "RepositoryMetadata",
        "ExportConfigurationSummary",
        "ExportSummary",
        "LanguageStatistics",
        "FileTreeEntry",
        "FileEntry",
        "ExportWarning",
        "DependencyReport",
        "DatabaseSchemaReport",
        "SecretDetectionSummary",
        "SymbolIndex",
        "ImportGraphReport",
        "CallGraphReport",
        "TestMapReport",
        "RecentCommitReport",
    }

    missing = sorted(required_types - set(api.__all__))

    assert missing == []
    for name in required_types:
        exported = getattr(api, name)
        assert inspect.isclass(exported)


def test_export_model_api_exports_acceptance_helpers():
    required_helpers = {
        "assert_export_model_contract",
        "assert_export_model_selftest",
        "assert_repository_export_audit",
        "assert_repository_export_ready",
        "assert_repository_export_round_trips",
        "audit_repository_export",
        "compare_repository_exports",
        "make_export_model_selftest_export",
        "repository_export_file_inventory",
        "repository_export_from_dict",
        "repository_export_from_json",
        "repository_export_manifest",
        "repository_export_readiness_status",
        "repository_export_round_trip_status",
        "repository_export_to_dict",
        "repository_export_to_json",
        "repository_export_view",
        "run_export_model_selftest",
    }

    missing = sorted(required_helpers - set(api.__all__))

    assert missing == []
    for name in required_helpers:
        exported = getattr(api, name)
        assert callable(exported)


def test_export_model_api_selftest_export_is_ready_via_public_surface():
    export = api.make_export_model_selftest_export()

    api.assert_export_model_contract(export)
    api.assert_repository_export_audit(export)
    api.assert_repository_export_ready(export)
    api.assert_repository_export_round_trips(export)

    assert api.run_export_model_selftest().valid
    assert api.repository_export_readiness_status(export).valid
    assert api.repository_export_round_trip_status(export).valid
