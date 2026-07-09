from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "planning/patchharbor/c-alias-contract.md"
CRITERIA = ROOT / "planning/patchharbor/c-alias-switch-criteria.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_c_alias_contract_document_exists_and_preserves_current_target() -> None:
    text = read(CONTRACT)

    assert "Current `c` alias contract" in text
    assert "scripts/dev/run_latest_download_patch.sh" in text
    assert "patchharbor-patch" in text
    assert "scripts/dev/run_patchharbor_patch.sh" in text
    assert "`c` is not switched yet" in text


def test_c_alias_switch_criteria_document_exists_and_requires_parity() -> None:
    text = read(CRITERIA)

    assert "`c` alias switch criteria" in text
    assert "This patch does not switch `c`" in text
    assert "metadata validation parity is tested" in text
    assert "repeat-detection parity is tested" in text
    assert "freshness-check parity is tested" in text
    assert "successful patch lifecycle parity is tested" in text
    assert "failed patch lifecycle parity is tested" in text
    assert "footer and progress context parity is tested" in text


def test_switch_plan_requires_rollback_and_focused_tests() -> None:
    text = read(CRITERIA)

    assert "one-command rollback" in text
    assert "how to verify rollback" in text
    assert "which files changed" in text
    assert "which tests prove parity" in text
    assert "dry-run does not write shell rc files" in text
    assert "no private path literals are stored in tracked files" in text


def test_switch_plan_forbids_silent_or_combined_alias_changes() -> None:
    text = read(CRITERIA)

    forbidden_actions = [
        "switching `c` and changing export scripts",
        "switching `c` and deleting the old runner",
        "switching `c` and changing `r`",
        "switching `c` and installing aliases into the real shell environment",
        "switching `c` without focused tests",
    ]
    for phrase in forbidden_actions:
        assert phrase in text


def test_source_alias_files_still_reflect_non_switched_state() -> None:
    installer = read(ROOT / "scripts/dev/install_aliases.sh")

    assert "alias c=" in installer
    assert "scripts/dev/run_latest_download_patch.sh" in installer
    assert "alias r=" in installer
    assert "scripts/dev/r.sh" in installer
    assert "alias patchharbor-patch=" in installer
    assert "scripts/dev/run_patchharbor_patch.sh" in installer


def test_c_alias_switch_plan_files_do_not_store_private_local_values() -> None:
    checked = [
        CONTRACT,
        CRITERIA,
        ROOT / "tests/test_c_alias_switch_plan.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
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
