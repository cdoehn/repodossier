"""RepositoryExport adapter helpers."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path

from repodossier.export_model import FileEntry
from repodossier.exporters.model_adapter import (
    build_repository_export_from_entries,
    export_warning_from_mapping,
    export_warning_from_object,
    file_entries_from_objects,
    file_entry_from_mapping,
    file_entry_from_object,
)
from repodossier.exporters.model_markdown import render_markdown_export_from_model


@dataclass(frozen=True)
class LegacyScan:
    path: str
    language: str = "python"
    size_bytes: int = 12
    line_count: int = 2
    estimated_tokens: int = 4
    text_status: str = "text"
    status: str = "included"
    content: str | None = "print('hi')\n"
    masked_content: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class LegacyWarning:
    message: str
    path: str | None = None
    code: str | None = None


def test_file_entry_from_mapping_uses_safe_defaults() -> None:
    entry = file_entry_from_mapping(
        {
            "path": "README.md",
            "language": "markdown",
            "content": "# Demo\n",
        }
    )

    assert entry.path == "README.md"
    assert entry.language == "markdown"
    assert entry.status == "included"
    assert entry.text_status == "text"
    assert entry.content == "# Demo\n"


def test_file_entry_from_object_accepts_legacy_scan_object() -> None:
    entry = file_entry_from_object(LegacyScan(path="src/app.py"))

    assert entry.path == "src/app.py"
    assert entry.language == "python"
    assert entry.size_bytes == 12
    assert entry.line_count == 2
    assert entry.estimated_tokens == 4
    assert entry.content == "print('hi')\n"


def test_file_entries_from_objects_preserves_existing_file_entries() -> None:
    existing = FileEntry(path="docs/usage.md", language="markdown")

    entries = file_entries_from_objects((existing, {"path": "src/app.py"}))

    assert entries[0] is existing
    assert entries[1].path == "src/app.py"


def test_export_warning_adapters_accept_mapping_and_object() -> None:
    from_mapping = export_warning_from_mapping(
        {"path": "large.log", "message": "truncated", "code": "large"}
    )
    from_object = export_warning_from_object(
        LegacyWarning(path="secret.env", message="masked", code="secret")
    )

    assert from_mapping.path == "large.log"
    assert from_mapping.message == "truncated"
    assert from_mapping.code == "large"
    assert from_object.path == "secret.env"
    assert from_object.message == "masked"
    assert from_object.code == "secret"


def test_build_repository_export_from_entries_derives_summary() -> None:
    export = build_repository_export_from_entries(
        mode="ai",
        root_path="/tmp/repo",
        files=file_entries_from_objects(
            (
                LegacyScan(path="src/app.py", language="python"),
                LegacyScan(path="README.md", language="markdown", line_count=3),
            )
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
        warnings=(
            export_warning_from_mapping(
                {
                    "path": "assets/logo.png",
                    "message": "binary skipped",
                    "code": "binary",
                }
            ),
        ),
        git_branch="main",
        git_commit="abc123",
        git_dirty=False,
    )

    assert export.mode == "ai"
    assert export.repository.root_path == "/tmp/repo"
    assert export.repository.root_name == "repo"
    assert export.repository.git_branch == "main"
    assert export.summary.total_tracked_files == 3
    assert export.summary.scanned_files == 3
    assert export.summary.exported_text_files == 2
    assert export.summary.skipped_binary_files == 1
    assert export.summary.total_lines == 5
    assert export.summary.estimated_tokens == 8
    assert export.summary.file_type_statistics == {".py": 1, ".md": 1, ".png": 1}
    assert export.summary.language_statistics.counts == {
        "markdown": 1,
        "python": 1,
    }


def test_adapted_repository_export_can_be_rendered_by_model_markdown() -> None:
    export = build_repository_export_from_entries(
        mode="docs",
        root_path=Path("/tmp/repo"),
        files=file_entries_from_objects(
            (
                {
                    "path": "README.md",
                    "language": "markdown",
                    "content": "# Demo\n",
                    "line_count": 1,
                    "estimated_tokens": 2,
                },
            )
        ),
    )

    rendered = render_markdown_export_from_model(export)

    assert rendered.startswith("# Documentation Context")
    assert "Documentation files: 1" in rendered
    assert "### README.md" in rendered


def test_model_adapter_helpers_do_not_collect_or_analyze_data() -> None:
    import repodossier.exporters.model_adapter as model_adapter

    source = inspect.getsource(model_adapter)

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
        "git diff",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source
