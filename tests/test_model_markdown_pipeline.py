"""End-to-end model Markdown pipeline regression tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from repodossier.export_model import (
    CallGraphReport,
    DatabaseSchemaReport,
    DependencyReport,
    ExportWarning,
    FileEntry,
    ImportGraphReport,
    SymbolIndex,
)
from repodossier.exporters.model_adapter import build_repository_export_from_entries
from repodossier.exporters.model_markdown import (
    render_markdown_export_from_model,
    write_markdown_export_from_model,
    write_markdown_export_model_to_stream,
)


def _file_entries() -> tuple[FileEntry, ...]:
    return (
        FileEntry(
            path="README.md",
            language="markdown",
            content="# Demo\n\nWelcome.\n",
            size_bytes=18,
            line_count=3,
            estimated_tokens=5,
        ),
        FileEntry(
            path="docs/usage.md",
            language="markdown",
            content="# Usage\n\nRun the CLI.\n",
            size_bytes=24,
            line_count=3,
            estimated_tokens=6,
        ),
        FileEntry(
            path="src/repodossier/cli.py",
            language="python",
            content="def main():\n    return 0\n",
            size_bytes=26,
            line_count=2,
            estimated_tokens=7,
        ),
    )


def _export(mode: str):
    return build_repository_export_from_entries(
        mode=mode,
        root_path="/tmp/repo",
        files=_file_entries(),
        omitted_files=(
            FileEntry(
                path="assets/logo.png",
                language="unknown",
                text_status="binary",
                status="skipped",
                reason="binary file",
            ),
        ),
        warnings=(
            ExportWarning(
                path="assets/logo.png",
                message="binary file skipped",
                code="binary",
            ),
        ),
        git_branch="main",
        git_commit="abc123",
        git_dirty=False,
        config_active=True,
        config_path="repodossier.yml",
        include_paths=("src", "docs"),
        include_globs=("*.py", "*.md"),
        exclude_paths=("build",),
        exclude_globs=("*.log",),
        limits={"max_total_files": 100},
        split_settings={"enabled": True},
        dependencies=DependencyReport(
            items=({"name": "PyYAML", "type": "runtime"},),
        ),
        database_schema=DatabaseSchemaReport(
            items=({"source": "schema.sql", "tables": 2},),
        ),
        symbol_index=SymbolIndex(
            symbols=({"path": "src/repodossier/cli.py", "symbol": "main"},),
        ),
        import_graph=ImportGraphReport(
            edges=({"source": "cli", "target": "exporters"},),
        ),
        call_graph=CallGraphReport(
            edges=({"caller": "cli.main", "callee": "run"},),
        ),
    )


@pytest.mark.parametrize(
    ("mode", "expected_prefix", "expected_sections"),
    (
        (
            "full",
            "# AI Quick Start",
            (
                "# Repository Statistics",
                "# Repository Tree",
                "# Dependencies",
                "# Complete Source Export",
            ),
        ),
        (
            "ai",
            "# AI CONTEXT",
            (
                "## Project",
                "## Architecture Summary",
                "## Important Files",
                "## Dependencies",
                "## Symbol Index",
            ),
        ),
        (
            "docs",
            "# Documentation Context",
            (
                "## Documentation Quick Start",
                "## Documentation Files",
                "## Extracted Documents",
                "### README.md",
                "### docs/usage.md",
            ),
        ),
        (
            "changed",
            "# Changed Export",
            (
                "# Changed Files Summary",
                "# Changed Files",
                "# Changed File Contents",
                "# Binary / Skipped Files",
            ),
        ),
    ),
)
def test_model_markdown_pipeline_renders_expected_mode_sections(
    mode: str,
    expected_prefix: str,
    expected_sections: tuple[str, ...],
) -> None:
    rendered = render_markdown_export_from_model(_export(mode))

    assert rendered.startswith(expected_prefix)
    for section in expected_sections:
        assert section in rendered


@pytest.mark.parametrize(
    ("mode", "expected_prefix"),
    (
        ("full", "# AI Quick Start"),
        ("ai", "# AI CONTEXT"),
        ("docs", "# Documentation Context"),
        ("changed", "# Changed Export"),
    ),
)
def test_model_markdown_pipeline_writes_mode_specific_files(
    tmp_path: Path,
    mode: str,
    expected_prefix: str,
) -> None:
    output_path = tmp_path / f"{mode}.txt"

    write_markdown_export_from_model(_export(mode), output_path)

    rendered = output_path.read_text(encoding="utf-8")
    assert rendered.startswith(expected_prefix)


def test_model_markdown_pipeline_stream_writer_uses_same_dispatch() -> None:
    import io

    stream = io.StringIO()

    write_markdown_export_model_to_stream(_export("ai"), stream)

    assert stream.getvalue().startswith("# AI CONTEXT")
    assert "name: PyYAML" in stream.getvalue()
    assert "symbol: main" in stream.getvalue()


def test_model_markdown_pipeline_preserves_tree_reports_and_configuration() -> None:
    full_markdown = render_markdown_export_from_model(_export("full"))
    ai_markdown = render_markdown_export_from_model(_export("ai"))

    assert "- docs/" in full_markdown
    assert "  - docs/usage.md" in full_markdown
    assert "- src/" in full_markdown
    assert "  - src/repodossier/" in full_markdown
    assert "name: PyYAML" in full_markdown
    assert "tables: 2" in full_markdown

    assert "Top-level directories: assets, docs, src" in ai_markdown
    assert "name: PyYAML" in ai_markdown
    assert "symbol: main" in ai_markdown
    assert "target: exporters" in ai_markdown
    assert "callee: run" in ai_markdown


def test_model_markdown_pipeline_rejects_unsupported_mode_before_writing(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "xml.txt"

    with pytest.raises(ValueError, match="Unsupported RepositoryExport mode 'xml'"):
        write_markdown_export_from_model(_export("xml"), output_path)

    assert not output_path.exists()
