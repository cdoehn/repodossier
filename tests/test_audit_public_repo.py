from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.dev.audit_public_repo import (
    _findings_from_patchharbor_stdout,
    _patchharbor_cli_pattern_args,
    scan_text,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "dev" / "audit_public_repo.py"


def test_scan_text_finds_private_patterns_without_storing_literal_in_test() -> None:
    text = "x " + "Christian " + "Döhn" + " y\n" + "/home/" + "christian" + "/project\n"

    findings = scan_text("sample.txt", text)

    assert len(findings) == 2
    assert findings[0].line == 1
    assert findings[1].line == 2


def test_scan_text_accepts_custom_patterns() -> None:
    findings = scan_text("sample.txt", "alpha\nneedle here\n", ["needle"])

    assert len(findings) == 1
    assert findings[0].pattern == "needle"
    assert findings[0].text == "needle here"


def test_scan_text_ignores_split_private_email_test_literals() -> None:
    text = '"christian.doehn" + "@" + "gmail.com"\n'

    assert scan_text("test_file.py", text) == []


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


def test_public_repo_audit_wraps_patchharbor_public_audit_helper_additively() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    required = [
        "PATCHHARBOR_REPO",
        "PATCHHARBOR_SRC",
        "patchharbor.public_audit_checks",
        "audit-public",
        "_run_patchharbor_tracked_scan",
        "_scan_tracked_legacy",
        "_patchharbor_cli_pattern_args",
        "_findings_from_patchharbor_stdout",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_patchharbor_cli_pattern_args_cover_default_patterns_without_literals() -> None:
    args = _patchharbor_cli_pattern_args(["TOKEN", "SECOND"])

    assert args == [
        "--pattern",
        "pattern_1=TOKEN",
        "--pattern",
        "pattern_2=SECOND",
    ]


def test_patchharbor_stdout_is_converted_to_legacy_findings() -> None:
    stdout = "file.txt:2:4: error/person_name: contains name\nstatus: failed\n"

    findings = _findings_from_patchharbor_stdout(stdout)

    assert len(findings) == 1
    assert findings[0].path == "file.txt"
    assert findings[0].line == 2
    assert findings[0].pattern == "Christian " + "Döhn"
    assert findings[0].text == "contains name"


def test_patchharbor_stdout_maps_full_email_pattern_without_bare_handle_false_positive() -> None:
    stdout = "file.txt:1:1: error/person_email: contains email\nstatus: failed\n"

    findings = _findings_from_patchharbor_stdout(stdout)

    assert len(findings) == 1
    assert findings[0].pattern == "christian" + ".doehn" + "@" + "gmail.com"
