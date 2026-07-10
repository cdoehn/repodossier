from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELETED_LINTER = REPO_ROOT / "scripts" / "dev" / "lint_patch_script.py"
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def test_obsolete_lint_wrapper_is_removed() -> None:
    assert not DELETED_LINTER.exists()


def test_c_runner_no_longer_references_deleted_lint_wrapper() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert "scripts/dev/lint_patch_script.py" not in text
    assert "preflight_linter=" not in text
    assert "run_patchharbor_cli lint-script" in text
    assert "Prüfe Patchscript mit patchharbor lint-script." in text


def test_c_runner_keeps_internal_metadata_validation() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert "PY_META_C_RUNNER_14B2" in text
    assert "Metadata invalid:" in text
    assert "display progress_context=false must not be combined with progress metadata records" in text
    assert "progress_context" in text


def test_lint_wrapper_cleanup_tests_do_not_store_private_local_values() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in [Path(__file__).resolve(), RUNNER])
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
