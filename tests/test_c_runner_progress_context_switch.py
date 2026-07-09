from __future__ import annotations

import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/dev/run_latest_download_patch.sh"


def patch_text(*, patch_id: str) -> str:
    meta = "# " + "repodossier-" + "meta: "
    lines = [
        "#!/usr/bin/env bash",
        f'{meta}{{"type":"patch","id":"{patch_id}","title":"Context switch smoke","commit":"Context switch smoke"}}',
        f'{meta}{{"type":"progress","panel":"roadmap","status":"active","file":"planning/roadmap_migration.md","start":285,"end":290,"label":"Context switch roadmap"}}',
        f'{meta}{{"type":"progress","panel":"milestone","status":"active","file":"planning/milestones_migration.md","start":1,"end":8,"label":"Context switch milestone"}}',
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
        'print("context switch smoke checks ok")',
        "PYSMOKE",
        "",
        "true",
        "",
    ]
    return "\n".join(lines)


def run_c(downloads: Path, *args: str, progress_context: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(downloads)
    env["C_RUNNER_MAX_AGE_SECONDS"] = "999999"
    env["NO_COLOR"] = "1"
    if progress_context is not None:
        env["C_RUNNER_PROGRESS_CONTEXT"] = progress_context
    return subprocess.run(
        [str(RUNNER), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=False,
    )


def write_patch(downloads: Path, name: str, patch_id: str) -> Path:
    path = downloads / name
    path.write_text(patch_text(patch_id=patch_id), encoding="utf-8")
    path.chmod(0o755)
    return path


def test_no_progress_context_flag_hides_context_but_keeps_success_band(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    patch = write_patch(downloads, "patch.sh", "PATCHHARBOR.CRUNNER.CONTEXT.FLAG")
    result = run_c(downloads, "--no-progress-context", str(patch))
    assert result.returncode == 0, result.stdout
    assert "Roadmap / Milestone" not in result.stdout
    assert "Progress Context" not in result.stdout
    assert "ERFOLG" in result.stdout


def test_no_context_alias_hides_context_but_keeps_success_band(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    patch = write_patch(downloads, "patch.sh", "PATCHHARBOR.CRUNNER.CONTEXT.ALIAS")
    result = run_c(downloads, "--no-context", str(patch))
    assert result.returncode == 0, result.stdout
    assert "Roadmap / Milestone" not in result.stdout
    assert "Progress Context" not in result.stdout
    assert "ERFOLG" in result.stdout


def test_progress_context_env_var_hides_context(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    patch = write_patch(downloads, "patch.sh", "PATCHHARBOR.CRUNNER.CONTEXT.ENV")
    result = run_c(downloads, str(patch), progress_context="0")
    assert result.returncode == 0, result.stdout
    assert "Roadmap / Milestone" not in result.stdout
    assert "Progress Context" not in result.stdout
    assert "ERFOLG" in result.stdout


def test_c_runner_progress_context_switch_is_documented_in_runner_source() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "--no-progress-context" in text
    assert "--no-context" in text
    assert "C_RUNNER_PROGRESS_CONTEXT" in text
    assert "show_progress_context" in text


def test_c_runner_progress_context_switch_tests_have_no_private_values() -> None:
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
