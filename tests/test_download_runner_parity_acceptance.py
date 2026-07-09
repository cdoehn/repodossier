from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "planning/patchharbor/download-runner-parity-acceptance.md"
PARITY_FILES = {
    "PATCHHARBOR.10b1": ROOT / "tests/test_download_runner_metadata_parity.py",
    "PATCHHARBOR.10b2": ROOT / "tests/test_download_runner_freshness_parity.py",
    "PATCHHARBOR.10b3": ROOT / "tests/test_download_runner_repeat_parity.py",
    "PATCHHARBOR.10b4": ROOT / "tests/test_download_runner_syntax_parity.py",
    "PATCHHARBOR.10b5": ROOT / "tests/test_download_runner_success_lifecycle_parity.py",
    "PATCHHARBOR.10b6": ROOT / "tests/test_download_runner_failure_lifecycle_parity.py",
    "PATCHHARBOR.10b7": ROOT / "tests/test_download_runner_footer_parity.py",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_download_runner_parity_acceptance_document_exists() -> None:
    text = _read(ACCEPTANCE)
    assert "PATCHHARBOR.10b8" in text
    assert "Download Runner Parity Acceptance" in text
    assert "This document accepts the completed source-side download runner parity test phase." in text


def test_acceptance_references_all_10b_parity_test_files() -> None:
    text = _read(ACCEPTANCE)
    for step, path in PARITY_FILES.items():
        relative = path.relative_to(ROOT).as_posix()
        assert step in text, step
        assert relative in text, relative
        assert path.exists(), relative


def test_acceptance_covers_all_required_parity_areas() -> None:
    text = _read(ACCEPTANCE)
    required = [
        "metadata validation",
        "freshness checks",
        "repeat detection",
        "syntax failure handling",
        "success lifecycle",
        "failure lifecycle",
        "footer and completion output",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    assert not missing, missing


def test_acceptance_records_current_runner_contract_without_migrating_behavior() -> None:
    text = _read(ACCEPTANCE)
    required = [
        "valid metadata is accepted before execution",
        "invalid metadata stops before execution",
        "`progress_context=false` disables the patchscript context display",
        "old patchscripts require confirmation before execution",
        "repeat detection uses the applied ledger and done-file checks",
        "syntax failures stop before execution",
        "successful scripts move to `done`",
        "failed scripts move to `failed`",
        "ZIP input keeps the original archive as the lifecycle artifact",
        "log files remain in Downloads",
        "success runs update `.applied_patch_hashes.tsv`",
        "failure runs do not update `.applied_patch_hashes.tsv`",
        "final success and failure bands remain visible",
    ]
    missing = [phrase for phrase in required if phrase not in text]
    assert not missing, missing


def test_acceptance_records_10b_non_goals() -> None:
    text = _read(ACCEPTANCE)
    non_goals = [
        "change the runner implementation",
        "change PatchHarbor target code",
        "switch `c`",
        "change aliases",
        "change export scripts",
        "remove the existing RepoDossier runner",
        "introduce target-side download runner APIs",
    ]
    missing = [phrase for phrase in non_goals if phrase not in text]
    assert not missing, missing


def test_acceptance_declares_readiness_for_10c() -> None:
    text = _read(ACCEPTANCE)
    assert "PATCHHARBOR.10c may now start target-side planning/API work." in text
    assert "these parity tests as the safety net" in text
    assert "documented explicitly instead of silently weakening tests" in text


def test_each_parity_test_file_contains_a_representative_contract_marker() -> None:
    markers = {
        "tests/test_download_runner_metadata_parity.py": "Metadata OK",
        "tests/test_download_runner_freshness_parity.py": "Das Patchscript ist älter als",
        "tests/test_download_runner_repeat_parity.py": "Dieses Patchscript wurde bereits erfolgreich angewendet.",
        "tests/test_download_runner_syntax_parity.py": "Syntaxprüfung",
        "tests/test_download_runner_success_lifecycle_parity.py": "Patch erfolgreich.",
        "tests/test_download_runner_failure_lifecycle_parity.py": "Patch fehlgeschlagen.",
        "tests/test_download_runner_footer_parity.py": "ERFOLG  ERFOLG  ERFOLG",
    }
    missing: list[str] = []
    for relative, marker in markers.items():
        if marker not in _read(ROOT / relative):
            missing.append(f"{relative}: {marker}")
    assert not missing, missing


def test_download_runner_parity_acceptance_files_do_not_store_private_local_values() -> None:
    checked = [
        ACCEPTANCE,
        ROOT / "tests/test_download_runner_parity_acceptance.py",
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
        assert value not in text, value
