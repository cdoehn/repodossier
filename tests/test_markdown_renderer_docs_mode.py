"""Docs-mode Markdown rendering from RepositoryExport."""

from __future__ import annotations

from repodossier.export_model import (
    ExportSummary,
    ExportWarning,
    FileEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.renderers import MarkdownRenderer, render_docs_markdown
from repodossier.renderers.markdown import iter_docs_markdown_renderer_headings


def _docs_export() -> RepositoryExport:
    return RepositoryExport(
        mode="docs",
        repository=RepositoryMetadata(
            root_path="/tmp/repo",
            root_name="repo",
            git_branch="main",
        ),
        summary=ExportSummary(
            total_tracked_files=5,
            scanned_files=5,
            exported_text_files=3,
            total_lines=25,
            estimated_tokens=120,
            language_statistics=LanguageStatistics({"markdown": 2, "python": 1}),
        ),
        files=(
            FileEntry(
                path="README.md",
                language="markdown",
                content="# Demo\n\nWelcome.\n",
                size_bytes=16,
                line_count=3,
                estimated_tokens=5,
            ),
            FileEntry(
                path="docs/usage.md",
                language="markdown",
                content="# Usage\n\nRun the CLI.\n",
                size_bytes=22,
                line_count=3,
                estimated_tokens=6,
            ),
            FileEntry(
                path="src/app.py",
                language="python",
                content="def main():\n    return 0\n",
                size_bytes=24,
                line_count=2,
                estimated_tokens=6,
            ),
        ),
        omitted_files=(
            FileEntry(
                path="docs/large.md",
                language="markdown",
                status="skipped",
                reason="too large",
            ),
        ),
        warnings=(
            ExportWarning(
                path="docs/large.md",
                message="documentation file skipped",
                code="skipped",
            ),
            ExportWarning(
                path="src/app.py",
                message="source warning ignored by docs renderer",
                code="source",
            ),
        ),
    )


def _headings(markdown_text: str) -> tuple[str, ...]:
    headings: list[str] = []
    in_fence = False

    for line in markdown_text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("# ") or line.startswith("## "):
            headings.append(line)

    return tuple(headings)


def test_docs_mode_renderer_uses_docs_heading_order() -> None:
    rendered = MarkdownRenderer().render_docs(_docs_export())

    assert _headings(rendered) == iter_docs_markdown_renderer_headings()


def test_docs_mode_renderer_renders_quick_start_and_summary() -> None:
    rendered = render_docs_markdown(_docs_export())

    assert rendered.startswith("# Documentation Context")
    assert "## Documentation Quick Start" in rendered
    assert "Repository: repo" in rendered
    assert "Documentation files: 2" in rendered
    assert "Start with: README.md" in rendered
    assert "## Documentation Summary" in rendered
    assert "Tracked files: 5" in rendered
    assert "Documentation files included: 2" in rendered
    assert "Documentation files omitted: 1" in rendered
    assert "Documentation lines: 6" in rendered


def test_docs_mode_renderer_renders_documentation_files_and_content() -> None:
    rendered = render_docs_markdown(_docs_export())
    fence = "`" * 3

    assert "## Documentation Files" in rendered
    assert "Included:" in rendered
    assert "- README.md (markdown, 3 lines, 16 bytes, included)" in rendered
    assert "- docs/usage.md (markdown, 3 lines, 22 bytes, included)" in rendered
    assert "Omitted:" in rendered
    assert "- docs/large.md (skipped) - too large" in rendered
    assert "## Extracted Documents" in rendered
    assert "### README.md" in rendered
    assert f"{fence}markdown" in rendered
    assert "# Demo" in rendered
    assert "### docs/usage.md" in rendered
    assert "# Usage" in rendered
    assert "src/app.py" not in rendered


def test_docs_mode_renderer_renders_only_documentation_warnings() -> None:
    rendered = render_docs_markdown(_docs_export())

    assert "## Warnings" in rendered
    assert "- docs/large.md: documentation file skipped [skipped]" in rendered
    assert "source warning ignored by docs renderer" not in rendered
