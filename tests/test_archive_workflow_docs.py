from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_readme_documents_archive_cli_examples_and_zip_structure() -> None:
    text = _read("README.md")
    required = [
        "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER",
        "repodossier ./projekt ./output",
        "repodossier ./projekt/src/backend ./output",
        "repodossier ./projekt/backend ./projekt/frontend ./output",
        "repodossier ./repo-a ./repo-b ./output",
        "--output-name projektpaket.zip",
        "--output-name projektpaket.xml",
        "reports/",
        "reports/full.txt",
        "reports/ai.txt",
        "reports/docs.txt",
        "reports/changed.txt",
        "repositories/",
        "Source file: src/main.py",
        "Archive path: ../repositories/projekt/src/main.py",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []


def test_installation_doc_documents_pip_pipx_and_platform_target() -> None:
    text = _read("docs/installation.md")
    required = [
        "python3 -m pip install .",
        "python3 -m pipx install",
        "repodossier ./projekt ./output",
        "repodossier ./projekt/src/backend ./output",
        "repodossier ./repo-a ./repo-b ./output",
        "--output-name projektpaket.xml",
        "Ubuntu 26.04",
        "Ubuntu 24.04",
        "git archive --format=zip --output=repodossier.zip HEAD",
        "Git internals",
        "ignored files",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []


def test_archive_workflow_doc_covers_snapshot_and_source_reference_rules() -> None:
    text = _read("docs/archive-workflow.md")
    required = [
        "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER",
        "Source folders may be Git repository roots or subfolders",
        "reports/",
        "full.txt",
        "ai.txt",
        "docs.txt",
        "changed.txt",
        "not created in the source repository",
        "current working tree",
        "repositories/",
        "committed `HEAD` tree",
        "git archive --format=zip --output=repodossier.zip HEAD",
        "excludes staged changes, unstaged changes, untracked files, ignored files, `.git` metadata",
        "Source file: src/main.py",
        "Archive path: ../repositories/projekt/src/main.py",
        "central language detection",
        "python3 -m pip install .",
        "pipx install .",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []
