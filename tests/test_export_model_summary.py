from repodossier.export_model import FileEntry, RepositoryExport, RepositoryMetadata
from repodossier.export_model_summary import (
    build_export_summary,
    build_export_summary_from_export,
    count_files_by_language,
    count_files_by_status,
    file_type_statistics_from_files,
    language_statistics_from_files,
)


def test_build_export_summary_counts_basic_file_statistics():
    files = (
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
        FileEntry(
            path="assets/logo.png",
            language="unknown",
            text_status="binary",
            status="skipped",
            size_bytes=100,
        ),
        FileEntry(
            path="broken.txt",
            language="text",
            status="error",
        ),
    )

    summary = build_export_summary(files)

    assert summary.total_tracked_files == 4
    assert summary.scanned_files == 4
    assert summary.exported_text_files == 2
    assert summary.skipped_binary_files == 1
    assert summary.errored_files == 1
    assert summary.total_lines == 15
    assert summary.estimated_tokens == 60
    assert summary.file_type_statistics == {
        ".md": 1,
        ".png": 1,
        ".py": 1,
        ".txt": 1,
    }
    assert summary.language_statistics.counts == {
        "markdown": 1,
        "python": 1,
        "text": 1,
        "unknown": 1,
    }


def test_build_export_summary_from_export_uses_known_files_once():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(path="README.md", language="markdown", status="included"),
            FileEntry(path="src/app.py", language="python", status="included"),
        ),
        truncated_files=(
            FileEntry(path="src/large.py", language="python", status="truncated"),
            FileEntry(path="README.md", language="markdown", status="truncated"),
        ),
        omitted_files=(
            FileEntry(path="assets/logo.png", language="unknown", status="skipped"),
        ),
    )

    summary = build_export_summary_from_export(export)

    assert summary.total_tracked_files == 4
    assert summary.exported_text_files == 2
    assert summary.file_type_statistics == {
        ".md": 1,
        ".png": 1,
        ".py": 2,
    }
    assert summary.language_statistics.counts == {
        "markdown": 1,
        "python": 2,
        "unknown": 1,
    }


def test_language_statistics_from_files_is_sorted_and_uses_unknown_fallback():
    files = (
        FileEntry(path="b.txt", language="text"),
        FileEntry(path="a.py", language="python"),
        FileEntry(path="unknown", language=""),
    )

    assert language_statistics_from_files(files) == {
        "python": 1,
        "text": 1,
        "unknown": 1,
    }


def test_file_type_statistics_from_files_counts_suffixes_and_extensionless_names():
    files = (
        FileEntry(path="Dockerfile", language="dockerfile"),
        FileEntry(path="README.md", language="markdown"),
        FileEntry(path="src/app.PY", language="python"),
        FileEntry(path="src/test_app.py", language="python"),
    )

    assert file_type_statistics_from_files(files) == {
        ".md": 1,
        ".py": 2,
        "Dockerfile": 1,
    }


def test_count_files_by_status_counts_exact_status():
    files = (
        FileEntry(path="a.py", language="python", status="included"),
        FileEntry(path="b.py", language="python", status="included"),
        FileEntry(path="c.py", language="python", status="truncated"),
    )

    assert count_files_by_status(files, "included") == 2
    assert count_files_by_status(files, "truncated") == 1
    assert count_files_by_status(files, "skipped") == 0


def test_count_files_by_language_counts_exact_language():
    files = (
        FileEntry(path="a.py", language="python"),
        FileEntry(path="b.py", language="python"),
        FileEntry(path="README.md", language="markdown"),
    )

    assert count_files_by_language(files, "python") == 2
    assert count_files_by_language(files, "markdown") == 1
    assert count_files_by_language(files, "text") == 0
