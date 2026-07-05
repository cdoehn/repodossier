"""Changed-mode Markdown rendering from RepositoryExport."""

from __future__ import annotations

from repodossier.export_model import (
    ExportSummary,
    FileEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.renderers import MarkdownRenderer, render_changed_markdown
from repodossier.renderers.markdown import iter_changed_markdown_renderer_headings


def _changed_export() -> RepositoryExport:
    return RepositoryExport(
        mode="changed",
        repository=RepositoryMetadata(
            root_path="/tmp/repo",
            root_name="repo",
            git_branch="feature/docs",
            git_commit="abc123",
            git_dirty=True,
        ),
        summary=ExportSummary(
            total_tracked_files=4,
            scanned_files=4,
            exported_text_files=2,
            total_lines=9,
            estimated_tokens=40,
            language_statistics=LanguageStatistics({"python": 1, "markdown": 1}),
        ),
        files=(
            FileEntry(
                path="README.md",
                language="markdown",
                content="# Demo\n\nUpdated docs.\n",
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
                path="old.txt",
                language="text",
                status="deleted",
                reason="deleted in compare target",
            ),
            FileEntry(
                path="assets/logo.png",
                language="unknown",
                text_status="binary",
                status="skipped",
                reason="binary file",
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
        if line.startswith("# ") and not line.startswith("## "):
            headings.append(line)

    return tuple(headings)


def test_changed_mode_renderer_uses_changed_heading_order() -> None:
    rendered = MarkdownRenderer().render_changed(_changed_export())

    assert _headings(rendered) == iter_changed_markdown_renderer_headings()


def test_changed_mode_renderer_renders_header_and_summary() -> None:
    rendered = render_changed_markdown(_changed_export())

    assert rendered.startswith("# Changed Export")
    assert "Repository path: /tmp/repo" in rendered
    assert "Compare mode: model" in rendered
    assert "Git branch: feature/docs" in rendered
    assert "Git dirty: True" in rendered
    assert "# Changed Files Summary" in rendered
    assert "Changed text files: 2" in rendered
    assert "Deleted files: 1" in rendered
    assert "Binary / skipped files: 1" in rendered
    assert "Estimated tokens: 40" in rendered


def test_changed_mode_renderer_renders_changed_files_and_contents() -> None:
    rendered = render_changed_markdown(_changed_export())
    fence = "`" * 3

    assert "# Changed Files" in rendered
    assert "- README.md (markdown, 3 lines, 22 bytes, included)" in rendered
    assert "- src/app.py (python, 2 lines, 24 bytes, included)" in rendered
    assert "# Changed File Contents" in rendered
    assert "## File: README.md" in rendered
    assert f"{fence}markdown" in rendered
    assert "# Demo" in rendered
    assert "## File: src/app.py" in rendered
    assert f"{fence}python" in rendered
    assert "def main():" in rendered


def test_changed_mode_renderer_renders_deleted_and_skipped_files() -> None:
    rendered = render_changed_markdown(_changed_export())

    assert "# Deleted Files" in rendered
    assert "- old.txt (deleted) - deleted in compare target" in rendered
    assert "# Binary / Skipped Files" in rendered
    assert "- assets/logo.png (skipped, binary) - binary file" in rendered


def test_changed_mode_renderer_keeps_empty_git_diff_explicit() -> None:
    rendered = render_changed_markdown(_changed_export())

    assert "# Git Diff\n\nNo git diff available in export model." in rendered
