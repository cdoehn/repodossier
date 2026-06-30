from __future__ import annotations

from pathlib import Path


def test_readme_documents_bash_support():
    readme = Path("README.md").read_text(encoding="utf-8").lower()

    assert "bash support" in readme
    assert ".sh" in readme
    assert ".bash" in readme
    assert "function discovery" in readme
    assert "symbol index" in readme
    assert "bash call graph" in readme


def test_readme_says_bash_analysis_is_static_and_safe():
    readme = Path("README.md").read_text(encoding="utf-8").lower()

    assert "static" in readme
    assert "does not execute" in readme
    assert "eval" in readme
    assert "complete bash grammar" in readme


def test_readme_lists_bash_support_as_implemented_not_planned():
    readme = Path("README.md").read_text(encoding="utf-8")
    lower_readme = readme.lower()

    assert "bash source detection" in lower_readme
    assert "static bash call graph support" in lower_readme

    planned_section = readme.split("Planned but not complete yet:", 1)[1].split(
        "## Installation",
        1,
    )[0]
    assert "Bash symbol and call graph support" not in planned_section

