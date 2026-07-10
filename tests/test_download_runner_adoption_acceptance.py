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


def test_download_runner_adoption_acceptance_document_exists_and_is_historical() -> None:
    text = _read(ACCEPTANCE)
    assert "PATCHHARBOR.10d4" in text
    assert "Download Runner Adoption Acceptance Documentation" in text
    assert "PATCHHARBOR.14b3 applied" in text
    assert "historical candidate artifact" in text


def test_acceptance_tracks_productive_runner_and_removed_candidate() -> None:
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
    assert not CANDIDATE_RUNNER.exists()
    assert WRAPPER_DRAFT.exists()
    assert HARNESS_TESTS.exists()
    assert CANDIDATE_TESTS.exists()


def test_acceptance_records_that_c_is_not_switched_or_removed_here() -> None:
    text = _read(ACCEPTANCE)
    required = [
        "the old productive source runner remains present",
        "the user-facing `c` workflow is not switched by this patch",
        "source-only patches must leave the target repository unchanged",
        "the historical candidate runner was removed by PATCHHARBOR.14b3",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_acceptance_non_goals_keep_runner_contract_stable_after_cleanup() -> None:
    text = _read(ACCEPTANCE)
    non_goals = [
        "switch `c`",
        "replace `scripts/dev/run_latest_download_patch.sh`",
        "edit alias installers",
        "edit export scripts",
        "remove the old runner",
        "change PatchHarbor target code",
        "change runner output contracts",
    ]
    missing = [marker for marker in non_goals if marker not in text]
    assert not missing, missing


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
        assert value not in text
