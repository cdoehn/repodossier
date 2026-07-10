from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "planning" / "patchharbor" / "download-runner-adoption-acceptance.md"
PRODUCTIVE_RUNNER = ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"
CANDIDATE_RUNNER = ROOT / "scripts" / "dev" / "run_latest_download_patch_patchharbor_candidate.sh"
WRAPPER_DRAFT = ROOT / "planning" / "patchharbor" / "source-download-runner-wrapper-draft.md"
HARNESS_TESTS = ROOT / "tests" / "test_download_runner_wrapper_harness.py"
CANDIDATE_TESTS = ROOT / "tests" / "test_download_runner_wrapper_candidate.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_download_runner_adoption_acceptance_document_exists() -> None:
    text = _read(ACCEPTANCE)
    assert "PATCHHARBOR.10d4" in text
    assert "Download Runner Adoption Acceptance Documentation" in text
    assert "The accepted state is deliberately conservative" in text


def test_acceptance_references_productive_candidate_and_test_artifacts() -> None:
    text = _read(ACCEPTANCE)
    required_paths = [
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh",
        "planning/patchharbor/source-download-runner-wrapper-draft.md",
        "tests/test_download_runner_wrapper_harness.py",
        "tests/test_download_runner_wrapper_candidate.py",
    ]
    missing = [path for path in required_paths if path not in text]
    assert not missing, missing

    assert PRODUCTIVE_RUNNER.exists()
    assert CANDIDATE_RUNNER.exists()
    assert WRAPPER_DRAFT.exists()
    assert HARNESS_TESTS.exists()
    assert CANDIDATE_TESTS.exists()


def test_acceptance_records_that_c_is_not_switched_here() -> None:
    text = _read(ACCEPTANCE)
    required = [
        "the old productive source runner remains present",
        "the candidate runner remains additive",
        "the user-facing `c` workflow is not switched by this patch",
        "source-only patches must leave the target repository unchanged",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_acceptance_records_rollback_instructions() -> None:
    text = _read(ACCEPTANCE)
    required = [
        "Rollback",
        "Revert the commit that added the candidate runner if the candidate itself is wrong.",
        "Revert this acceptance documentation if the documented state is wrong.",
        "Do not touch the productive old runner unless a later explicit replacement commit changed it.",
        "Keep PATCHHARBOR.10b parity tests before any future replacement attempt.",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_acceptance_non_goals_keep_runner_contract_stable() -> None:
    text = _read(ACCEPTANCE)
    non_goals = [
        "switch `c`",
        "replace `scripts/dev/run_latest_download_patch.sh`",
        "edit alias installers",
        "edit export scripts",
        "remove the old runner",
        "delete the candidate runner",
        "change PatchHarbor target code",
        "change runner output contracts",
    ]
    missing = [marker for marker in non_goals if marker not in text]
    assert not missing, missing


def test_candidate_and_harness_files_express_additive_candidate_contract() -> None:
    harness_text = _read(HARNESS_TESTS)
    candidate_text = _read(CANDIDATE_TESTS)
    candidate_runner_text = _read(CANDIDATE_RUNNER)

    assert "test_harness_can_compare_two_candidate_commands_without_switching_runner" in harness_text
    assert "test_wrapper_harness_file_does_not_modify_productive_runner" in harness_text
    assert "run_latest_" + "download_patch.sh" in harness_text
    assert "patchharbor" in candidate_runner_text
    assert "run-script" in candidate_runner_text
    assert "run_latest_download_patch_patchharbor_candidate.sh" in candidate_text


def test_productive_runner_is_not_replaced_by_candidate() -> None:
    productive_text = _read(PRODUCTIVE_RUNNER)
    candidate_text = _read(CANDIDATE_RUNNER)

    future_wrapper = "exec " + "patchharbor " + "run-script"
    assert future_wrapper not in productive_text
    assert "patchharbor" in candidate_text
    assert "run-script" in candidate_text


def test_adoption_acceptance_files_do_not_store_private_local_values() -> None:
    checked = [
        ACCEPTANCE,
        ROOT / "tests/test_download_runner_adoption_acceptance.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
    forbidden = [
        "/home/" + "christian",
        "christian" + "@",
        "christian.doehn" + "@" + "gmail.com",
        "Think" + "Pad",
        "~/" + "Projekte",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text, value
