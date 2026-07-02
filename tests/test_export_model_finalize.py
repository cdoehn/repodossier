import pytest

from repodossier.export_model import (
    ExportModelValidationError,
    ExportSummary,
    FileEntry,
    FileTreeEntry,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.export_model_finalize import (
    finalize_repository_export,
    refresh_repository_export_derived_sections,
    replace_repository_export_files,
    repository_export_with_files,
)


def test_finalize_repository_export_builds_summary_and_tree_without_mutating_input():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(
                path="src/app.py",
                language="python",
                status="included",
                line_count=10,
                estimated_tokens=40,
            ),
            FileEntry(
                path="README.md",
                language="markdown",
                status="included",
                line_count=5,
                estimated_tokens=20,
            ),
        ),
    )

    finalized = finalize_repository_export(export)

    assert export.summary == ExportSummary()
    assert export.tree == ()

    assert finalized.summary.total_tracked_files == 2
    assert finalized.summary.exported_text_files == 2
    assert finalized.summary.total_lines == 15
    assert finalized.summary.estimated_tokens == 60
    assert finalized.summary.language_statistics.counts == {
        "markdown": 1,
        "python": 1,
    }
    assert [entry.path for entry in finalized.tree] == [
        "README.md",
        "src",
    ]


def test_finalize_repository_export_can_preserve_existing_summary_and_tree():
    existing_summary = ExportSummary(total_tracked_files=99)
    existing_tree = (
        FileTreeEntry(path="custom", entry_type="directory"),
    )
    export = RepositoryExport(
        mode="ai",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        summary=existing_summary,
        tree=existing_tree,
        files=(
            FileEntry(path="src/app.py", language="python"),
        ),
    )

    finalized = finalize_repository_export(
        export,
        rebuild_summary=False,
        rebuild_tree=False,
    )

    assert finalized.summary is existing_summary
    assert finalized.tree is existing_tree


def test_repository_export_with_files_builds_finalized_model():
    export = repository_export_with_files(
        mode="docs",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(path="README.md", language="markdown"),
            FileEntry(path="docs/guide.md", language="markdown"),
        ),
    )

    assert export.summary.total_tracked_files == 2
    assert export.summary.language_statistics.counts == {"markdown": 2}
    assert [entry.path for entry in export.tree] == [
        "README.md",
        "docs",
    ]


def test_replace_repository_export_files_refreshes_derived_sections():
    export = repository_export_with_files(
        mode="changed",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(FileEntry(path="old.py", language="python"),),
    )

    updated = replace_repository_export_files(
        export,
        files=(
            FileEntry(path="new.py", language="python"),
            FileEntry(path="README.md", language="markdown"),
        ),
    )

    assert [entry.path for entry in export.files] == ["old.py"]
    assert [entry.path for entry in updated.files] == [
        "new.py",
        "README.md",
    ]
    assert updated.summary.total_tracked_files == 2
    assert updated.summary.language_statistics.counts == {
        "markdown": 1,
        "python": 1,
    }
    assert [entry.path for entry in updated.tree] == [
        "README.md",
        "new.py",
    ]


def test_refresh_repository_export_derived_sections_overwrites_stale_sections():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        summary=ExportSummary(total_tracked_files=999),
        tree=(FileTreeEntry(path="stale", entry_type="directory"),),
        files=(FileEntry(path="src/app.py", language="python"),),
    )

    refreshed = refresh_repository_export_derived_sections(export)

    assert refreshed.summary.total_tracked_files == 1
    assert [entry.path for entry in refreshed.tree] == ["src"]


def test_finalize_repository_export_validation_can_be_disabled():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
        files=(FileEntry(path="src/app.py", language="python"),),
    )

    with pytest.raises(ExportModelValidationError):
        finalize_repository_export(export)

    finalized = finalize_repository_export(export, validate=False)

    assert finalized.repository.root_path == ""
    assert finalized.summary.total_tracked_files == 1
