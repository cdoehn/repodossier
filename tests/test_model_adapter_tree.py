"""File-tree adapter helpers for RepositoryExport models."""

from __future__ import annotations

from repodossier.export_model import FileEntry
from repodossier.exporters.model_adapter import (
    build_file_tree_from_entries,
    build_repository_export_from_entries,
    file_entry_from_mapping,
)


def _flatten_tree_paths(entries) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []

    def visit(nodes) -> None:
        for node in nodes:
            result.append((node.path, node.entry_type))
            visit(node.children)

    visit(entries)
    return tuple(result)


def test_build_file_tree_from_entries_creates_sorted_directories_and_files() -> None:
    tree = build_file_tree_from_entries(
        (
            FileEntry(path="src/repodossier/cli.py", language="python"),
            FileEntry(path="README.md", language="markdown"),
            FileEntry(path="src/repodossier/exporters/full.py", language="python"),
            FileEntry(path="pyproject.toml", language="toml"),
            FileEntry(path="tests/test_cli.py", language="python"),
        )
    )

    assert _flatten_tree_paths(tree) == (
        ("README.md", "file"),
        ("pyproject.toml", "file"),
        ("src", "directory"),
        ("src/repodossier", "directory"),
        ("src/repodossier/cli.py", "file"),
        ("src/repodossier/exporters", "directory"),
        ("src/repodossier/exporters/full.py", "file"),
        ("tests", "directory"),
        ("tests/test_cli.py", "file"),
    )


def test_build_file_tree_from_entries_ignores_empty_paths() -> None:
    tree = build_file_tree_from_entries(
        (
            FileEntry(path="", language="unknown"),
            FileEntry(path=".", language="unknown"),
            FileEntry(path="README.md", language="markdown"),
        )
    )

    assert _flatten_tree_paths(tree) == (("README.md", "file"),)


def test_build_repository_export_from_entries_populates_tree() -> None:
    export = build_repository_export_from_entries(
        mode="full",
        root_path="/tmp/repo",
        files=(
            file_entry_from_mapping(
                {
                    "path": "src/app.py",
                    "language": "python",
                    "content": "print('hi')\n",
                }
            ),
            file_entry_from_mapping(
                {
                    "path": "README.md",
                    "language": "markdown",
                    "content": "# Demo\n",
                }
            ),
        ),
        omitted_files=(
            file_entry_from_mapping(
                {
                    "path": "assets/logo.png",
                    "language": "unknown",
                    "text_status": "binary",
                    "status": "skipped",
                    "reason": "binary file",
                }
            ),
        ),
    )

    assert _flatten_tree_paths(export.tree) == (
        ("README.md", "file"),
        ("assets", "directory"),
        ("assets/logo.png", "file"),
        ("src", "directory"),
        ("src/app.py", "file"),
    )


def test_model_adapter_tree_feeds_full_markdown_renderer() -> None:
    from repodossier.exporters.model_markdown import render_markdown_export_from_model

    export = build_repository_export_from_entries(
        mode="full",
        root_path="/tmp/repo",
        files=(
            file_entry_from_mapping(
                {
                    "path": "src/app.py",
                    "language": "python",
                    "content": "print('hi')\n",
                    "line_count": 1,
                    "estimated_tokens": 3,
                }
            ),
        ),
    )

    rendered = render_markdown_export_from_model(export)

    assert "# Repository Tree" in rendered
    assert "- src/" in rendered
    assert "  - src/app.py" in rendered
