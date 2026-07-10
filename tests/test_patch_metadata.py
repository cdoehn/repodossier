from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELETED_HELPER = REPO_ROOT / "scripts" / "dev" / "validate_patch_metadata.py"
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"
LINTER = REPO_ROOT / "scripts" / "dev" / "lint_patch_script.py"


def test_obsolete_metadata_helper_wrapper_is_removed() -> None:
    assert not DELETED_HELPER.exists()


def test_c_runner_no_longer_executes_deleted_metadata_helper() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert "validate_patch_metadata.py" not in text
    assert "--metadata-only" in text
    assert "Validiere repodossier-meta JSON-Kommentarzeilen." in text


def test_lint_wrapper_no_longer_imports_deleted_metadata_helper() -> None:
    text = LINTER.read_text(encoding="utf-8")

    assert "from validate_patch_metadata" not in text
    assert "validate_patch_metadata.py" not in text
    assert "ALLOWED_LAYOUTS" in text
    assert "--metadata-only" in text
    assert "parse_metadata_lines" in text
    assert "validate_records" in text


def test_c_runner_still_rejects_invalid_metadata_in_dry_run(tmp_path: Path) -> None:
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    patch = downloads / "bad_metadata.sh"
    patch.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.BAD","title":"Bad"}',
                '# repodossier-meta: {"type":"display","progress_context":false}',
                "echo should-not-run",
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


def test_lint_wrapper_metadata_only_still_rejects_missing_metadata(tmp_path: Path) -> None:
    patch = tmp_path / "missing_metadata_only.sh"
    patch.write_text("#!/usr/bin/env bash\nprint_footer() { echo footer; }\n", encoding="utf-8")
    patch.chmod(0o755)

    result = subprocess.run(
        [sys.executable, str(LINTER), "--metadata-only", "--script", str(patch), "--repo", str(REPO_ROOT)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 10
    assert "missing required repodossier-meta block" in result.stdout


def test_lint_wrapper_normal_mode_still_uses_lint_exit_code_for_metadata_findings(tmp_path: Path) -> None:
    patch = tmp_path / "missing_metadata.sh"
    patch.write_text("#!/usr/bin/env bash\nprint_footer() { echo footer; }\n", encoding="utf-8")
    patch.chmod(0o755)

    result = subprocess.run(
        [sys.executable, str(LINTER), "--script", str(patch), "--repo", str(REPO_ROOT)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 20
    assert "missing required repodossier-meta block" in result.stdout


def test_metadata_cleanup_tests_do_not_store_private_local_values() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [Path(__file__).resolve(), RUNNER, LINTER]
    )
    forbidden = [
        "/home/" + "christian",
        "christian" + "@",
        "christian.doehn" + "@" + "gmail.com",
        "Think" + "Pad",
        "Blade-" + "15",
        "~/" + "Projekte",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text
