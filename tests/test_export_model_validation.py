import pytest

from repodossier.export_model import (
    ExportModelValidationError,
    FileEntry,
    FileTreeEntry,
    RepositoryExport,
    RepositoryMetadata,
    assert_valid_repository_export,
    validate_repository_export,
)


def test_validate_repository_export_accepts_minimal_valid_model():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(FileEntry(path="src/app.py", language="python"),),
        tree=(
            FileTreeEntry(
                path="src",
                entry_type="directory",
                children=(
                    FileTreeEntry(path="src/app.py", entry_type="file"),
                ),
            ),
        ),
    )

    assert validate_repository_export(export) == ()
    assert_valid_repository_export(export)


def test_validate_repository_export_reports_invalid_repository_metadata():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name=""),
    )

    issues = validate_repository_export(export)

    assert "repository.root_path must not be empty" in issues
    assert "repository.root_name must not be empty" in issues


def test_validate_repository_export_reports_invalid_file_values():
    export = RepositoryExport(
        mode="ai",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(
                path="",
                language="",
                size_bytes=-1,
                line_count=-2,
                estimated_tokens=-3,
                text_status="maybe",
                status="unknown",
            ),
        ),
    )

    issues = validate_repository_export(export)

    assert "files[0].path must not be empty" in issues
    assert "files[0].language must not be empty" in issues
    assert "files[0].size_bytes must not be negative" in issues
    assert "files[0].line_count must not be negative" in issues
    assert "files[0].estimated_tokens must not be negative" in issues
    assert any("files[0].text_status must be one of" in issue for issue in issues)
    assert any("files[0].status must be one of" in issue for issue in issues)


def test_validate_repository_export_reports_duplicate_paths_in_same_group():
    export = RepositoryExport(
        mode="docs",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(path="README.md", language="markdown"),
            FileEntry(path="README.md", language="markdown"),
        ),
    )

    assert (
        "files contains duplicate path: README.md"
        in validate_repository_export(export)
    )


def test_validate_repository_export_reports_invalid_tree_entries():
    export = RepositoryExport(
        mode="changed",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        tree=(
            FileTreeEntry(path="", entry_type="other"),
            FileTreeEntry(path="src", entry_type="directory"),
            FileTreeEntry(path="src", entry_type="directory"),
        ),
    )

    issues = validate_repository_export(export)

    assert "tree[0].path must not be empty" in issues
    assert "tree[0].entry_type must be one of ['directory', 'file']" in issues
    assert "tree contains duplicate path: src" in issues


def test_assert_valid_repository_export_raises_useful_error():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
    )

    with pytest.raises(ExportModelValidationError) as exc_info:
        assert_valid_repository_export(export)

    assert "Invalid repository export model:" in str(exc_info.value)
    assert "- repository.root_path must not be empty" in str(exc_info.value)
