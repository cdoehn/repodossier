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
