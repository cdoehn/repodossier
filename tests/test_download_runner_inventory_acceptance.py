from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "planning/patchharbor/download-runner-inventory-acceptance.md"
INVENTORY = ROOT / "planning/patchharbor/download-runner-file-inventory.md"
LIFECYCLE = ROOT / "planning/patchharbor/download-runner-lifecycle-flow.md"
OUTPUT = ROOT / "planning/patchharbor/download-runner-output-contract.md"
INVENTORY_TESTS = ROOT / "tests/test_download_runner_inventory_docs.py"
RUNNER = ROOT / "scripts/dev/run_latest_download_patch.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_download_runner_inventory_acceptance_document_exists() -> None:
    assert ACCEPTANCE.exists()
    text = _read(ACCEPTANCE)
    assert "PATCHHARBOR.10a5" in text
    assert "Download Runner Inventory Acceptance" in text
    assert "This document accepts the Download Runner Inventory phase." in text


def test_acceptance_references_all_10a_artifacts() -> None:
    text = _read(ACCEPTANCE)
    required_paths = [
        "planning/patchharbor/download-runner-file-inventory.md",
        "planning/patchharbor/download-runner-lifecycle-flow.md",
        "planning/patchharbor/download-runner-output-contract.md",
        "tests/test_download_runner_inventory_docs.py",
        "scripts/dev/run_latest_download_patch.sh",
    ]
    for path in required_paths:
        assert path in text, path
        assert (ROOT / path).exists(), path


def test_acceptance_documents_current_behavior_coverage() -> None:
    text = _read(ACCEPTANCE)
    required = [
        "direct `.sh` patch scripts",
        "`.zip` archives containing one patch script",
        "metadata validation",
        "repeat detection",
        "freshness checks",
        "Bash syntax checks",
        "patch preflight linting",
        "dry-run behavior",
        "progress context suppression through patch metadata",
        "done and failed lifecycle moves",
        "applied ledger behavior",
        "terminal output contract",
        "success and failure completion semantics",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_acceptance_records_non_goals_before_parity_phase() -> None:
    text = _read(ACCEPTANCE)
    non_goals = [
        "PatchHarbor download runner API changes",
        "source runner replacement",
        "`c` alias migration",
        "alias installation",
        "export runner migration",
        "deletion of old source scripts",
        "changes to done or failed lifecycle behavior",
        "changes to terminal output behavior",
    ]
    for phrase in non_goals:
        assert phrase in text, phrase


def test_acceptance_defines_next_10b_parity_areas() -> None:
    text = _read(ACCEPTANCE)
    required = [
        "metadata validation",
        "freshness rejection",
        "repeat rejection",
        "syntax failure",
        "success lifecycle",
        "failure lifecycle",
        "footer and output semantics",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_acceptance_is_consistent_with_inventory_documents() -> None:
    combined_inventory = "\n".join(_read(path) for path in (INVENTORY, LIFECYCLE, OUTPUT))
    acceptance = _read(ACCEPTANCE)
    shared_terms = [
        "metadata",
        "repeat",
        "freshness",
        "syntax",
        ".zip",
        "done",
        "failed",
        "progress context",
    ]
    for term in shared_terms:
        assert term in combined_inventory, term
        assert term in acceptance, term


def test_acceptance_is_backed_by_inventory_tests() -> None:
    test_text = _read(INVENTORY_TESTS)
    required_tests = [
        "test_download_runner_inventory_documents_exist",
        "test_file_inventory_covers_runner_inputs_outputs_and_non_goals",
        "test_lifecycle_flow_documents_phase_order_and_zip_semantics",
        "test_output_contract_documents_visible_terminal_contract",
        "test_inventory_documents_match_existing_runner_capabilities",
    ]
    for test_name in required_tests:
        assert test_name in test_text, test_name


def test_acceptance_does_not_change_runner_or_lifecycle_scripts() -> None:
    runner_text = _read(RUNNER)
    assert "--no-progress-context" in runner_text
    assert "--no-context" in runner_text
    assert "C_RUNNER_PROGRESS_CONTEXT" in runner_text
    assert ".zip" in runner_text
    assert ".applied_patch_hashes.tsv" in runner_text


def test_download_runner_inventory_acceptance_files_do_not_store_private_local_values() -> None:
    checked = [
        ACCEPTANCE,
        ROOT / "tests/test_download_runner_inventory_acceptance.py",
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
