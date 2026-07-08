from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY = REPO_ROOT / "planning" / "patchharbor" / "dev-scripts-inventory.md"


def test_patchharbor_inventory_exists_and_names_core_dev_scripts():
    text = INVENTORY.read_text(encoding="utf-8")

    assert "# PatchHarbor Dev-Script Migration Inventory" in text
    assert "scripts/dev/run_latest_download_patch.sh" in text
    assert "scripts/dev/repo_patch_helper.py" in text
    assert "scripts/dev/lint_patch_script.py" in text
    assert "scripts/dev/run_repodossier_exports.sh" in text


def test_patchharbor_inventory_documents_migration_boundaries():
    text = INVENTORY.read_text(encoding="utf-8")

    assert "source repository only" in text
    assert "no target repository changes" in text
    assert "thin RepoDossier wrappers" in text
    assert "Do not remove or destructively rewrite RepoDossier scripts" in text


def test_patchharbor_inventory_avoids_local_private_markers():
    text = INVENTORY.read_text(encoding="utf-8")

    disallowed_fragments = [
        "/home/",
        "/Users/",
        "\\Users\\",
        "@gmail.com",
        "@outlook.",
        "@hotmail.",
    ]

    for fragment in disallowed_fragments:
        assert fragment not in text
