from repodossier.export_model import ExportConfigurationSummary, FileEntry
from repodossier.export_model_builder import (
    NO_EXTENSION_LABEL,
    build_file_tree_entries,
    create_repository_export,
    summarize_file_entries,
)


def test_summarize_file_entries_counts_core_statistics():
    files = (
        FileEntry(
            path="src/app.py",
            language="python",
            line_count=10,
            estimated_tokens=20,
        ),
        FileEntry(
            path="README",
            language="text",
            line_count=3,
            estimated_tokens=5,
        ),
        FileEntry(
            path="assets/logo.png",
            language="unknown",
            text_status="binary",
            status="skipped",
        ),
        FileEntry(
            path="broken.txt",
            language="text",
            status="error",
        ),
    )

    summary = summarize_file_entries(files)

    assert summary.total_tracked_files == 4
    assert summary.scanned_files == 4
    assert summary.exported_text_files == 2
    assert summary.skipped_binary_files == 1
    assert summary.errored_files == 1
    assert summary.total_lines == 13
    assert summary.estimated_tokens == 25
    assert summary.file_type_statistics == {
        ".png": 1,
        ".py": 1,
        ".txt": 1,
        NO_EXTENSION_LABEL: 1,
    }
    assert summary.language_statistics.counts == {
        "python": 1,
        "text": 2,
        "unknown": 1,
    }


def test_build_file_tree_entries_is_nested_and_deterministic():
    tree = build_file_tree_entries(
        [
            "./src/repodossier/export_model.py",
            "README.md",
            "src/repodossier/cli.py",
            "tests/test_export_model.py",
        ]
    )

    assert [entry.path for entry in tree] == ["src", "tests", "README.md"]

    src = tree[0]
    assert src.entry_type == "directory"
    assert [entry.path for entry in src.children] == ["src/repodossier"]

    package = src.children[0]
    assert [entry.path for entry in package.children] == [
        "src/repodossier/cli.py",
        "src/repodossier/export_model.py",
    ]


def test_create_repository_export_groups_files_by_status():
    config = ExportConfigurationSummary(
        config_active=True,
        include_paths=("src",),
        exclude_paths=("dist",),
    )
    included = FileEntry(path="src/a.py", language="python", status="included")
    skipped = FileEntry(
        path="dist/app.whl",
        language="unknown",
        text_status="binary",
        status="skipped",
    )
    truncated = FileEntry(path="large.md", language="markdown", status="truncated")
    errored = FileEntry(path="broken.txt", language="text", status="error")

    export = create_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        files=(truncated, skipped, included, errored),
        configuration=config,
        git_branch="main",
        git_commit="abc123",
        git_dirty=False,
    )

    assert export.mode == "full"
    assert export.repository.root_path == "/repo"
    assert export.repository.root_name == "repo"
    assert export.repository.git_branch == "main"
    assert export.repository.git_commit == "abc123"
    assert export.repository.git_dirty is False
    assert export.configuration is config
    assert export.files == (included,)
    assert export.omitted_files == (errored, skipped)
    assert export.truncated_files == (truncated,)
    assert export.summary.total_tracked_files == 4
    assert export.all_paths() == (
        "broken.txt",
        "dist/app.whl",
        "large.md",
        "src/a.py",
    )


def test_create_repository_export_handles_empty_file_list():
    export = create_repository_export(
        mode="ai",
        root_path="/repo",
        root_name="repo",
    )

    assert export.files == ()
    assert export.omitted_files == ()
    assert export.truncated_files == ()
    assert export.tree == ()
    assert export.summary.total_tracked_files == 0
