from __future__ import annotations

import os
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/dev/run_latest_download_patch.sh"


def patch_text(*, patch_id: str, body: str = "true") -> str:
    meta = "# " + "repodossier-" + "meta: "
    lines = [
        "#!/usr/bin/env bash",
        f'{meta}{{"type":"patch","id":"{patch_id}","title":"Zip smoke","commit":"Zip smoke"}}',
        f'{meta}{{"type":"progress","panel":"roadmap","status":"active","file":"planning/roadmap_migration.md","start":1,"end":20,"label":"Zip smoke roadmap"}}',
        f'{meta}{{"type":"progress","panel":"milestone","status":"active","file":"planning/milestones_migration.md","start":1,"end":20,"label":"Zip smoke milestone"}}',
        f'{meta}{{"type":"display","context":1,"layout":"side-by-side","frame":false}}',
        "set -euo pipefail",
        "",
        "print_footer() {",
        "  true",
        "}",
        "trap print_footer EXIT",
        "",
        'bash -n "$0"',
        "python3 - <<'PYSMOKE'",
        'print("zip smoke checks ok")',
        "PYSMOKE",
        "",
        body,
        "",
    ]
    return "\n".join(lines)


def write_zip(path: Path, script_name: str, script_content: str) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(script_name, script_content)


def run_c(downloads: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(downloads)
    env["C_RUNNER_MAX_AGE_SECONDS"] = "999999"
    env["NO_COLOR"] = "1"
    return subprocess.run(
        [str(RUNNER), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=False,
    )


def test_c_runner_dry_run_accepts_zip_with_single_patch_script(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    patch_zip = downloads / "patch.zip"
    write_zip(patch_zip, "patch.sh", patch_text(patch_id="PATCHHARBOR.CRUNNER.ZIP.DRY"))

    result = run_c(downloads, "--dry-run", str(patch_zip))

    assert result.returncode == 0, result.stdout
    assert "Patcharchive:" in result.stdout
    assert "Patchscript:" in result.stdout
    assert "Dry-run erfolgreich" in result.stdout
    assert patch_zip.exists()


def test_c_runner_failure_prints_progress_above_failure_band_for_zip(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    patch_zip = downloads / "failing_patch.zip"
    write_zip(
        patch_zip,
        "failing_patch.sh",
        patch_text(patch_id="PATCHHARBOR.CRUNNER.ZIP.FAIL", body="exit 7"),
    )

    result = run_c(downloads, str(patch_zip))

    assert result.returncode == 7, result.stdout
    assert "Patch fehlgeschlagen." in result.stdout
    assert "Roadmap / Milestone" in result.stdout
    assert "FEHLSCHLAG" in result.stdout
    assert result.stdout.rfind("Roadmap / Milestone") < result.stdout.rfind("FEHLSCHLAG")
    assert not patch_zip.exists()
    assert (downloads / "failed" / "failing_patch.zip").exists()


def test_c_runner_selects_latest_zip_when_no_path_is_given(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    patch_zip = downloads / "latest_patch.zip"
    write_zip(patch_zip, "latest_patch.sh", patch_text(patch_id="PATCHHARBOR.CRUNNER.ZIP.LATEST"))

    result = run_c(downloads, "--dry-run")

    assert result.returncode == 0, result.stdout
    assert "latest_patch.zip" in result.stdout
    assert "Dry-run erfolgreich" in result.stdout


def test_c_runner_zip_support_and_status_test_has_no_private_values() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
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
