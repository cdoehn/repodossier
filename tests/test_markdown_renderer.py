from repodossier.export_model import (
    ExportConfigurationSummary,
    ExportSummary,
    ExportWarning,
    FileEntry,
    FileTreeEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.renderers import MarkdownRenderer, render_markdown


def make_export(**overrides):
    values = {
        "mode": "full",
        "repository": RepositoryMetadata(
            root_path="/tmp/repo",
            root_name="repo",
            git_branch="main",
            git_commit="abc123",
            git_dirty=False,
        ),
    }
    values.update(overrides)
    return RepositoryExport(**values)


def test_markdown_renderer_renders_minimal_repository_export():
    rendered = MarkdownRenderer().render(make_export())

    assert rendered.startswith("# RepoDossier Export (full)")
    assert "## Repository" in rendered
    assert "- Root name: repo" in rendered
    assert "- Git branch: main" in rendered
    assert "- Git dirty: False" in rendered


def test_markdown_renderer_renders_summary_and_configuration():
    export = make_export(
        configuration=ExportConfigurationSummary(
            config_active=True,
            config_path="repodossier.yml",
            include_paths=("src",),
            exclude_globs=("*.bin",),
            limits={"max_file_bytes": 1000},
            split_settings={"enabled": False},
        ),
        summary=ExportSummary(
            total_tracked_files=3,
            scanned_files=2,
            exported_text_files=1,
            skipped_binary_files=1,
            total_lines=10,
            estimated_tokens=42,
            file_type_statistics={".py": 1, ".md": 2},
            language_statistics=LanguageStatistics({"python": 1, "markdown": 2}),
        ),
    )

    rendered = render_markdown(export)

    assert "- Config active: True" in rendered
    assert "- Config path: repodossier.yml" in rendered
    assert "  - src" in rendered
    assert "  - *.bin" in rendered
    assert "  - max_file_bytes: 1000" in rendered
    assert "## Language Statistics" in rendered
    assert "- markdown: 2" in rendered
    assert "- python: 1" in rendered


def test_markdown_renderer_renders_tree_file_summary_and_sources():
    export = make_export(
        tree=(
            FileTreeEntry(
                path="src",
                entry_type="directory",
                children=(FileTreeEntry(path="src/app.py", entry_type="file"),),
            ),
        ),
        files=(
            FileEntry(
                path="src/app.py",
                language="python",
                size_bytes=18,
                line_count=2,
                content="def main():\n    pass\n",
            ),
            FileEntry(
                path="README.md",
                language="markdown",
                status="skipped",
                reason="docs mode excluded",
            ),
        ),
    )

    rendered = render_markdown(export)

    assert "## Repository Tree" in rendered
    assert "- src/" in rendered
    assert "  - src/app.py" in rendered
    assert "README.md (markdown, 0 lines, 0 bytes, skipped) - docs mode excluded" in rendered
    assert "## Source Export" in rendered
    assert "### src/app.py" in rendered
    assert ("`" * 3) + "python" in rendered
    assert "def main():" in rendered


def test_markdown_renderer_uses_masked_content():
    export = make_export(
        files=(
            FileEntry(
                path=".env",
                language="text",
                content="TOKEN=secret",
                masked_content="TOKEN=***",
            ),
        ),
    )

    rendered = render_markdown(export)

    assert "TOKEN=***" in rendered
    assert "TOKEN=secret" not in rendered


def test_markdown_renderer_renders_warnings():
    export = make_export(
        warnings=(
            ExportWarning(
                path="large.log",
                message="file was truncated",
                code="truncated",
            ),
        ),
    )

    rendered = render_markdown(export)

    assert "## Warnings" in rendered
    assert "- large.log: file was truncated [truncated]" in rendered
