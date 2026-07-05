"""Mode dispatch for MarkdownRenderer."""

from __future__ import annotations

import inspect

import pytest

from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.renderers import (
    MarkdownRenderer,
    describe_markdown_renderer_status,
    render_markdown,
    render_mode_markdown,
)
from repodossier.renderers.markdown import MARKDOWN_RENDERER_MODE_DISPATCH


def _export(mode: str) -> RepositoryExport:
    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(root_path="/tmp/repo", root_name="repo"),
    )


@pytest.mark.parametrize(
    ("mode", "expected_prefix"),
    (
        ("full", "# AI Quick Start"),
        ("ai", "# AI CONTEXT"),
        ("docs", "# Documentation Context"),
        ("changed", "# Changed Export"),
    ),
)
def test_render_mode_dispatches_to_mode_specific_renderer(
    mode: str,
    expected_prefix: str,
) -> None:
    rendered = MarkdownRenderer().render_mode(_export(mode))

    assert rendered.startswith(expected_prefix)


@pytest.mark.parametrize(
    ("mode", "expected_prefix"),
    (
        ("full", "# AI Quick Start"),
        ("ai", "# AI CONTEXT"),
        ("docs", "# Documentation Context"),
        ("changed", "# Changed Export"),
    ),
)
def test_render_mode_markdown_module_helper_dispatches_by_mode(
    mode: str,
    expected_prefix: str,
) -> None:
    rendered = render_mode_markdown(_export(mode))

    assert rendered.startswith(expected_prefix)


def test_render_mode_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported RepositoryExport mode 'xml'"):
        MarkdownRenderer().render_mode(_export("xml"))


def test_render_markdown_default_stays_generic_for_migration_safety() -> None:
    rendered = render_markdown(_export("full"))

    assert rendered.startswith("# RepoDossier Export (full)")
    assert not rendered.startswith("# AI Quick Start")


def test_renderer_status_exposes_mode_dispatch_table() -> None:
    status = describe_markdown_renderer_status()

    assert status["mode_dispatch"] == MARKDOWN_RENDERER_MODE_DISPATCH
    assert status["mode_dispatch"] == {
        "full": "render_full",
        "ai": "render_ai",
        "docs": "render_docs",
        "changed": "render_changed",
    }


def test_render_mode_does_not_collect_or_analyze_data() -> None:
    source = inspect.getsource(MarkdownRenderer.render_mode)

    forbidden_terms = (
        "RepositoryScanner",
        "list_tracked_files",
        "discover_repository",
        "analyze_dependencies",
        "analyze_database_schemas",
        "build_symbol_index",
        "build_import_graph",
        "build_call_graph",
        "collect_changed_file_scans",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source
