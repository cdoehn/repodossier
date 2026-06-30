import tomllib
from pathlib import Path


def test_pyproject_defines_repodossier_and_legacy_cli_scripts():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "repodossier"

    scripts = data["project"]["scripts"]
    assert scripts["repodossier"] == "repodossier.cli:main"
    assert scripts["repocontext"] == "repodossier.cli:main"


def test_repodossier_cli_wrapper_exposes_callable_main():
    from repodossier.cli import main

    assert callable(main)
