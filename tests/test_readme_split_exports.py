"""Documentation regression tests for split exports."""

from __future__ import annotations

from pathlib import Path
import re


def _readme() -> str:
    return Path("README.md").read_text(encoding="utf-8")


def _planned_section(readme: str) -> str:
    match = re.search(
        r"(Planned but not complete yet:\n)(?P<body>.*?)(?=\n## |\Z)",
        readme,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group("body")


def test_readme_lists_split_exports_as_implemented() -> None:
    readme = _readme()

    implemented_section = readme.split("Implemented:", 1)[1].split(
        "Planned but not complete yet:", 1
    )[0]

    assert "- split exports for large `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` files" in implemented_section


def test_readme_no_longer_lists_split_exports_as_planned() -> None:
    readme = _readme()

    assert "split exports" not in _planned_section(readme).lower()


def test_readme_documents_split_export_commands_and_flags() -> None:
    readme = _readme()

    assert "### Split exports" in readme
    assert "repocontext full --split" in readme
    assert "repocontext export-ai --split" in readme
    assert "repocontext export-docs --split" in readme
    assert "repocontext changed --split" in readme
    assert "--split-max-chars" in readme
    assert "--split-strategy" in readme
    assert "--no-split" in readme


def test_readme_documents_split_part_file_names() -> None:
    readme = _readme()

    assert "full.part01.txt" in readme
    assert "ai.part01.txt" in readme
    assert "docs.part01.txt" in readme
    assert "changed.part01.txt" in readme
    assert "review-changes.part01.txt" in readme


def test_readme_documents_split_config_schema() -> None:
    readme = _readme()

    assert "exports:" in readme
    assert "split:" in readme
    assert "enabled: true" in readme
    assert "max_chars: 200000" in readme
    assert "strategy: heading" in readme
    assert "`exports.split.enabled`" in readme
    assert "`exports.split.max_chars`" in readme
    assert "`exports.split.strategy`" in readme
    assert "CLI options override the configuration file." in readme


def test_example_config_documents_split_settings() -> None:
    example = Path(".repocontext.example.yml").read_text(encoding="utf-8")

    assert "exports:" in example
    assert "split:" in example
    assert "enabled: false" in example
    assert "max_chars: 200000" in example
    assert "strategy: heading" in example
