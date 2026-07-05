"""Central model-only Markdown exporter helpers."""

from __future__ import annotations

import inspect
import io
from pathlib import Path

import pytest

from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.exporters.model_markdown import (
    render_markdown_export_from_model,
    write_markdown_export_from_model,
    write_markdown_export_model_to_stream,
)


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
def test_render_markdown_export_from_model_dispatches_by_mode(
    mode: str,
    expected_prefix: str,
) -> None:
    rendered = render_markdown_export_from_model(_export(mode))

    assert rendered.startswith(expected_prefix)


def test_write_markdown_export_from_model_writes_file(tmp_path: Path) -> None:
    output_path = tmp_path / "ai.txt"

    write_markdown_export_from_model(_export("ai"), output_path)

    assert output_path.read_text(encoding="utf-8").startswith("# AI CONTEXT")


def test_write_markdown_export_model_to_stream_writes_text() -> None:
    stream = io.StringIO()

    write_markdown_export_model_to_stream(_export("docs"), stream)

    assert stream.getvalue().startswith("# Documentation Context")


def test_model_markdown_helpers_validate_unknown_mode(tmp_path: Path) -> None:
    output_path = tmp_path / "unknown.txt"

    with pytest.raises(ValueError, match="Unsupported RepositoryExport mode 'xml'"):
        write_markdown_export_from_model(_export("xml"), output_path)

    assert not output_path.exists()


@pytest.mark.parametrize(
    "helper_name",
    (
        "render_markdown_export_from_model",
        "write_markdown_export_from_model",
        "write_markdown_export_model_to_stream",
    ),
)
def test_model_markdown_helpers_do_not_collect_or_analyze_data(helper_name: str) -> None:
    import repodossier.exporters.model_markdown as model_markdown

    source = inspect.getsource(getattr(model_markdown, helper_name))

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
        "render_full_export",
        "render_ai_export",
        "render_docs_export",
        "render_changed_export",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source
