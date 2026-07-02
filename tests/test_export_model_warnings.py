import pytest

from repodossier.export_model import ExportWarning, RepositoryExport, RepositoryMetadata
from repodossier.export_model_warnings import (
    append_export_warnings,
    make_export_warning,
    normalize_export_warnings,
    warning_counts_by_code,
    warning_messages,
    warnings_by_path,
)


def test_make_export_warning_normalizes_message_path_and_code():
    warning = make_export_warning(
        "  File was truncated  ",
        path="./src\\app.py",
        code=" limit ",
    )

    assert warning.message == "File was truncated"
    assert warning.path == "src/app.py"
    assert warning.code == "limit"


def test_make_export_warning_rejects_empty_message():
    with pytest.raises(ValueError, match="message must not be empty"):
        make_export_warning("   ")


def test_make_export_warning_allows_repository_level_warning():
    warning = make_export_warning("Repository has no Git metadata")

    assert warning.message == "Repository has no Git metadata"
    assert warning.path is None
    assert warning.code is None


def test_normalize_export_warnings_deduplicates_and_sorts():
    warnings = (
        ExportWarning(message="B warning", path="src/b.py", code="b"),
        ExportWarning(message="A warning", path="src/a.py", code="a"),
        ExportWarning(message="A warning", path="src/a.py", code="a"),
        ExportWarning(message="   "),
    )

    normalized = normalize_export_warnings(warnings)

    assert normalized == (
        ExportWarning(message="A warning", path="src/a.py", code="a"),
        ExportWarning(message="B warning", path="src/b.py", code="b"),
    )


def test_append_export_warnings_returns_copy_with_merged_warnings():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        warnings=(
            ExportWarning(message="Existing", path="a.py", code="old"),
        ),
    )

    updated = append_export_warnings(
        export,
        (
            ExportWarning(message="New", path="b.py", code="new"),
            ExportWarning(message="Existing", path="a.py", code="old"),
        ),
    )

    assert export.warnings == (
        ExportWarning(message="Existing", path="a.py", code="old"),
    )
    assert updated.warnings == (
        ExportWarning(message="Existing", path="a.py", code="old"),
        ExportWarning(message="New", path="b.py", code="new"),
    )


def test_warning_counts_by_code_uses_uncategorized_fallback():
    warnings = (
        ExportWarning(message="A", code="limit"),
        ExportWarning(message="B", code="limit"),
        ExportWarning(message="C"),
    )

    assert warning_counts_by_code(warnings) == {
        "limit": 2,
        "uncategorized": 1,
    }


def test_warnings_by_path_groups_repository_level_and_file_warnings():
    warnings = (
        ExportWarning(message="Repo warning", code="repo"),
        ExportWarning(message="B", path="src/app.py", code="b"),
        ExportWarning(message="A", path="src/app.py", code="a"),
    )

    grouped = warnings_by_path(warnings)

    assert list(grouped) == ["<repository>", "src/app.py"]
    assert [warning.message for warning in grouped["<repository>"]] == [
        "Repo warning",
    ]
    assert [warning.message for warning in grouped["src/app.py"]] == [
        "A",
        "B",
    ]


def test_warning_messages_returns_sorted_deduplicated_messages():
    warnings = (
        ExportWarning(message="B", path="b.py"),
        ExportWarning(message="A", path="a.py"),
        ExportWarning(message="A", path="a.py"),
    )

    assert warning_messages(warnings) == ("A", "B")
