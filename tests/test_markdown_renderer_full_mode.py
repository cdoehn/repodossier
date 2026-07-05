"""Full-mode Markdown rendering from RepositoryExport."""

from __future__ import annotations

from repodossier.export_model import (
    ExportSummary,
    FileEntry,
    FileTreeEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.renderers import MarkdownRenderer, render_full_markdown
from repodossier.renderers.markdown import iter_full_markdown_renderer_headings


def _full_export() -> RepositoryExport:
    files = (
        FileEntry(
            path="README.md",
            language="markdown",
            content="# Demo\n",
            line_count=1,
            estimated_tokens=2,
        ),
        FileEntry(
            path="src/app.py",
            language="python",
            content="def main():\n    return 0\n",
            line_count=2,
            estimated_tokens=6,
        ),
    )
    return RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(
            root_path="/tmp/repo",
            root_name="repo",
            git_branch="main",
            git_commit="abc123",
            git_dirty=False,
        ),
        summary=ExportSummary(
            total_tracked_files=2,
            scanned_files=2,
            exported_text_files=2,
            total_lines=3,
            estimated_tokens=8,
            file_type_statistics={".md": 1, ".py": 1},
            language_statistics=LanguageStatistics(
                {"markdown": 1, "python": 1}
            ),
        ),
        tree=(
            FileTreeEntry(path="README.md", entry_type="file"),
            FileTreeEntry(
                path="src",
                entry_type="directory",
                children=(FileTreeEntry(path="src/app.py", entry_type="file"),),
            ),
        ),
        files=files,
    )


def _top_level_headings(markdown_text: str) -> tuple[str, ...]:
    headings: list[str] = []
    in_fence = False

    for line in markdown_text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("# ") and not line.startswith("## "):
            headings.append(line)

    return tuple(headings)


def test_full_mode_renderer_uses_legacy_full_heading_order() -> None:
    rendered = MarkdownRenderer().render_full(_full_export())

    assert _top_level_headings(rendered) == iter_full_markdown_renderer_headings()


def test_full_mode_renderer_renders_model_summary_and_tree() -> None:
    rendered = render_full_markdown(_full_export())

    assert rendered.startswith("# AI Quick Start")
    assert "Repository: repo" in rendered
    assert "Git branch: main" in rendered
    assert "# Repository Statistics" in rendered
    assert "Total tracked files: 2" in rendered
    assert "File types:" in rendered
    assert "- .py: 1" in rendered
    assert "# Repository Tree" in rendered
    assert "- README.md" in rendered
    assert "- src/" in rendered
    assert "  - src/app.py" in rendered


def test_full_mode_renderer_renders_file_summary_and_source_export() -> None:
    rendered = render_full_markdown(_full_export())
    fence = "`" * 3

    assert "# File Summary" in rendered
    assert "## Markdown (1 file)" in rendered
    assert "- `README.md` — 1 lines, ~2 tokens" in rendered
    assert "## Python (1 file)" in rendered
    assert "- `src/app.py` — 2 lines, ~6 tokens" in rendered
    assert "# Complete Source Export" in rendered
    assert f"{fence}python" in rendered
    assert "def main():" in rendered
    assert f"{fence}markdown" in rendered


def test_full_mode_renderer_keeps_empty_report_sections_explicit() -> None:
    rendered = render_full_markdown(_full_export())

    assert "# Dependencies\n\nNo dependencies detected." in rendered
    assert "# Database Schema\n\nNo database schema files detected." in rendered
    assert "# Secret Detection\n\nNo secret findings reported." in rendered
    assert "# Warnings\n\nNo warnings." in rendered
    assert "# Import Graph\n\nNo import graph data available." in rendered
    assert "# Call Graph\n\nNo call graph data available." in rendered
