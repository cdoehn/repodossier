from pathlib import Path
import subprocess

from repodossier.export_model import ExportConfigurationSummary, FileEntry
from repodossier.models import FileInfo
from repodossier.export_model_builder import (
    NO_EXTENSION_LABEL,
    build_file_tree_entries,
    build_repository_export_from_scan,
    create_repository_export,
    file_entries_from_scan_infos,
    file_entry_from_scan_info,
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


def test_file_entry_from_scan_info_maps_text_file_info_to_model_entry():
    file_info = FileInfo(
        relative_path=Path("src/app.py"),
        absolute_path=Path("/repo/src/app.py"),
        size_bytes=32,
        is_text=True,
        is_binary=False,
        language="python",
        line_count=2,
        estimated_tokens=8,
        content="def main():\n    return 0\n",
    )

    entry = file_entry_from_scan_info(file_info)

    assert entry.path == "src/app.py"
    assert entry.language == "python"
    assert entry.size_bytes == 32
    assert entry.line_count == 2
    assert entry.estimated_tokens == 8
    assert entry.text_status == "text"
    assert entry.status == "included"
    assert entry.content == "def main():\n    return 0\n"
    assert entry.reason is None


def test_file_entries_from_scan_infos_maps_binary_and_error_results():
    binary_info = FileInfo(
        relative_path=Path("assets/logo.bin"),
        absolute_path=Path("/repo/assets/logo.bin"),
        size_bytes=4,
        is_text=True,
        is_binary=True,
        language=None,
        content=None,
    )
    error_info = FileInfo(
        relative_path=Path("broken.txt"),
        absolute_path=Path("/repo/broken.txt"),
        is_text=False,
        is_binary=False,
        language="text",
        error="Unable to read file",
    )

    entries = file_entries_from_scan_infos((error_info, binary_info))

    assert [entry.path for entry in entries] == [
        "assets/logo.bin",
        "broken.txt",
    ]
    assert entries[0].text_status == "binary"
    assert entries[0].status == "skipped"
    assert entries[0].reason == "binary file"
    assert entries[0].content is None
    assert entries[1].text_status == "text"
    assert entries[1].status == "error"
    assert entries[1].reason == "Unable to read file"


def test_build_repository_export_from_scan_uses_real_repository_scanner(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text(
        "def main():\n    return 0\n",
        encoding="utf-8",
    )
    (tmp_path / "assets.bin").write_bytes(b"\x00\x01demo")

    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.email", "test@example.invalid")
    _run_git(tmp_path, "config", "user.name", "RepoDossier Test")
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", "Initial test repository")

    export = build_repository_export_from_scan(tmp_path, mode="full")

    assert export.mode == "full"
    assert export.repository.root_path == str(tmp_path.resolve())
    assert export.repository.root_name == tmp_path.name
    assert export.repository.git_commit is not None
    assert export.repository.git_dirty is False

    assert [entry.path for entry in export.files] == [
        "README.md",
        "src/app.py",
    ]
    assert [entry.path for entry in export.omitted_files] == [
        "assets.bin",
    ]
    assert export.truncated_files == ()
    assert export.warnings == ()

    assert export.files[0].language == "markdown"
    assert export.files[1].language == "python"
    assert export.files[1].content == "def main():\n    return 0\n"
    assert export.omitted_files[0].text_status == "binary"
    assert export.omitted_files[0].status == "skipped"

    assert export.summary.total_tracked_files == 3
    assert export.summary.scanned_files == 3
    assert export.summary.exported_text_files == 2
    assert export.summary.skipped_binary_files == 1
    assert export.summary.errored_files == 0
    assert export.summary.language_statistics.counts == {
        "markdown": 1,
        "python": 1,
        "unknown": 1,
    }
    assert export.all_paths() == (
        "README.md",
        "assets.bin",
        "src/app.py",
    )


def test_build_repository_export_from_scan_accepts_pre_scanned_infos_without_content(tmp_path):
    file_info = FileInfo(
        relative_path=Path("src/app.ts"),
        absolute_path=tmp_path / "src" / "app.ts",
        size_bytes=22,
        is_text=True,
        is_binary=False,
        language="typescript",
        line_count=1,
        estimated_tokens=6,
        content="const name: string = 'x'\n",
    )

    export = build_repository_export_from_scan(
        tmp_path,
        mode="ai",
        file_infos=(file_info,),
        include_content=False,
        include_git_metadata=False,
    )

    assert export.mode == "ai"
    assert export.repository.git_branch is None
    assert export.repository.git_commit is None
    assert export.repository.git_dirty is None
    assert export.files[0].path == "src/app.ts"
    assert export.files[0].language == "typescript"
    assert export.files[0].content is None
    assert export.summary.language_statistics.counts == {"typescript": 1}


def test_build_repository_export_from_scan_is_available_from_public_api(tmp_path):
    import repodossier.export_model_api as api

    file_info = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        size_bytes=7,
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=1,
        estimated_tokens=2,
        content="# Demo\n",
    )

    export = api.build_repository_export_from_scan(
        tmp_path,
        file_infos=(file_info,),
        include_git_metadata=False,
    )

    assert export.files[0].path == "README.md"
    assert api.repository_export_readiness_status(export).valid


def _run_git(repo_path: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

