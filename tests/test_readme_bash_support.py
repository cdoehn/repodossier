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
