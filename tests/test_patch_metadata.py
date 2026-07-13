from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELETED_METADATA_HELPER = REPO_ROOT / "scripts" / "dev" / "validate_patch_metadata.py"
DELETED_LINTER = REPO_ROOT / "scripts" / "dev" / "lint_patch_script.py"
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def test_obsolete_metadata_and_lint_helpers_are_removed() -> None:
    assert not DELETED_METADATA_HELPER.exists()
    assert not DELETED_LINTER.exists()


def test_c_runner_has_internal_metadata_validation_not_deleted_helpers() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert "validate_patch_metadata.py" not in text
    assert "scripts/dev/lint_patch_script.py" not in text
    assert "--metadata-only" not in text
    assert "PY_META_C_RUNNER_14B2" in text
    assert "Metadata invalid:" in text
    assert "progress_context" in text


def test_c_runner_still_rejects_invalid_metadata_in_dry_run(tmp_path: Path) -> None:
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    patch = downloads / "bad_metadata.sh"
    patch.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"REPODOSSIER.BAD","title":"Bad"}',
                '# repodossier-meta: {"type":"display","progress_context":false}',
                "print_footer() { echo footer; }",
                "trap print_footer EXIT",
                "bash -n scripts/dev/run_latest_download_patch.sh",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    patch.chmod(0o755)

    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(downloads)
    result = subprocess.run(
        [str(RUNNER), "--dry-run", str(patch)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 10
    assert "Metadata invalid:" in result.stdout
    assert "commit" in result.stdout


def test_metadata_cleanup_tests_do_not_store_private_local_values() -> None:
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
