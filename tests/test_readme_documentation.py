"""Documentation regression tests for README.md."""

from __future__ import annotations

from pathlib import Path


def test_readme_documents_call_graph_static_analysis_and_limitations() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "RepoContext statically analyzes Python function and method calls" in readme
    assert "Python source is parsed statically with `ast`" in readme
    assert "project code is not imported or executed" in readme
    assert "Dynamic calls" in readme
    assert "runtime imports" in readme
    assert "object method calls where the receiver type is unknown" in readme


def test_readme_documents_call_graph_export_size_limits() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Default `full.txt` Call Graph display limits:" in readme
    assert "| Internal calls | 200 |" in readme
    assert "| External calls | 25 |" in readme
    assert "| Ambiguous calls | 25 |" in readme
    assert "| Unresolved calls | 25 |" in readme
    assert "large call groups are truncated with deterministic `... more` lines" in readme


def test_readme_documents_call_graph_duplicate_semantics() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "identical call edges at the same call location are deduplicated" in readme
    assert "repeated calls on different lines remain visible" in readme

def test_readme_documents_ai_export_usage_and_completed_status() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "compact `ai.txt` export" in readme
    assert "repocontext export-ai" in readme
    assert "full.txt\nai.txt" in readme
    assert "## Output: ai.txt" in readme
    assert "The AI export is intentionally compact" in readme
    assert "Planned but not complete yet:\n\n- `ai.txt`" not in readme
    assert "`docs.txt` and `changed.txt` are planned but not complete yet" in readme

