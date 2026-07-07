from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "dev" / "validate_patch_metadata.py"


def _write_script(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_validate_patch_metadata_accepts_patch_display_and_progress(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
            '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"scripts/dev/patch-rules.md","start":1,"end":1}',
            '# repodossier-meta: {"type":"display","context":2,"layout":"side-by-side","frame":false}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Metadata OK" in result.stdout


def test_validate_patch_metadata_rejects_missing_patch_record(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"display","context":2}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "expected exactly one patch" in result.stdout


def test_validate_patch_metadata_rejects_unknown_status(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
            '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"unknown","file":"scripts/dev/patch-rules.md","start":1,"end":1}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "status must be one of" in result.stdout


def test_validate_patch_metadata_rejects_missing_file(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
            '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"done","file":"missing.md","start":1,"end":1}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "file does not exist" in result.stdout
