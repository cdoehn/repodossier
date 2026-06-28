from __future__ import annotations

from pathlib import Path


def test_readme_documents_dependency_detection_feature() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Dependency detection from pyproject.toml and requirements.txt" in readme
    assert "## Dependency Detection" in readme


def test_readme_documents_dependency_sources_and_exports() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "`pyproject.toml`" in readme
    assert "`requirements.txt`" in readme
    assert "requirements/*.txt" in readme
    assert "`full.txt`" in readme
    assert "`ai.txt`" in readme


def test_readme_documents_dependency_detection_limits() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "no package installation" in readme
    assert "no network access" in readme
    assert "no full dependency resolver" in readme
    assert "no lockfile analysis" in readme
    assert "unsupported requirement lines" in readme
