from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def test_c_runner_has_single_self_copy_bootstrap_after_14b4() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert text.count('original_runner="${BASH_SOURCE[0]}"') == 1
    assert text.count('C_RUNNER_SELF_COPY=1 C_RUNNER_ORIGINAL=') == 1
    assert 'self_copy="$(mktemp' not in text
    assert "C_RUNNER_ORIGINAL" in text
    assert "cleanup_c_runner" in text


def test_c_runner_keeps_download_and_lifecycle_contract_after_self_copy_cleanup() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    required = [
        "RepoDossier Download Patch Runner",
        "download_dir=",
        "done_dir=",
        "failed_dir=",
        "applied_ledger=",
        "zip_extract_dir",
        "record_successful_application",
        "move_script_to",
        "run_patchharbor_cli lint-script",
        "PY_META_C_RUNNER_14B2",
        "DRY-RUN OK",
        "Patch erfolgreich.",
        "Patch fehlgeschlagen.",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_c_runner_self_copy_cleanup_does_not_store_private_local_values() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [Path(__file__).resolve(), RUNNER]
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
