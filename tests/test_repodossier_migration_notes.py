from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "planning" / "patchharbor" / "repodossier-migration-notes.md"
WORKFLOW = ROOT / "planning" / "patchharbor" / "repodossier-developer-workflow.md"
INSTALL = ROOT / "docs" / "installation.md"
PATCH_RULES = ROOT / "scripts" / "dev" / "patch-rules.md"
README = ROOT / "README.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_migration_notes_exist_and_record_current_source_state() -> None:
    text = read(NOTES)

    required = [
        "PATCHHARBOR.14c3 – RepoDossier migration notes",
        "planning/milestones_migration.md",
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/r.sh",
        "scripts/dev/run_repodossier_exports.sh",
        "scripts/dev/run_patchharbor_patch.sh",
        "scripts/dev/install_aliases.sh",
        "patchharbor lint-script",
        "patchharbor run-script",
        "patchharbor audit-public",
        "patchharbor check-env",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_migration_notes_record_14b_cleanup_sequence() -> None:
    text = read(NOTES)

    required = [
        "PATCHHARBOR.14b1",
        "scripts/dev/validate_patch_metadata.py",
        "internal metadata validation inside scripts/dev/run_latest_download_patch.sh",
        "PATCHHARBOR.14b2",
        "scripts/dev/lint_patch_script.py",
        "patchharbor lint-script",
        "PATCHHARBOR.14b3",
        "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh",
        "PATCHHARBOR.14b4",
        "one self-copy bootstrap",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing

    positions = [text.index(marker) for marker in ["PATCHHARBOR.14b1", "PATCHHARBOR.14b2", "PATCHHARBOR.14b3", "PATCHHARBOR.14b4"]]
    assert positions == sorted(positions)


def test_migration_notes_record_14c_documentation_sequence() -> None:
    text = read(NOTES)

    required = [
        "PATCHHARBOR.14c1",
        "planning/patchharbor/repodossier-developer-workflow.md",
        "docs/dev-aliases.md",
        "PATCHHARBOR.14c2",
        "README.md",
        "docs/installation.md",
        "PATCHHARBOR.14c4",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_migration_notes_link_back_from_workflow_and_install_docs() -> None:
    workflow = read(WORKFLOW)
    install = read(INSTALL)

    assert "PATCHHARBOR.14c3 applied" in workflow
    assert "planning/patchharbor/repodossier-migration-notes.md" in workflow
    assert "PATCHHARBOR.14c3 records source-cleanup migration notes" in install
    assert "planning/patchharbor/repodossier-migration-notes.md" in install


def test_removed_helper_paths_are_historical_and_not_active_instructions() -> None:
    notes = read(NOTES)
    patch_rules = read(PATCH_RULES)
    readme = read(README)
    install = read(INSTALL)

    removed = [
        "scripts/dev/validate_patch_metadata.py",
        "scripts/dev/lint_patch_script.py",
        "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh",
    ]

    assert "Do not recreate removed source helper wrappers" in notes
    assert "historical migration facts" in notes

    for marker in removed:
        assert marker in notes
        assert not (ROOT / marker).exists()
        assert marker not in patch_rules
        assert marker not in readme
        assert marker not in install


def test_migration_notes_do_not_store_private_local_values_or_fences() -> None:
    text = "\n".join(read(path) for path in [NOTES, Path(__file__).resolve()])
    forbidden = [
        "/home/" + "christian",
        "christian" + "@",
        "christian.doehn" + "@" + "gmail.com",
        "Think" + "Pad",
        "Blade-" + "15",
        "~/" + "Projekte",
    ]

    for value in forbidden:
        assert value not in text

    assert chr(96) * 3 not in text
