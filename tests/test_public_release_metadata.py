from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_readme_contains_public_github_badges_and_metadata():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "[![CI](https://github.com/cdoehn/repodossier/actions/workflows/ci.yml/badge.svg)]" in text
    assert "[![License: MIT]" in text
    assert "[![Python 3.12+]" in text
    assert "Description: AI-friendly repository exports for coding assistants" in text
    assert "Website: https://github.com/cdoehn/repodossier" in text
    assert "context-export" in text
    assert "developer-tools" in text


def test_pyproject_contains_public_project_urls():
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "[project.urls]" in text
    assert 'Homepage = "https://github.com/cdoehn/repodossier"' in text
    assert 'Repository = "https://github.com/cdoehn/repodossier"' in text
    assert 'Issues = "https://github.com/cdoehn/repodossier/issues"' in text
    assert 'Documentation = "https://github.com/cdoehn/repodossier#readme"' in text
    assert 'Changelog = "https://github.com/cdoehn/repodossier/releases"' in text

def test_dev_dependencies_include_release_validation_tools() -> None:
    import tomllib
    from pathlib import Path

    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = data["project"]["optional-dependencies"]["dev"]

    assert "build>=1.2" in dev_dependencies
    assert "twine>=5.0" in dev_dependencies

def test_pyproject_declares_readme_for_package_metadata():
    import tomllib
    from pathlib import Path

    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["readme"] == "README.md"


def test_pyproject_uses_modern_spdx_license_metadata():
    import tomllib
    from pathlib import Path

    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["license"] == "MIT"
    assert data["project"]["license-files"] == ["LICENSE"]
    assert "License :: OSI Approved :: MIT License" not in data["project"]["classifiers"]

