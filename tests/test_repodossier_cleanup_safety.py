from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEANUP_INVENTORY = ROOT / "planning/patchharbor/repodossier-script-cleanup-inventory.md"
REPLACED_LOGIC_MAP = ROOT / "planning/patchharbor/replaced-source-logic-map.md"
MILESTONES = ROOT / "planning/milestones_migration.md"

DELETE_CANDIDATES = {
    "scripts/dev/validate_patch_metadata.py": [
        "src/patchharbor/metadata.py",
        "src/patchharbor/runner_preflight.py",
        "PATCHHARBOR.14b1",
    ],
    "scripts/dev/lint_patch_script.py": [
        "src/patchharbor/patch_lint_api.py",
        "patchharbor lint-script",
        "PATCHHARBOR.14b2",
    ],
    "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh": [
        "src/patchharbor/runner_core.py",
        "PATCHHARBOR.14b3",
    ],
}

HIGH_RISK_KEEP_FILES = {
    "scripts/dev/run_latest_download_patch.sh",
    "scripts/dev/run_patchharbor_patch.sh",
    "scripts/dev/r.sh",
    "scripts/dev/run_repodossier_exports.sh",
    "scripts/dev/install_aliases.sh",
    "scripts/dev/patch-rules.md",
    "scripts/dev/patch-workflow-rules.json",
    "scripts/dev/patch-workflow-rules.schema.json",
    "scripts/dev/validate_patch_workflow_rules.py",
    "scripts/dev/repo_patch_helper.py",
}

ACTIVE_REFERENCE_FILES = {
    "scripts/dev/install_aliases.sh",
    "scripts/dev/run_patchharbor_patch.sh",
    "scripts/dev/r.sh",
    "scripts/dev/run_repodossier_exports.sh",
    "tests/test_repodossier_cleanup_safety.py",
}

FUNCTIONAL_REPLACEMENT_MARKERS = {
    "patchharbor audit-public",
    "patchharbor check-env",
    "patchharbor lint-script",
    "src/patchharbor/runner_core.py",
    "src/patchharbor/metadata.py",
    "src/patchharbor/export_model.py",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def active_texts() -> dict[str, str]:
    return {
        relative: read(ROOT / relative)
        for relative in ACTIVE_REFERENCE_FILES
        if (ROOT / relative).is_file()
    }


def test_cleanup_inventory_and_replaced_logic_map_are_present() -> None:
    assert CLEANUP_INVENTORY.is_file()
    assert REPLACED_LOGIC_MAP.is_file()

    cleanup = read(CLEANUP_INVENTORY)
    replaced = read(REPLACED_LOGIC_MAP)
    milestones = read(MILESTONES)

    required = [
        "PATCHHARBOR.14a1 – RepoDossier Script Cleanup Inventory",
        "PATCHHARBOR.14a2 – Replaced Logic Map",
        "PATCHHARBOR.14a3 – Cleanup Safety Tests",
        "PATCHHARBOR.14b1 – Remove obsolete metadata helper wrapper",
        "PATCHHARBOR.14b2 – Remove obsolete lint wrapper",
        "PATCHHARBOR.14b3 – Remove obsolete runner helper part 1",
        "PATCHHARBOR.14b4 – Remove obsolete runner helper part 2",
    ]
    combined = cleanup + "\n" + replaced + "\n" + milestones
    missing = [marker for marker in required if marker not in combined]
    assert not missing, missing


def test_cleanup_candidates_have_documented_replacements_and_order() -> None:
    replaced = read(REPLACED_LOGIC_MAP)

    for candidate, markers in DELETE_CANDIDATES.items():
        assert candidate in replaced
        missing = [marker for marker in markers if marker not in replaced]
        assert not missing, (candidate, missing)
        assert "Deletion gate:" in replaced

    ordered_markers = [
        "PATCHHARBOR.14b1",
        "PATCHHARBOR.14b2",
        "PATCHHARBOR.14b3",
        "PATCHHARBOR.14b4",
    ]
    positions = [replaced.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)


def test_high_risk_and_source_policy_files_are_kept_before_cleanup_removal() -> None:
    cleanup = read(CLEANUP_INVENTORY)
    replaced = read(REPLACED_LOGIC_MAP)

    for relative in HIGH_RISK_KEEP_FILES:
        assert (ROOT / relative).is_file(), relative
        assert relative in cleanup
        assert relative in replaced

    keep_markers = [
        "high-risk",
        "source-policy",
        "keep source-side",
        "Keep for now",
        "Do not jump directly to deleting high-risk files.",
    ]
    combined = cleanup + "\n" + replaced
    missing = [marker for marker in keep_markers if marker not in combined]
    assert not missing, missing


def test_missing_delete_candidates_are_not_referenced_by_active_wrappers() -> None:
    texts = active_texts()

    for candidate in DELETE_CANDIDATES:
        if (ROOT / candidate).exists():
            continue

        offenders = [
            path
            for path, text in texts.items()
            if path != "tests/test_repodossier_cleanup_safety.py" and candidate in text
        ]
        assert not offenders, (candidate, offenders)


def test_aliases_keep_c_and_r_compatibility_paths_intact() -> None:
    aliases = read(ROOT / "scripts/dev/install_aliases.sh")
    r_wrapper = read(ROOT / "scripts/dev/r.sh")
    c_wrapper = read(ROOT / "scripts/dev/run_patchharbor_patch.sh")

    assert "alias c=" in aliases
    assert "alias r=" in aliases
    assert "scripts/dev/r.sh" in aliases
    assert "run_latest_download_patch.sh" in aliases or "run_patchharbor_patch.sh" in aliases
    assert "run_repodossier_exports.sh" in r_wrapper
    assert "patchharbor" in c_wrapper.lower()


def test_cleanup_safety_requires_functional_replacement_markers_not_display_layout() -> None:
    cleanup = read(CLEANUP_INVENTORY)
    replaced = read(REPLACED_LOGIC_MAP)
    combined = cleanup + "\n" + replaced

    missing = [marker for marker in FUNCTIONAL_REPLACEMENT_MARKERS if marker not in combined]
    assert not missing, missing

    display_markers = [
        "display-only formatting is not treated as a functional cleanup blocker",
        "display-only output layout tests are skipped or separated from functional cleanup tests",
    ]
    missing_display_policy = [marker for marker in display_markers if marker not in combined]
    assert not missing_display_policy, missing_display_policy


def test_cleanup_safety_docs_do_not_allow_immediate_high_risk_deletion() -> None:
    replaced = read(REPLACED_LOGIC_MAP)

    forbidden_claims = [
        "delete all source scripts",
        "remove all wrappers",
        "remove `scripts/dev/run_latest_download_patch.sh` immediately",
        "delete `scripts/dev/repo_patch_helper.py`",
    ]

    for claim in forbidden_claims:
        assert claim not in replaced


def test_cleanup_safety_files_do_not_store_private_local_values() -> None:
    checked = [
        CLEANUP_INVENTORY,
        REPLACED_LOGIC_MAP,
        Path(__file__).resolve(),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
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


def test_removed_metadata_helper_has_no_active_source_references() -> None:
    candidate = "scripts/dev/validate_patch_metadata.py"
    if (ROOT / candidate).exists():
        return

    checked = [
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/install_aliases.sh",
        "scripts/dev/run_patchharbor_patch.sh",
        "scripts/dev/r.sh",
    ]
    offenders = [
        relative
        for relative in checked
        if candidate in (ROOT / relative).read_text(encoding="utf-8")
    ]
    assert not offenders, offenders


def test_removed_lint_wrapper_has_no_active_source_references() -> None:
    candidate = "scripts/dev/lint_patch_script.py"
    if (ROOT / candidate).exists():
        return

    checked = [
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/install_aliases.sh",
        "scripts/dev/run_patchharbor_patch.sh",
        "scripts/dev/r.sh",
        "scripts/dev/patch-rules.md",
    ]
    offenders = [
        relative
        for relative in checked
        if candidate in (ROOT / relative).read_text(encoding="utf-8")
    ]
    assert not offenders, offenders


def test_removed_download_runner_candidate_has_no_active_source_references() -> None:
    candidate = "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh"
    if (ROOT / candidate).exists():
        return

    checked = [
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/run_patchharbor_patch.sh",
        "scripts/dev/install_aliases.sh",
        "scripts/dev/r.sh",
        "scripts/dev/patch-rules.md",
    ]
    offenders = [
        relative
        for relative in checked
        if candidate in (ROOT / relative).read_text(encoding="utf-8")
    ]
    assert not offenders, offenders


def test_runner_helper_part2_cleanup_keeps_single_c_self_copy_bootstrap() -> None:
    runner = ROOT / "scripts/dev/run_latest_download_patch.sh"
    text = runner.read_text(encoding="utf-8")

    assert text.count('original_runner="${BASH_SOURCE[0]}"') == 1
    assert text.count('C_RUNNER_SELF_COPY=1 C_RUNNER_ORIGINAL=') == 1
    assert 'self_copy="$(mktemp' not in text
    assert "run_patchharbor_cli lint-script" in text
    assert "PY_META_C_RUNNER_14B2" in text
