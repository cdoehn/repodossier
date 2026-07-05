"""Markdown heading stability contracts for the Milestone 4 migration."""

from __future__ import annotations

import repodossier.changed_exporter as changed_exporter
import repodossier.exporters.ai as ai_exporter
import repodossier.exporters.docs as docs_exporter
import repodossier.exporters.full as full_exporter


def _top_level_headings(markdown_text: str) -> tuple[str, ...]:
    return tuple(
        line
        for line in markdown_text.splitlines()
        if line.startswith("# ") and not line.startswith("## ")
    )


def test_full_markdown_heading_order_contract() -> None:
    expected = (
        "# AI Quick Start",
        "# Repository Statistics",
        "# File Summary",
        "# Repository Tree",
        "# Dependencies",
        "# Database Schema",
        "# Complete Source Export",
        "# Warnings",
    )

    assert full_exporter.FULL_EXPORT_SECTION_ORDER == (
        "ai_quick_start",
        "repository_statistics",
        "file_summary",
        "repository_tree",
        "dependencies",
        "database_schema",
        "complete_source_export",
        "warnings",
    )
    assert full_exporter.iter_full_export_headings() == expected
    assert tuple(
        full_exporter.FULL_EXPORT_SECTION_HEADINGS[section_name]
        for section_name in full_exporter.FULL_EXPORT_SECTION_ORDER
    ) == expected


def test_ai_markdown_heading_order_contract() -> None:
    expected = (
        "# AI CONTEXT",
        "## Project",
        "## Architecture Summary",
        "## Important Files",
        "## Symbol Index",
        "## Import Graph",
        "## Call Graph",
        "## Notes",
    )

    assert ai_exporter.AI_EXPORT_SECTION_ORDER == (
        "project",
        "architecture_summary",
        "important_files",
        "symbol_index",
        "import_graph",
        "call_graph",
        "notes",
    )
    assert ai_exporter.iter_ai_export_headings() == expected
    assert tuple(
        ai_exporter.AI_EXPORT_SECTION_HEADINGS[section_name]
        for section_name in ai_exporter.AI_EXPORT_SECTION_ORDER
    ) == expected[1:]


def test_docs_markdown_heading_order_contract() -> None:
    expected = (
        "# Documentation Context",
        "## Documentation Quick Start",
        "## Documentation Summary",
        "## Documentation Files",
        "## Extracted Documents",
        "## Warnings",
    )

    assert docs_exporter.DOCS_EXPORT_SECTION_ORDER == (
        "documentation_quick_start",
        "documentation_summary",
        "documentation_files",
        "extracted_documents",
        "warnings",
    )
    assert docs_exporter.iter_docs_export_headings() == expected
    assert tuple(
        docs_exporter.DOCS_EXPORT_SECTION_HEADINGS[section_name]
        for section_name in docs_exporter.DOCS_EXPORT_SECTION_ORDER
    ) == expected[1:]


def test_changed_markdown_heading_order_contract() -> None:
    expected = (
        "# Changed Export",
        "# Changed Files Summary",
        "# Changed Files",
        "# Git Diff",
        "# Changed File Contents",
        "# Deleted Files",
        "# Binary / Skipped Files",
    )

    assert changed_exporter.CHANGED_EXPORT_SECTION_ORDER == (
        "changed_files_summary",
        "changed_files",
        "git_diff",
        "changed_file_contents",
        "deleted_files",
        "binary_or_skipped_files",
    )
    assert changed_exporter.iter_changed_export_headings() == expected
    assert tuple(
        changed_exporter.CHANGED_EXPORT_SECTION_HEADINGS[section_name]
        for section_name in changed_exporter.CHANGED_EXPORT_SECTION_ORDER
    ) == expected[1:]


def test_changed_rendered_markdown_uses_heading_contract(tmp_path) -> None:
    rendered = changed_exporter.render_changed_export(
        tmp_path,
        scans=(),
        include_diff=True,
    )

    assert _top_level_headings(rendered) == changed_exporter.iter_changed_export_headings()
