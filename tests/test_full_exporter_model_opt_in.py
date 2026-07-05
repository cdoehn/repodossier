"""Opt-in model renderer selector for the legacy full exporter."""

from __future__ import annotations

import pytest

from repodossier.export_model import FileEntry
from repodossier.exporters.full import render_full_export_with_optional_model
from repodossier.exporters.model_adapter import build_repository_export_from_entries


def _full_export():
    return build_repository_export_from_entries(
        mode="full",
        root_path="/tmp/repo",
        files=(
            FileEntry(
                path="src/app.py",
                language="python",
                content="print('hi')\n",
                line_count=1,
                estimated_tokens=3,
            ),
        ),
    )


def test_full_export_optional_model_selector_keeps_legacy_default() -> None:
    rendered = render_full_export_with_optional_model(
        "legacy-context",
        legacy_renderer=lambda context: f"legacy:{context}",
    )

    assert rendered == "legacy:legacy-context"


def test_full_export_optional_model_selector_accepts_explicit_legacy_mode() -> None:
    rendered = render_full_export_with_optional_model(
        {"legacy": True},
        use_model_renderer=False,
        legacy_renderer=lambda context: "legacy-ok" if context["legacy"] else "bad",
    )

    assert rendered == "legacy-ok"


def test_full_export_optional_model_selector_requires_legacy_callable() -> None:
    with pytest.raises(TypeError, match="legacy_renderer must be callable"):
        render_full_export_with_optional_model("legacy-context")


def test_full_export_optional_model_selector_renders_repository_export_when_opted_in() -> None:
    rendered = render_full_export_with_optional_model(
        _full_export(),
        use_model_renderer=True,
    )

    assert rendered.startswith("# AI Quick Start")
    assert "# Repository Statistics" in rendered
    assert "# Complete Source Export" in rendered
    assert "src/app.py" in rendered


def test_full_export_optional_model_selector_rejects_non_model_opt_in() -> None:
    with pytest.raises(TypeError, match="RepositoryExport"):
        render_full_export_with_optional_model(
            {"not": "repository-export"},
            use_model_renderer=True,
        )
