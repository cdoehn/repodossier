from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.dev.audit_public_repo import scan_text

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "dev" / "audit_public_repo.py"


def test_scan_text_finds_private_patterns_without_storing_literal_in_test() -> None:
    text = "x " + "Christian " + "Döhn" + " y\n" + "/home/" + "christian" + "/project\n"

    findings = scan_text("sample.txt", text)

    assert len(findings) == 2
    assert findings[0].line == 1
    assert findings[1].line == 2


def test_public_repo_audit_accepts_tracked_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(AUDIT), "--repo", str(ROOT), "--tracked"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Public repo tracked-file audit OK" in result.stdout
