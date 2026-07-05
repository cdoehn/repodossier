"""Opt-in model renderer selectors for non-full exporters."""

from __future__ import annotations

import pytest

from repodossier.changed_exporter import render_changed_export_with_optional_model
from repodossier.export_model import FileEntry
from repodossier.exporters.ai import render_ai_export_with_optional_model
from repodossier.exporters.docs import render_docs_export_with_optional_model
from repodossier.exporters.model_adapter import build_repository_export_from_entries


def _export(mode: str):
    return build_repository_export_from_entries(
        mode=mode,
        root_path="/tmp/repo",
        files=(
            FileEntry(
                path="README.md",
                language="markdown",
                content="# Demo\n\nWelcome.\n",
                line_count=3,
                estimated_tokens=5,
            ),
            FileEntry(
                path="src/app.py",
                language="python",
                content="print('hi')\n",
                line_count=1,
                estimated_tokens=3,
            ),
        ),
    )


@pytest.mark.parametrize(
    ("selector", "context"),
    (
        (render_ai_export_with_optional_model, "ai-context"),
        (render_docs_export_with_optional_model, "docs-context"),
        (render_changed_export_with_optional_model, "changed-context"),
    ),
)
def test_exporter_model_opt_in_selectors_keep_legacy_default(
    selector,
    context: str,
) -> None:
    rendered = selector(
        context,
        legacy_renderer=lambda value: f"legacy:{value}",
    )

    assert rendered == f"legacy:{context}"


@pytest.mark.parametrize(
    "selector",
    (
        render_ai_export_with_optional_model,
        render_docs_export_with_optional_model,
        render_changed_export_with_optional_model,
    ),
)
def test_exporter_model_opt_in_selectors_require_legacy_callable(selector) -> None:
    with pytest.raises(TypeError, match="legacy_renderer must be callable"):
        selector("legacy-context")


@pytest.mark.parametrize(
    ("selector", "mode", "expected_prefix", "expected_section"),
    (
        (
            render_ai_export_with_optional_model,
            "ai",
            "# AI CONTEXT",
            "## Important Files",
        ),
        (
            render_docs_export_with_optional_model,
            "docs",
            "# Documentation Context",
            "## Documentation Files",
        ),
        (
            render_changed_export_with_optional_model,
            "changed",
            "# Changed Export",
            "# Changed Files Summary",
        ),
    ),
)
def test_exporter_model_opt_in_selectors_render_repository_export_when_opted_in(
    selector,
    mode: str,
    expected_prefix: str,
    expected_section: str,
) -> None:
    rendered = selector(
        _export(mode),
        use_model_renderer=True,
    )

    assert rendered.startswith(expected_prefix)
    assert expected_section in rendered


@pytest.mark.parametrize(
    "selector",
    (
        render_ai_export_with_optional_model,
        render_docs_export_with_optional_model,
        render_changed_export_with_optional_model,
    ),
)
def test_exporter_model_opt_in_selectors_reject_non_model_opt_in(selector) -> None:
    with pytest.raises(TypeError, match="RepositoryExport"):
        selector(
            {"not": "repository-export"},
            use_model_renderer=True,
        )
