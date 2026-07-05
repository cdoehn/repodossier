"""Current MarkdownRenderer inventory for Milestone 4 step 4.1.c."""

from __future__ import annotations

from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.renderers import MarkdownRenderer, describe_markdown_renderer_status
from repodossier.renderers.markdown import (
    MARKDOWN_RENDERER_LEGACY_GAPS,
    MARKDOWN_RENDERER_MIGRATION_DECISION,
    MARKDOWN_RENDERER_REUSABLE_SECTIONS,
)


def _minimal_export(mode: str = "full") -> RepositoryExport:
    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(root_path="/tmp/repo", root_name="repo"),
    )


def test_markdown_renderer_status_documents_reusable_sections() -> None:
    status = describe_markdown_renderer_status()

    assert status["reusable_sections"] == MARKDOWN_RENDERER_REUSABLE_SECTIONS
    assert {
        "repository",
        "summary",
        "configuration",
        "repository_tree",
        "file_summary",
        "source_export",
        "warnings",
    }.issubset(set(status["reusable_sections"]))


def test_markdown_renderer_status_documents_legacy_gaps() -> None:
    status = describe_markdown_renderer_status()

    assert status["legacy_gaps"] == MARKDOWN_RENDERER_LEGACY_GAPS
    assert {
        "full_legacy_heading_order",
        "ai_legacy_heading_order",
        "docs_legacy_heading_order",
        "changed_legacy_heading_order",
        "dependencies_report_rendering",
        "database_schema_report_rendering",
        "secret_detection_report_rendering",
        "symbol_index_report_rendering",
        "import_graph_report_rendering",
        "call_graph_report_rendering",
        "changed_diff_rendering",
    }.issubset(set(status["legacy_gaps"]))


def test_markdown_renderer_status_records_mode_aware_migration_decision() -> None:
    status = describe_markdown_renderer_status()

    assert status["mode_methods"] == (
        "render_full",
        "render_ai",
        "render_docs",
        "render_changed",
    )
    assert status["decision"] == MARKDOWN_RENDERER_MIGRATION_DECISION
    assert "generic RepositoryExport" in status["decision"]
    assert "mode-aware" in status["decision"]
    assert "render_full" in status["decision"]
    assert "render_ai" in status["decision"]
    assert "render_docs" in status["decision"]
    assert "render_changed" in status["decision"]


def test_current_markdown_renderer_is_still_generic_not_legacy_full() -> None:
    rendered = MarkdownRenderer().render(_minimal_export("full"))

    assert rendered.startswith("# RepoDossier Export (full)")
    assert "# AI Quick Start" not in rendered
    assert "# Repository Statistics" not in rendered
    assert "# Complete Source Export" not in rendered


def test_current_markdown_renderer_is_still_generic_for_non_full_modes() -> None:
    for mode in ("ai", "docs", "changed"):
        rendered = MarkdownRenderer().render(_minimal_export(mode))

        assert rendered.startswith(f"# RepoDossier Export ({mode})")
        assert "# AI CONTEXT" not in rendered
        assert "# Documentation Quick Start" not in rendered
        assert "# Changed Export" not in rendered
