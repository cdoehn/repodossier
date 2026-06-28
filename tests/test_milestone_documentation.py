"""Regression tests for milestone planning documents."""

from __future__ import annotations

from pathlib import Path


def test_milestone9_file_is_clean_markdown_document() -> None:
    content = Path("planning/MILESTONE9.md").read_text(encoding="utf-8")

    assert content.startswith("MILESTONE 9 – Documentation Export")
    assert "Ja, hier ist **MILESTONE9.md vollständig** zum Kopieren:" not in content
    assert not content.rstrip().endswith("````")
