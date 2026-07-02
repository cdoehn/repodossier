import importlib
from pathlib import Path

import repodossier


def _package_root() -> Path:
    package_file = Path(repodossier.__file__).resolve()
    return package_file.parent


def _export_model_module_names() -> tuple[str, ...]:
    package_root = _package_root()

    return tuple(
        sorted(
            f"repodossier.{path.stem}"
            for path in package_root.glob("export_model*.py")
            if path.name != "__init__.py"
        )
    )


def test_all_export_model_python_files_are_importable_modules():
    module_names = _export_model_module_names()

    assert "repodossier.export_model" in module_names
    assert "repodossier.export_model_api" in module_names
    assert "repodossier.export_model_selftest" in module_names
    assert "repodossier.export_model_readiness" in module_names

    failed = []

    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failed.append(f"{module_name}: {exc}")

    assert failed == []


def test_export_model_module_discovery_covers_static_smoke_test_list():
    discovered = set(_export_model_module_names())

    static_smoke_modules = {
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
    }

    missing = sorted(static_smoke_modules - discovered)

    assert missing == []


def test_export_model_public_api_remains_valid_after_dynamic_module_imports():
    for module_name in _export_model_module_names():
        importlib.import_module(module_name)

    api = importlib.import_module("repodossier.export_model_api")

    export = api.make_export_model_selftest_export()

    assert api.export_model_contract_status(export).valid
    assert api.audit_repository_export(export).valid
    assert api.repository_export_readiness_status(export).valid
    assert api.repository_export_round_trip_status(export).valid
    assert api.run_export_model_selftest().valid
