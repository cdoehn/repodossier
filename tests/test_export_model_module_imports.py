import importlib


EXPORT_MODEL_MODULES = (
    "repodossier.export_model",
    "repodossier.export_model_adapters",
    "repodossier.export_model_api",
    "repodossier.export_model_audit",
    "repodossier.export_model_builder",
    "repodossier.export_model_collector",
    "repodossier.export_model_compare",
    "repodossier.export_model_configuration",
    "repodossier.export_model_content",
    "repodossier.export_model_contract",
    "repodossier.export_model_deserialization",
    "repodossier.export_model_factory",
    "repodossier.export_model_finalize",
    "repodossier.export_model_index",
    "repodossier.export_model_inventory",
    "repodossier.export_model_manifest",
    "repodossier.export_model_modes",
    "repodossier.export_model_paths",
    "repodossier.export_model_readiness",
    "repodossier.export_model_reports",
    "repodossier.export_model_repository",
    "repodossier.export_model_roundtrip",
    "repodossier.export_model_sections",
    "repodossier.export_model_selftest",
    "repodossier.export_model_serialization",
    "repodossier.export_model_snapshot",
    "repodossier.export_model_summary",
    "repodossier.export_model_tree",
    "repodossier.export_model_view",
    "repodossier.export_model_warnings",
)


def test_all_export_model_modules_import_cleanly():
    imported = []

    for module_name in EXPORT_MODEL_MODULES:
        module = importlib.import_module(module_name)
        imported.append(module.__name__)

    assert tuple(imported) == EXPORT_MODEL_MODULES


def test_export_model_api_import_after_all_helper_modules_is_stable():
    for module_name in EXPORT_MODEL_MODULES:
        importlib.import_module(module_name)

    api = importlib.import_module("repodossier.export_model_api")

    assert api.run_export_model_selftest().valid
    assert api.repository_export_readiness_status(
        api.make_export_model_selftest_export()
    ).valid


def test_export_model_contract_import_after_public_api_is_stable():
    api = importlib.import_module("repodossier.export_model_api")
    contract = importlib.import_module("repodossier.export_model_contract")

    status = contract.export_model_contract_status(
        api.make_export_model_selftest_export()
    )

    assert status.valid
    assert status.issues == ()
    assert status.missing_api_symbols == ()
