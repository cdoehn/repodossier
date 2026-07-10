from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILE_INVENTORY = ROOT / "planning" / "patchharbor" / "export-runner-file-inventory.md"
BEHAVIOR_INVENTORY = ROOT / "planning" / "patchharbor" / "export-runner-behavior-inventory.md"
RUNNER = ROOT / "scripts" / "dev" / "run_repodossier_exports.sh"
R_WRAPPER = ROOT / "scripts" / "dev" / "r.sh"
ALIAS_INSTALLER = ROOT / "scripts" / "dev" / "install_aliases.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_export_runner_inventory_documents_exist() -> None:
    for path in (FILE_INVENTORY, BEHAVIOR_INVENTORY):
        assert path.exists(), str(path)
        assert path.stat().st_size > 1000, str(path)


def test_file_inventory_covers_current_source_files_and_artifacts() -> None:
    text = _read(FILE_INVENTORY)
    required = [
        "PATCHHARBOR.11a1",
        "scripts/dev/r.sh",
        "scripts/dev/run_repodossier_exports.sh",
        "scripts/dev/patch-rules.md",
        "scripts/dev/install_aliases.sh",
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
        "`all`",
        "`quick`",
        "`export-ai`",
        "`doc`",
        "`changes`",
        "`REPODOSSIER_BIN`",
        "`PATCH_DOWNLOAD_DIR`",
        "`r · RepoDossier Export Runner`",
        "`r abgeschlossen.`",
        "RepoDossier-specific parts",
        "Candidate generic parts",
        "PATCHHARBOR.11a1 does not:",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_behavior_inventory_covers_current_runner_contract() -> None:
    text = _read(BEHAVIOR_INVENTORY)
    required = [
        "PATCHHARBOR.11a2",
        "scripts/dev/r.sh",
        "scripts/dev/run_repodossier_exports.sh",
        "`--help` / `-h`",
        "`--list-modes`",
        "`--dry-run`",
        "Unknown modes are rejected with an `r error` line and exit code `2`.",
        "normal run with no mode arguments: `full ai`",
        "dry-run with no mode arguments: `full ai docs changed`",
        "`git rev-parse --show-toplevel`",
        "`REPODOSSIER_BIN`",
        "`PATCH_DOWNLOAD_DIR`",
        "`repodossier full`",
        "`repodossier export-ai`",
        "`repodossier export-docs`",
        "`repodossier changed`",
        "`patch-rules.md`",
        "`Dry-run: keine Dateien geschrieben.`",
        "`r abgeschlossen.`",
        "not in a Git repository",
        "`REPODOSSIER_BIN` not found",
        "unknown mode",
        "export command fails",
        "PATCHHARBOR.11a2 does not:",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_inventory_docs_match_actual_export_runner_modes_and_commands() -> None:
    file_inventory = _read(FILE_INVENTORY)
    behavior = _read(BEHAVIOR_INVENTORY)
    runner = _read(RUNNER)

    required_in_runner = [
        "ALL_MODES=(all full ai docs changed)",
        "ai|quick|export-ai)",
        "docs|doc)",
        "changed|changes)",
        "MODES=(full ai docs changed)",
        "MODES=(full ai)",
        '"$REPODOSSIER_BIN" full',
        '"$REPODOSSIER_BIN" export-ai',
        '"$REPODOSSIER_BIN" export-docs',
        '"$REPODOSSIER_BIN" changed',
        'copy_if_exists "full.txt" "$DOWNLOAD_DIR/full.txt"',
        'copy_if_exists "ai.txt" "$DOWNLOAD_DIR/ai.txt"',
        'copy_if_exists "docs.txt" "$DOWNLOAD_DIR/docs.txt"',
        'copy_if_exists "changed.txt" "$DOWNLOAD_DIR/changed.txt"',
    ]
    missing_runner = [marker for marker in required_in_runner if marker not in runner]
    assert not missing_runner, missing_runner

    shared_markers = [
        "full ai docs changed",
        "repodossier full",
        "repodossier export-ai",
        "repodossier export-docs",
        "repodossier changed",
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
    ]
    missing_docs: list[str] = []
    for marker in shared_markers:
        if marker not in file_inventory:
            missing_docs.append(f"file inventory: {marker}")
        if marker not in behavior:
            missing_docs.append(f"behavior inventory: {marker}")
    assert not missing_docs, missing_docs


def test_behavior_inventory_matches_actual_output_and_failure_markers() -> None:
    behavior = _read(BEHAVIOR_INVENTORY)
    runner = _read(RUNNER)

    shared_output_markers = [
        "r · RepoDossier Export Runner",
        "Repo:",
        "Downloads:",
        "Modi:",
        "Befehl:",
        "Kopiert:",
        "Dry-run: keine Dateien geschrieben.",
        "r abgeschlossen.",
    ]
    exact_runner_markers = [
        "Exportiere full",
        "Exportiere ai",
        "Exportiere docs",
        "Exportiere changed",
    ]
    missing = []
    for marker in shared_output_markers:
        if marker not in runner:
            missing.append(f"runner: {marker}")
        if marker not in behavior:
            missing.append(f"behavior inventory: {marker}")
    for marker in exact_runner_markers:
        if marker not in runner:
            missing.append(f"runner: {marker}")
    assert not missing, missing

    runner_failures = [
        "Kein Git-Repository",
        "RepoDossier-Befehl nicht gefunden:",
        "Unbekannter r-Modus:",
        "fehlgeschlagen. Exit-Code:",
    ]
    missing_runner = [marker for marker in runner_failures if marker not in runner]
    assert not missing_runner, missing_runner


def test_inventory_docs_keep_source_specific_and_generic_parts_separate() -> None:
    file_inventory = _read(FILE_INVENTORY)
    behavior = _read(BEHAVIOR_INVENTORY)
    combined = file_inventory + "\n" + behavior

    source_specific = [
        "exact RepoDossier CLI commands",
        "exact generated artifact names",
        "`REPODOSSIER_BIN` environment variable name",
        "`patch-rules.md` copy behavior",
        "German output markers used by `r`",
    ]
    missing = [marker for marker in source_specific if marker not in combined]
    assert not missing, missing

    generic_candidates = [
        "export job model",
        "export plan model",
        "command execution result model",
        "copy-if-exists artifact lifecycle",
        "dry-run planning display",
        "mode alias normalization shape",
    ]
    missing_generic = [marker for marker in generic_candidates if marker not in file_inventory]
    assert not missing_generic, missing_generic


def test_export_runner_inventory_non_goals_prevent_behavior_changes() -> None:
    combined = _read(FILE_INVENTORY) + "\n" + _read(BEHAVIOR_INVENTORY)
    non_goals = [
        "change `scripts/dev/r.sh`",
        "change `scripts/dev/run_repodossier_exports.sh`",
        "change aliases",
        "change export modes",
        "change RepoDossier CLI commands",
        "add target-side PatchHarbor export APIs",
        "remove source-side export logic",
        "switch `r`",
        "change output markers",
        "change alias installation",
    ]
    missing = [marker for marker in non_goals if marker not in combined]
    assert not missing, missing


def test_export_runner_source_files_still_match_inventory_entry_points() -> None:
    wrapper_text = _read(R_WRAPPER)
    runner_text = _read(RUNNER)
    alias_text = _read(ALIAS_INSTALLER)

    assert "run_repodossier_exports.sh" in wrapper_text
    assert "alias r=" in alias_text
    assert "scripts/dev/r.sh" in alias_text
    assert "REPODOSSIER_BIN" in runner_text
    assert "PATCH_DOWNLOAD_DIR" in runner_text
    assert "patch-rules.md" in runner_text
    assert "print_help()" in runner_text
    assert "normalize_mode()" in runner_text
    assert "run_mode()" in runner_text


def test_export_runner_inventory_docs_do_not_store_private_local_values() -> None:
    checked = [
        FILE_INVENTORY,
        BEHAVIOR_INVENTORY,
        ROOT / "tests/test_export_runner_inventory_docs.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
    forbidden = [
        "/home/" + "exampleuser",
        "user" + "@",
        "example.user" + "@" + "example.invalid",
        "Example" + "Laptop",
        "~/" + "Projects",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text, value
