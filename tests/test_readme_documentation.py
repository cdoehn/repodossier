"""Documentation regression tests for README.md."""

from __future__ import annotations

from pathlib import Path


def test_readme_documents_call_graph_static_analysis_and_limitations() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "RepoDossier statically analyzes Python function and method calls" in readme
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
    assert "repodossier export-ai" in readme
    assert "full.txt\nai.txt" in readme
    assert "## Output: ai.txt" in readme
    assert "The AI export is intentionally compact" in readme
    assert "Planned but not complete yet:\n\n- `ai.txt`" not in readme
    assert "`changed.txt` is planned but not complete yet" not in readme


def test_readme_documents_docs_export_usage_and_completed_status():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "repodossier export-docs" in readme
    assert "## Output: docs.txt" in readme
    assert "documentation-only `docs.txt` export" in readme
    assert "`full.txt`, `ai.txt`, `docs.txt`, and `changed.txt`" in readme

    planned_section = readme.split("Planned but not complete yet:", 1)[1].split("## Installation", 1)[0]
    assert "- `docs.txt`" not in planned_section


def test_readme_documents_docs_exporter_module():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "repodossier.exporters.docs" in readme
    assert "documentation-only `docs.txt` context creation, rendering, and writing" in readme


def test_architecture_documents_docs_exporter_scope():
    architecture = Path("architecture.md").read_text(encoding="utf-8")

    assert "## exporters/docs.py" in architecture
    assert "docs.txt" in architecture
    assert "Contains documentation files only" in architecture


def test_readme_no_longer_lists_dependency_detection_as_planned() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    planned_section = readme.split("Planned but not complete yet:", 1)[1].split(
        "## Installation", 1
    )[0]

    assert "dependency summary from `pyproject.toml` and requirements files" not in planned_section


def test_readme_lists_dependencies_in_full_and_ai_exports() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    full_output_section = readme.split("## Output: full.txt", 1)[1].split(
        "## Output: ai.txt", 1
    )[0]
    ai_output_section = readme.split("## Output: ai.txt", 1)[1].split(
        "## Output: docs.txt", 1
    )[0]

    assert "Dependencies" in full_output_section
    assert "Dependencies" in ai_output_section

def test_readme_documents_multi_signal_important_file_ranking() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "multi-signal important-file ranking for AI exports" in readme
    assert "## Output: ai.txt" in readme
    assert "### Important file ranking" in readme
    assert "The `Important Files` section is produced by RepoDossier's shared important-file ranking." in readme

    assert "CLI and Python entrypoints from `pyproject.toml`" in readme
    assert "import graph centrality" in readme
    assert "call graph centrality" in readme
    assert "documentation relevance" in readme
    assert "structural project files" in readme

    assert "`full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` are excluded" in readme


def test_readme_no_longer_lists_important_file_ranking_as_planned() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    planned_section = readme.split("Planned but not complete yet:", 1)[1].split(
        "## Installation", 1
    )[0]

    assert "advanced important-file ranking" not in planned_section


def test_readme_documents_changed_export_usage() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "### Changed-files export" in readme
    assert "repodossier changed" in readme
    assert "repodossier changed --branch main" in readme
    assert "repodossier changed --output review-changes.txt" in readme
    assert "repodossier changed --no-diff" in readme


def test_readme_documents_changed_txt_output() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Output: changed.txt" in readme
    assert "Changed Files Summary" in readme
    assert "Git Diff" in readme
    assert "Changed File Contents" in readme
    assert "Deleted Files" in readme
    assert "Binary / Skipped Files" in readme


def test_readme_no_longer_lists_changed_export_as_planned_or_incomplete() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    planned_start = readme.find("Planned but not complete yet:")
    assert planned_start != -1

    next_heading = readme.find("## Installation", planned_start)
    assert next_heading != -1

    planned_section = readme[planned_start:next_heading]

    assert "- `changed.txt`" not in planned_section
    assert "`changed.txt` is planned but not complete yet" not in readme
    assert "- `changed.txt` export for git diffs, changed file contents, and branch comparisons" in readme
    assert "The `changed.txt` export is different" in readme


def test_readme_changed_export_code_fences_are_plain_markdown() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert '```bash id="' not in readme
    assert '```text id="' not in readme
    assert '``` id="' not in readme


def test_readme_documents_secret_detection():
    from pathlib import Path

    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Secret Detection" in readme
    assert "API_KEY" in readme
    assert "TOKEN" in readme
    assert "SECRET" in readme
    assert "PASSWORD" in readme
    assert "masked" in readme.lower()
    assert "best-effort" in readme.lower()
    assert "full.txt" in readme
    assert "ai.txt" in readme
    assert "docs.txt" in readme
    assert "changed.txt" in readme
    assert "REDACTED" in readme


def test_readme_lists_secret_detection_as_implemented_not_planned():
    from pathlib import Path

    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Secret Detection" in readme
    assert "- secret detection" not in readme
    assert "Planned but not complete yet:" in readme
