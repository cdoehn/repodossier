"""AI-mode Markdown rendering from RepositoryExport."""

from __future__ import annotations

from repodossier.export_model import (
    CallGraphReport,
    DatabaseSchemaReport,
    DependencyReport,
    ExportSummary,
    ExportWarning,
    FileEntry,
    ImportGraphReport,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
    SymbolIndex,
)
from repodossier.renderers import MarkdownRenderer, render_ai_markdown
from repodossier.renderers.markdown import iter_ai_markdown_renderer_headings


def _ai_export() -> RepositoryExport:
    return RepositoryExport(
        mode="ai",
        repository=RepositoryMetadata(
            root_path="/tmp/repo",
            root_name="repo",
            git_branch="main",
            git_commit="abc123",
        ),
        summary=ExportSummary(
            total_tracked_files=3,
            scanned_files=3,
            exported_text_files=2,
            total_lines=12,
            estimated_tokens=50,
            language_statistics=LanguageStatistics({"python": 1, "markdown": 1}),
        ),
        files=(
            FileEntry(
                path="README.md",
                language="markdown",
                content="# Demo\n",
                line_count=1,
                estimated_tokens=2,
            ),
            FileEntry(
                path="src/repodossier/cli.py",
                language="python",
                content="def main():\n    return 0\n",
                line_count=2,
                estimated_tokens=6,
            ),
        ),
        omitted_files=(
            FileEntry(
                path="build/generated.bin",
                language="unknown",
                text_status="binary",
                status="skipped",
                reason="binary file",
            ),
        ),
        warnings=(
            ExportWarning(
                path="build/generated.bin",
                message="binary file skipped",
                code="binary",
            ),
        ),
        dependencies=DependencyReport(
            items=({"name": "PyYAML", "type": "runtime"},),
        ),
        database_schema=DatabaseSchemaReport(
            items=({"tables": 0, "source": "none"},),
        ),
        symbol_index=SymbolIndex(
            symbols=({"path": "src/repodossier/cli.py", "symbol": "main"},),
        ),
        import_graph=ImportGraphReport(
            edges=({"source": "cli", "target": "exporters"},),
        ),
        call_graph=CallGraphReport(
            edges=({"caller": "cli.main", "callee": "generate_ai_export"},),
        ),
    )


def _headings(markdown_text: str) -> tuple[str, ...]:
    return tuple(
        line
        for line in markdown_text.splitlines()
        if line.startswith("# ") or line.startswith("## ")
    )


def test_ai_mode_renderer_uses_ai_heading_order() -> None:
    rendered = MarkdownRenderer().render_ai(_ai_export())

    assert _headings(rendered) == iter_ai_markdown_renderer_headings()


def test_ai_mode_renderer_renders_project_and_architecture_summary() -> None:
    rendered = render_ai_markdown(_ai_export())

    assert rendered.startswith("# AI CONTEXT")
    assert "## Project" in rendered
    assert "Repository: repo" in rendered
    assert "Tracked files: 3" in rendered
    assert "Primary language: markdown" in rendered
    assert "Git branch: main" in rendered
    assert "## Architecture Summary" in rendered
    assert "Top-level directories: build, src" in rendered
    assert "Root files: README.md" in rendered


def test_ai_mode_renderer_renders_important_files_and_reports() -> None:
    rendered = render_ai_markdown(_ai_export())

    assert "## Important Files" in rendered
    assert "- README.md" in rendered
    assert "Reason: primary documentation" in rendered
    assert "- src/repodossier/cli.py" in rendered
    assert "Reason: likely entry point" in rendered
    assert "## Dependencies" in rendered
    assert "name: PyYAML" in rendered
    assert "## Database Schema" in rendered
    assert "tables: 0" in rendered
    assert "## Symbol Index" in rendered
    assert "symbol: main" in rendered
    assert "## Import Graph" in rendered
    assert "target: exporters" in rendered
    assert "## Call Graph" in rendered
    assert "callee: generate_ai_export" in rendered


def test_ai_mode_renderer_renders_notes_from_model() -> None:
    rendered = render_ai_markdown(_ai_export())

    assert "## Notes" in rendered
    assert "- build/generated.bin: binary file skipped [binary]" in rendered
    assert "Omitted files:" in rendered
    assert "- build/generated.bin (skipped) - binary file" in rendered
