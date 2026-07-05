"""Legacy exporter bridge functions for model-rendered Markdown."""

from __future__ import annotations

import inspect

import pytest

from repodossier.changed_exporter import render_changed_export_from_model
from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.exporters.ai import render_ai_export_from_model
from repodossier.exporters.docs import render_docs_export_from_model
from repodossier.exporters.full import render_full_export_from_model


def _export(mode: str) -> RepositoryExport:
    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(root_path="/tmp/repo", root_name="repo"),
    )


@pytest.mark.parametrize(
    ("mode", "renderer", "expected_prefix"),
    (
        ("full", render_full_export_from_model, "# AI Quick Start"),
        ("ai", render_ai_export_from_model, "# AI CONTEXT"),
        ("docs", render_docs_export_from_model, "# Documentation Context"),
        ("changed", render_changed_export_from_model, "# Changed Export"),
    ),
)
def test_exporter_model_bridges_render_mode_specific_markdown(
    mode: str,
    renderer,
    expected_prefix: str,
) -> None:
    rendered = renderer(_export(mode))

    assert rendered.startswith(expected_prefix)


@pytest.mark.parametrize(
    ("renderer", "wrong_mode", "expected_mode"),
    (
        (render_full_export_from_model, "ai", "full"),
        (render_ai_export_from_model, "full", "ai"),
        (render_docs_export_from_model, "full", "docs"),
        (render_changed_export_from_model, "full", "changed"),
    ),
)
def test_exporter_model_bridges_validate_model_mode(
    renderer,
    wrong_mode: str,
    expected_mode: str,
) -> None:
    with pytest.raises(ValueError, match=f"mode {expected_mode!r}"):
        renderer(_export(wrong_mode))


@pytest.mark.parametrize(
    "renderer",
    (
        render_full_export_from_model,
        render_ai_export_from_model,
        render_docs_export_from_model,
        render_changed_export_from_model,
    ),
)
def test_exporter_model_bridges_do_not_collect_or_analyze_data(renderer) -> None:
    source = inspect.getsource(renderer)

    forbidden_terms = (
        "RepositoryScanner",
        "list_tracked_files",
        "discover_repository",
        "analyze_dependencies",
        "analyze_database_schemas",
        "build_symbol_index",
        "build_import_graph",
        "build_call_graph",
        "create_full_export_context",
        "build_full_export_context",
        "collect_changed_file_scans",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source


def test_legacy_exporter_entrypoints_still_exist() -> None:
    import repodossier.changed_exporter as changed_exporter
    import repodossier.exporters.ai as ai_exporter
    import repodossier.exporters.docs as docs_exporter
    import repodossier.exporters.full as full_exporter

    assert callable(full_exporter.render_full_export)
    assert callable(ai_exporter.render_ai_export)
    assert callable(docs_exporter.render_docs_export)
    assert callable(changed_exporter.render_changed_export)
