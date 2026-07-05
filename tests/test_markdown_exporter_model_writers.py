"""Writer bridges for model-rendered Markdown exports."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Callable

import pytest

from repodossier.changed_exporter import write_changed_export_from_model
from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.exporters.ai import write_ai_export_from_model
from repodossier.exporters.docs import write_docs_export_from_model
from repodossier.exporters.full import write_full_export_from_model


def _export(mode: str) -> RepositoryExport:
    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(root_path="/tmp/repo", root_name="repo"),
    )


@pytest.mark.parametrize(
    ("mode", "writer", "expected_prefix"),
    (
        ("full", write_full_export_from_model, "# AI Quick Start"),
        ("ai", write_ai_export_from_model, "# AI CONTEXT"),
        ("docs", write_docs_export_from_model, "# Documentation Context"),
        ("changed", write_changed_export_from_model, "# Changed Export"),
    ),
)
def test_model_writer_bridges_write_mode_specific_markdown(
    tmp_path: Path,
    mode: str,
    writer: Callable[[RepositoryExport, Path], None],
    expected_prefix: str,
) -> None:
    output_path = tmp_path / f"{mode}.txt"

    writer(_export(mode), output_path)

    assert output_path.read_text(encoding="utf-8").startswith(expected_prefix)


@pytest.mark.parametrize(
    ("writer", "wrong_mode", "expected_mode"),
    (
        (write_full_export_from_model, "ai", "full"),
        (write_ai_export_from_model, "full", "ai"),
        (write_docs_export_from_model, "full", "docs"),
        (write_changed_export_from_model, "full", "changed"),
    ),
)
def test_model_writer_bridges_validate_model_mode(
    tmp_path: Path,
    writer: Callable[[RepositoryExport, Path], None],
    wrong_mode: str,
    expected_mode: str,
) -> None:
    output_path = tmp_path / "out.txt"

    with pytest.raises(ValueError, match=f"mode {expected_mode!r}"):
        writer(_export(wrong_mode), output_path)

    assert not output_path.exists()


@pytest.mark.parametrize(
    "writer",
    (
        write_full_export_from_model,
        write_ai_export_from_model,
        write_docs_export_from_model,
        write_changed_export_from_model,
    ),
)
def test_model_writer_bridges_do_not_collect_or_analyze_data(writer) -> None:
    source = inspect.getsource(writer)

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


def test_model_writer_bridges_overwrite_existing_file(tmp_path: Path) -> None:
    output_path = tmp_path / "full.txt"
    output_path.write_text("old content", encoding="utf-8")

    write_full_export_from_model(_export("full"), output_path)

    assert output_path.read_text(encoding="utf-8").startswith("# AI Quick Start")
