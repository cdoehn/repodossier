from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "planning/patchharbor/download-runner-file-inventory.md"
LIFECYCLE = ROOT / "planning/patchharbor/download-runner-lifecycle-flow.md"
OUTPUT = ROOT / "planning/patchharbor/download-runner-output-contract.md"
RUNNER = ROOT / "scripts/dev/run_latest_download_patch.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_download_runner_inventory_documents_exist() -> None:
    for path in (INVENTORY, LIFECYCLE, OUTPUT):
        assert path.exists(), str(path)
        assert path.stat().st_size > 1000, str(path)


def test_file_inventory_covers_runner_inputs_outputs_and_non_goals() -> None:
    text = _read(INVENTORY)
    required = [
        "PATCHHARBOR.10a1",
        "direct `.sh` patch script",
        "`.zip` archive containing exactly one `.sh` patch script",
        "download directory",
        "done directory",
        "failed directory",
        "run log",
        "applied ledger",
        "metadata",
        "repeat detection",
        "freshness checks",
        "Bash syntax checks",
        "patch preflight linting",
        "move successful inputs",
        "move failed inputs",
        "change `c`",
        "switch `c` to PatchHarbor",
        "remove the old runner",
        "migrate export behavior",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_lifecycle_flow_documents_phase_order_and_zip_semantics() -> None:
    text = _read(LIFECYCLE)
    required = [
        "PATCHHARBOR.10a2",
        "Resolve download, done, and failed workflow locations.",
        "Select the input patch",
        "safely extract exactly one `.sh` script",
        "Validate metadata.",
        "Apply display metadata such as `progress_context=false`.",
        "Check whether the input was already applied.",
        "Check freshness.",
        "Run Bash syntax validation.",
        "Run patch preflight linting.",
        "Execute the patch",
        "Move the original input artifact to done or failed.",
        "Record successful application",
        "For `.zip` input, syntax validation runs against the extracted `.sh` script.",
        "use the original `.zip` archive as the lifecycle input artifact",
        "temporary extraction directory is cleaned up",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_output_contract_documents_visible_terminal_contract() -> None:
    text = _read(OUTPUT)
    required = [
        "PATCHHARBOR.10a3",
        "start banner",
        "input artifact summary",
        "metadata check output",
        "repeat check output",
        "freshness check output",
        "syntax check output",
        "execution output",
        "progress context display",
        "done and failed move output",
        "final success or failure band",
        "exit-code meaning",
        "The exact colors are not part of the contract.",
        "Progress context can be shown or hidden.",
        "The runner exits with code `0` only",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_inventory_documents_match_existing_runner_capabilities() -> None:
    inventory = _read(INVENTORY)
    lifecycle = _read(LIFECYCLE)
    output = _read(OUTPUT)
    runner = _read(RUNNER)

    runner_flags = [
        "--dry-run",
        "--wait",
        "--no-progress-context",
        "--no-context",
        "C_RUNNER_PROGRESS_CONTEXT",
        ".zip",
        ".applied_patch_hashes.tsv",
        "done",
        "failed",
    ]
    for phrase in runner_flags:
        assert phrase in runner, phrase

    inventory_semantics = [
        "dry-run mode",
        "download directory",
        "done directory",
        "failed directory",
        "applied ledger",
        ".zip",
        "freshness checks",
        "repeat detection",
    ]
    for phrase in inventory_semantics:
        assert phrase in inventory, phrase

    lifecycle_semantics = [
        "dry-run",
        "--no-progress-context",
        "--no-context",
        "C_RUNNER_PROGRESS_CONTEXT",
        ".zip",
        "done",
        "failed",
        "applied ledger",
    ]
    for phrase in lifecycle_semantics:
        assert phrase in lifecycle, phrase

    output_semantics = [
        "--no-progress-context",
        "--no-context",
        "C_RUNNER_PROGRESS_CONTEXT",
        ".zip",
        "done",
        "failed",
        "progress_context=false",
    ]
    for phrase in output_semantics:
        assert phrase in output, phrase


def test_lifecycle_document_keeps_current_runner_scope_narrow() -> None:
    text = _read(LIFECYCLE)
    non_goals = [
        "switch `c` to PatchHarbor",
        "replace the download runner",
        "change alias behavior",
        "migrate export behavior",
    ]
    for phrase in non_goals:
        assert phrase in text, phrase


def test_output_contract_contains_failure_and_success_completion_semantics() -> None:
    text = _read(OUTPUT)
    required = [
        "A successful run ends with a prominent success band.",
        "A failed run ends with a prominent failure band.",
        "metadata validation fails",
        "repeat check rejects the input",
        "freshness check fails",
        "Bash syntax validation fails",
        "the patch was not executed",
        "log remains available",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_download_runner_inventory_files_do_not_store_private_local_values() -> None:
    checked = [
        INVENTORY,
        LIFECYCLE,
        OUTPUT,
        ROOT / "tests/test_download_runner_inventory_docs.py",
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


def test_download_runner_inventory_uses_patchharbor_10a_sequence() -> None:
    joined = "\n".join(_read(path) for path in (INVENTORY, LIFECYCLE, OUTPUT))
    headings = re.findall(r"PATCHHARBOR\.10a[123]", joined)
    assert headings.count("PATCHHARBOR.10a1") >= 1
    assert headings.count("PATCHHARBOR.10a2") >= 1
    assert headings.count("PATCHHARBOR.10a3") >= 1
