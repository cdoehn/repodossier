"""Documentation tests for database schema export behavior."""

from pathlib import Path


def test_readme_documents_database_schema_export() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Database Schema Export" in readme
    assert "`full.txt`" in readme
    assert "`ai.txt`" in readme
    assert "# Database Schema" in readme
    assert "## Database Schema" in readme


def test_readme_documents_database_schema_safety_boundaries() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    required_phrases = [
        "does **not** export table contents",
        "opened read-only",
        "does not execute migrations",
        "best-effort",
        "Generated RepoContext exports",
    ]

    for phrase in required_phrases:
        assert phrase in readme


def test_readme_lists_database_schema_as_implemented_not_planned() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    implemented_section = readme.split("Implemented:", 1)[1].split(
        "Planned but not complete yet:",
        1,
    )[0]
    planned_section = readme.split("Planned but not complete yet:", 1)[1].split(
        "## Installation",
        1,
    )[0]

    assert "database schema extraction from SQLite databases and SQL schema files" in implemented_section
    assert "database schema extraction" not in planned_section.lower()
    assert "database schema export" not in planned_section.lower()


def test_readme_documents_database_schema_in_full_and_ai_section_order() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    full_output_section = readme.split("## Output: full.txt", 1)[1].split(
        "## Output: ai.txt",
        1,
    )[0]
    ai_output_section = readme.split("## Output: ai.txt", 1)[1].split(
        "## Output: docs.txt",
        1,
    )[0]

    assert "6. Database Schema" in full_output_section
    assert "7. Complete Source Export" in full_output_section
    assert full_output_section.index("5. Dependencies") < full_output_section.index("6. Database Schema")
    assert full_output_section.index("6. Database Schema") < full_output_section.index("7. Complete Source Export")

    assert "5. Database Schema" in ai_output_section
    assert "6. Symbol Index" in ai_output_section
    assert ai_output_section.index("4. Dependencies") < ai_output_section.index("5. Database Schema")
    assert ai_output_section.index("5. Database Schema") < ai_output_section.index("6. Symbol Index")


def test_readme_mentions_schema_module_in_architecture_overview() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "`repocontext.schema`" in readme
    assert "SQLite metadata extraction" in readme
    assert "SQL CREATE TABLE parsing" in readme

