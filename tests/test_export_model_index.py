from repodossier.export_model import FileEntry, RepositoryExport, RepositoryMetadata
from repodossier.export_model_index import (
    file_index_by_path,
    files_by_language,
    files_by_status,
    filter_files_by_language,
    filter_files_by_status,
    get_file_entry,
    iter_known_files,
    language_counts_from_export,
    status_counts_from_export,
)


def make_export() -> RepositoryExport:
    return RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(path="src/app.py", language="python", status="included"),
            FileEntry(path="README.md", language="markdown", status="included"),
        ),
        truncated_files=(
            FileEntry(path="src/large.py", language="python", status="truncated"),
            FileEntry(path="README.md", language="markdown", status="truncated"),
        ),
        omitted_files=(
            FileEntry(path="assets/logo.png", language="unknown", status="skipped"),
            FileEntry(path="src/large.py", language="python", status="skipped"),
        ),
    )


def test_iter_known_files_returns_deterministic_unique_paths_with_precedence():
    export = make_export()

    entries = iter_known_files(export)

    assert [entry.path for entry in entries] == [
        "README.md",
        "assets/logo.png",
        "src/app.py",
        "src/large.py",
    ]
    assert get_file_entry(export, "README.md").status == "included"
    assert get_file_entry(export, "src/large.py").status == "truncated"


def test_file_index_by_path_returns_lookup_mapping():
    export = make_export()

    index = file_index_by_path(export)

    assert sorted(index) == [
        "README.md",
        "assets/logo.png",
        "src/app.py",
        "src/large.py",
    ]
    assert index["src/app.py"].language == "python"
    assert get_file_entry(export, "missing.py") is None


def test_files_by_language_groups_files_deterministically():
    grouped = files_by_language(make_export())

    assert list(grouped) == ["markdown", "python", "unknown"]
    assert [entry.path for entry in grouped["python"]] == [
        "src/app.py",
        "src/large.py",
    ]


def test_files_by_status_groups_files_deterministically():
    grouped = files_by_status(make_export())

    assert list(grouped) == ["included", "skipped", "truncated"]
    assert [entry.path for entry in grouped["included"]] == [
        "README.md",
        "src/app.py",
    ]
    assert [entry.path for entry in grouped["truncated"]] == ["src/large.py"]


def test_filter_files_by_status_returns_matching_files_only():
    entries = filter_files_by_status(make_export(), {"included", "truncated"})

    assert [entry.path for entry in entries] == [
        "README.md",
        "src/app.py",
        "src/large.py",
    ]


def test_filter_files_by_language_returns_matching_files_only():
    entries = filter_files_by_language(make_export(), {"python"})

    assert [entry.path for entry in entries] == [
        "src/app.py",
        "src/large.py",
    ]


def test_language_counts_from_export_are_sorted_and_deduplicated():
    assert language_counts_from_export(make_export()) == {
        "markdown": 1,
        "python": 2,
        "unknown": 1,
    }


def test_status_counts_from_export_are_sorted_and_deduplicated():
    assert status_counts_from_export(make_export()) == {
        "included": 2,
        "skipped": 1,
        "truncated": 1,
    }
