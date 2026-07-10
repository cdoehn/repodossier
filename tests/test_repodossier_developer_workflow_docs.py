from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "planning/patchharbor/repodossier-developer-workflow.md"
ALIASES = ROOT / "docs/dev-aliases.md"
PATCH_RULES = ROOT / "scripts/dev/patch-rules.md"
C_RUNNER = ROOT / "scripts/dev/run_latest_download_patch.sh"
R_RUNNER = ROOT / "scripts/dev/r.sh"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_developer_workflow_doc_exists_and_records_current_commands() -> None:
    text = read(WORKFLOW)

    required = [
        "PATCHHARBOR.14c1 – RepoDossier Developer Workflow",
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/run_patchharbor_patch.sh",
        "scripts/dev/r.sh",
        "scripts/dev/run_repodossier_exports.sh",
        "patchharbor lint-script",
        "patchharbor run-script",
        "patchharbor audit-public",
        "patchharbor check-env",
        "PATCHHARBOR.14c2",
        "PATCHHARBOR.14c3",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_alias_docs_match_current_source_wrappers() -> None:
    text = read(ALIASES)

    required = [
        "scripts/dev/install_aliases.sh",
        'bash "$REPODOSSIER_REPO/scripts/dev/run_latest_download_patch.sh"',
        'bash "$REPODOSSIER_REPO/scripts/dev/r.sh"',
        "patchharbor lint-script",
        "patchharbor run-script",
        "patchharbor audit-public",
        "patchharbor check-env",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_patch_rules_point_to_current_developer_workflow_docs() -> None:
    text = read(PATCH_RULES)

    required = [
        "Current RepoDossier developer workflow after PatchHarbor cleanup",
        "planning/patchharbor/repodossier-developer-workflow.md",
        "docs/dev-aliases.md",
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/r.sh",
        "PatchHarbor `lint-script`",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_removed_legacy_helpers_are_documented_as_removed_not_active() -> None:
    workflow = read(WORKFLOW)
    aliases = read(ALIASES)
    patch_rules = read(PATCH_RULES)

    removed = [
        "scripts/dev/validate_patch_metadata.py",
        "scripts/dev/lint_patch_script.py",
        "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh",
    ]

    assert "Removed legacy helpers" in workflow
    assert "Removed legacy helper paths are not active commands" in aliases
    assert "Removed legacy metadata, lint, and candidate-runner helpers are not active workflow commands" in patch_rules

    for marker in removed:
        assert marker in workflow
        assert marker in aliases
        assert marker not in patch_rules
        assert not (ROOT / marker).exists()


def test_productive_c_and_r_runners_remain_present() -> None:
    assert C_RUNNER.is_file()
    assert R_RUNNER.is_file()

    c_text = read(C_RUNNER)
    r_text = read(R_RUNNER)

    assert "run_patchharbor_cli lint-script" in c_text
    assert "PY_META_C_RUNNER_14B2" in c_text
    assert "run_repodossier_exports.sh" in r_text


def test_developer_workflow_docs_do_not_store_private_local_values() -> None:
    checked = [WORKFLOW, ALIASES, PATCH_RULES, Path(__file__).resolve()]
    text = "\n".join(read(path) for path in checked)
    private_forbidden = [
        "/home/" + "christian",
        "christian" + "@",
        "christian.doehn" + "@" + "gmail.com",
        "Think" + "Pad",
        "Blade-" + "15",
        "~/" + "Projekte",
    ]

    for value in private_forbidden:
        assert value not in text

    newly_written_text = "\n".join(read(path) for path in [WORKFLOW, ALIASES, Path(__file__).resolve()])
    assert chr(96) * 3 not in newly_written_text

    patch_rules_text = read(PATCH_RULES)
    marker = "## 14c1. Current RepoDossier developer workflow after PatchHarbor cleanup"
    assert marker in patch_rules_text
    new_patch_rules_section = patch_rules_text.split(marker, 1)[1]
    assert chr(96) * 3 not in new_patch_rules_section
