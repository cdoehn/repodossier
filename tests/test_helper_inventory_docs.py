from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_INVENTORY = ROOT / "planning" / "patchharbor" / "helper-file-inventory.md"
HELPER_CLASSIFICATION = ROOT / "planning" / "patchharbor" / "helper-classification.md"
MILESTONES = ROOT / "planning" / "milestones_migration.md"

CURRENT_HELPERS = [
    "scripts/dev/audit_public_repo.py",
    "scripts/dev/check_dev_environment.py",
    "scripts/dev/install_aliases.sh",
    "scripts/dev/patch-rules.md",
    "scripts/dev/patch-workflow-rules.json",
    "scripts/dev/patch-workflow-rules.schema.json",
    "scripts/dev/r.sh",
    "scripts/dev/repo_patch_helper.py",
    "scripts/dev/run_latest_download_patch.sh",
    "scripts/dev/run_patchharbor_patch.sh",
    "scripts/dev/run_repodossier_exports.sh",
    "scripts/dev/show_progress_context.py",
    "scripts/dev/validate_patch_workflow_rules.py",
]
OPTIONAL_HELPERS = [
]
REMOVED_HELPERS = [
    "scripts/dev/validate_patch_metadata.py",
    "scripts/dev/lint_patch_script.py",
    "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh",
]

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_helper_inventory_and_classification_documents_exist() -> None:
    for path in (HELPER_INVENTORY, HELPER_CLASSIFICATION):
        assert path.exists(), str(path)
        assert path.stat().st_size > 1000, str(path)


def test_helper_inventory_lists_current_helper_files_and_optional_candidate() -> None:
    text = _read(HELPER_INVENTORY)
    missing = [helper for helper in CURRENT_HELPERS + OPTIONAL_HELPERS if helper not in text]
    assert not missing, missing

    missing_on_disk = [helper for helper in CURRENT_HELPERS if not (ROOT / helper).exists()]
    assert not missing_on_disk, missing_on_disk

    optional_present = [helper for helper in OPTIONAL_HELPERS if (ROOT / helper).exists()]
    optional_missing_from_inventory = [helper for helper in optional_present if helper not in text]
    assert not optional_missing_from_inventory, optional_missing_from_inventory


def test_helper_classification_covers_every_inventory_helper() -> None:
    classification = _read(HELPER_CLASSIFICATION)
    missing = [helper for helper in CURRENT_HELPERS + OPTIONAL_HELPERS + REMOVED_HELPERS if helper not in classification]
    assert not missing, missing


def test_helper_inventory_records_source_specific_constraints_and_non_goals() -> None:
    text = _read(HELPER_INVENTORY)
    required = [
        "RepoDossier package names or CLI defaults",
        "source repository wrapper names",
        "`r` and `c` alias behavior",
        "generated export artifact names",
        "German source-side terminal output markers",
        "migration planning file paths",
        "local machine paths or private identity values",
        "Non-goals for PATCHHARBOR.12a1",
        "This patch does not:",
        "classify helpers",
        "move helpers to PatchHarbor",
        "modify helper behavior",
        "change aliases",
        "change `c`",
        "change `r`",
        "change download runner behavior",
        "change export runner behavior",
        "add target-side helper APIs",
        "delete source-side helpers",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_helper_classification_groups_match_operational_plan() -> None:
    text = _read(HELPER_CLASSIFICATION)
    groups = [
        "public audit helpers",
        "development environment helpers",
        "patch script lint helpers",
        "patch workflow rule helpers",
        "patch metadata helpers",
        "source alias and wrapper helpers",
        "source export helpers",
        "source download helpers",
        "repository patch helper",
        "documentation and policy data",
    ]
    missing = [group for group in groups if group not in text]
    assert not missing, missing

    immediate_steps = [
        "PATCHHARBOR.12a3 – Helper Inventory Tests",
        "PATCHHARBOR.12b1 – Public Audit Model",
        "PATCHHARBOR.12b2 – Public Audit Checks",
        "PATCHHARBOR.12b3 – Public Audit CLI",
        "PATCHHARBOR.12b4 – Source Public Audit Wrapper",
        "PATCHHARBOR.12c1 – Environment Check Model",
        "PATCHHARBOR.12c2 – Environment Check CLI",
        "PATCHHARBOR.12c3 – Source Environment Wrapper",
    ]
    missing_steps = [step for step in immediate_steps if step not in text]
    assert not missing_steps, missing_steps


def test_helper_classification_separates_immediate_generic_candidates_from_source_wrappers() -> None:
    text = _read(HELPER_CLASSIFICATION)
    required = [
        "scripts/dev/audit_public_repo.py",
        "generic-candidate",
        "planned area: PATCHHARBOR.12b",
        "scripts/dev/check_dev_environment.py",
        "planned area: PATCHHARBOR.12c",
        "scripts/dev/install_aliases.sh",
        "source-only integration helpers",
        "scripts/dev/run_patchharbor_patch.sh",
        "scripts/dev/r.sh",
        "PATCHHARBOR.11 already introduced generic export model/planning/display helpers",
        "scripts/dev/run_latest_download_patch.sh",
        "PATCHHARBOR.10 already covered download runner parity/API/adoption",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_helper_classification_keeps_metadata_and_workflow_rules_compatibility_sensitive() -> None:
    text = _read(HELPER_CLASSIFICATION)
    required = [
            "scripts/dev/show_progress_context.py",
        "compatibility-sensitive",
        "Do not weaken metadata validation.",
        "Context display suppression through `progress_context=false` must remain compatible.",
        "scripts/dev/patch-workflow-rules.json",
        "scripts/dev/patch-workflow-rules.schema.json",
        "scripts/dev/validate_patch_workflow_rules.py",
        "The schema and rule identifiers are contracts.",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_helper_classification_does_not_reintroduce_finished_download_or_export_migrations() -> None:
    text = _read(HELPER_CLASSIFICATION)
    required = [
        "Do not reclassify these as PATCHHARBOR.12 targets.",
        "Do not restart download runner migration under PATCHHARBOR.12.",
        "already migrated download/export helpers are not reintroduced as new PATCHHARBOR.12 migrations",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_helper_inventory_sequence_matches_milestones_operational_plan() -> None:
    classification = _read(HELPER_CLASSIFICATION)
    milestones = _read(MILESTONES)
    required_steps = [
        "PATCHHARBOR.12a3 – Helper Inventory Tests",
        "PATCHHARBOR.12b1 – Public Audit Model",
        "PATCHHARBOR.12b2 – Public Audit Checks",
        "PATCHHARBOR.12b3 – Public Audit CLI",
        "PATCHHARBOR.12b4 – Source Public Audit Wrapper",
        "PATCHHARBOR.12c1 – Environment Check Model",
        "PATCHHARBOR.12c2 – Environment Check CLI",
        "PATCHHARBOR.12c3 – Source Environment Wrapper",
    ]
    missing = []
    for step in required_steps:
        if step not in classification:
            missing.append(f"classification: {step}")
        if step not in milestones:
            missing.append(f"milestones: {step}")
    assert not missing, missing


def test_helper_inventory_docs_do_not_store_private_local_values() -> None:
    checked = [
        HELPER_INVENTORY,
        HELPER_CLASSIFICATION,
        ROOT / "tests/test_helper_inventory_docs.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
    forbidden = [
        "/home/" + "exampleuser",
        "user" + "@",
        "example.user" + "@" + "example.invalid",
        "Example" + "Laptop",
        "~/" + "Projects",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text, value
