"""Mode-aware Markdown renderer entrypoints for Milestone 4."""

from __future__ import annotations

import pytest

from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.renderers import (
    MarkdownRenderer,
    describe_markdown_renderer_status,
    render_ai_markdown,
    render_changed_markdown,
    render_docs_markdown,
    render_full_markdown,
)
from repodossier.renderers.markdown import MARKDOWN_RENDERER_MODE_METHODS


def _export(mode: str) -> RepositoryExport:
    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(root_path="/tmp/repo", root_name="repo"),
    )


def test_markdown_renderer_exposes_mode_specific_methods() -> None:
    renderer = MarkdownRenderer()

    for method_name in MARKDOWN_RENDERER_MODE_METHODS:
        assert hasattr(renderer, method_name)
        assert callable(getattr(renderer, method_name))


@pytest.mark.parametrize(
    ("mode", "method_name"),
    (
        ("full", "render_full"),
        ("ai", "render_ai"),
        ("docs", "render_docs"),
        ("changed", "render_changed"),
    ),
)
def test_mode_specific_methods_validate_and_render_expected_mode(
    mode: str,
    method_name: str,
) -> None:
    rendered = getattr(MarkdownRenderer(), method_name)(_export(mode))

    assert rendered.startswith(f"# RepoDossier Export ({mode})")


@pytest.mark.parametrize(
    ("method_name", "expected_mode"),
    (
        ("render_full", "full"),
        ("render_ai", "ai"),
        ("render_docs", "docs"),
        ("render_changed", "changed"),
    ),
)
def test_mode_specific_methods_reject_wrong_mode(
    method_name: str,
    expected_mode: str,
) -> None:
    with pytest.raises(ValueError, match=f"mode '{expected_mode}'"):
        getattr(MarkdownRenderer(), method_name)(_export("full" if expected_mode != "full" else "ai"))


def test_module_level_mode_helpers_delegate_to_renderer() -> None:
    assert render_full_markdown(_export("full")).startswith("# RepoDossier Export (full)")
    assert render_ai_markdown(_export("ai")).startswith("# RepoDossier Export (ai)")
    assert render_docs_markdown(_export("docs")).startswith("# RepoDossier Export (docs)")
    assert render_changed_markdown(_export("changed")).startswith(
        "# RepoDossier Export (changed)"
    )


def test_markdown_renderer_status_lists_mode_methods() -> None:
    status = describe_markdown_renderer_status()

    assert status["mode_methods"] == MARKDOWN_RENDERER_MODE_METHODS
    assert status["mode_methods"] == (
        "render_full",
        "render_ai",
        "render_docs",
        "render_changed",
    )
