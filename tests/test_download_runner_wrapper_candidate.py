from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTIVE_RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"
CANDIDATE_RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch_patchharbor_candidate.sh"
WRAPPER = REPO_ROOT / "scripts" / "dev" / "run_patchharbor_patch.sh"


def test_obsolete_download_runner_candidate_is_removed() -> None:
    assert not CANDIDATE_RUNNER.exists()


def test_productive_c_runner_remains_present_after_candidate_cleanup() -> None:
    assert PRODUCTIVE_RUNNER.exists()
    assert PRODUCTIVE_RUNNER.stat().st_size > 1000
    text = PRODUCTIVE_RUNNER.read_text(encoding="utf-8")
    assert "RepoDossier Download Patch Runner" in text
    assert "run_patchharbor_cli lint-script" in text
    assert "PY_META_C_RUNNER_14B2" in text


def test_patchharbor_source_wrapper_remains_present_after_candidate_cleanup() -> None:
    assert WRAPPER.exists()
    text = WRAPPER.read_text(encoding="utf-8")
    assert "patchharbor" in text.lower()


def test_candidate_cleanup_test_does_not_store_private_local_values() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [Path(__file__).resolve(), PRODUCTIVE_RUNNER, WRAPPER]
    )
    forbidden = [
        "/home/" + "exampleuser",
        "user" + "@",
        "example.user" + "@" + "example.invalid",
        "Example" + "Laptop",
        "Example" + "Machine",
        "~/" + "Projects",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text
