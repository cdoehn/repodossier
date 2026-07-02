import subprocess
from pathlib import Path

import repodossier.export_model_api as api
from repodossier.export_model_builder import build_repository_export_from_scan


def test_scanner_integration_builds_repository_export_model_from_real_fixture_repo(tmp_path):
    # Real files -> scanner -> RepositoryExport -> summary/tree/file/language checks.

    (tmp_path / "src").mkdir()
    (tmp_path / "web").mkdir()
    (tmp_path / "README.md").write_text("# Demo\n\nSmall fixture repo.\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text(
        "def main():\n    return 0\n",
        encoding="utf-8",
    )
    (tmp_path / "web" / "app.ts").write_text(
        "interface User { id: string }\n",
        encoding="utf-8",
    )
    (tmp_path / "web" / "index.html").write_text(
        "<!DOCTYPE html>\n<html><body>Hello</body></html>\n",
        encoding="utf-8",
    )
    (tmp_path / "assets.bin").write_bytes(b"\x00\x01\x02binary")

    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.email", "test@example.invalid")
    _run_git(tmp_path, "config", "user.name", "RepoDossier Test")
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", "Initial fixture repository")

    export = build_repository_export_from_scan(tmp_path, mode="full")

    assert export.mode == "full"
    assert export.repository.root_path == str(tmp_path.resolve())
    assert export.repository.root_name == tmp_path.name
    assert export.repository.git_branch in {"main", "master"}
    assert export.repository.git_commit
    assert export.repository.git_dirty is False

    assert [entry.path for entry in export.files] == [
        "README.md",
        "src/app.py",
        "web/app.ts",
        "web/index.html",
    ]
    assert [entry.path for entry in export.omitted_files] == ["assets.bin"]
    assert export.truncated_files == ()
    assert export.warnings == ()

    entries_by_path = {entry.path: entry for entry in export.files}
    assert entries_by_path["README.md"].language == "markdown"
    assert entries_by_path["src/app.py"].language == "python"
    assert entries_by_path["web/app.ts"].language == "typescript"
    assert entries_by_path["web/index.html"].language == "html"

    assert entries_by_path["src/app.py"].content == "def main():\n    return 0\n"
    assert entries_by_path["web/app.ts"].content == "interface User { id: string }\n"
    assert entries_by_path["web/index.html"].content.startswith("<!DOCTYPE html>")

    omitted = export.omitted_files[0]
    assert omitted.path == "assets.bin"
    assert omitted.text_status == "binary"
    assert omitted.status == "skipped"
    assert omitted.reason == "binary file"
    assert omitted.content is None

    assert export.summary.total_tracked_files == 5
    assert export.summary.scanned_files == 5
    assert export.summary.exported_text_files == 4
    assert export.summary.skipped_binary_files == 1
    assert export.summary.errored_files == 0
    assert export.summary.language_statistics.counts == {
        "html": 1,
        "markdown": 1,
        "python": 1,
        "typescript": 1,
        "unknown": 1,
    }

    tree_paths = api.tree_paths(export.tree)
    assert tree_paths == (
        "README.md",
        "assets.bin",
        "src",
        "src/app.py",
        "web",
        "web/app.ts",
        "web/index.html",
    )

    assert export.all_paths() == (
        "README.md",
        "assets.bin",
        "src/app.py",
        "web/app.ts",
        "web/index.html",
    )

    assert api.repository_export_readiness_status(export).valid
    assert api.repository_export_round_trip_status(export).valid


def test_scanner_integration_without_content_keeps_metadata_and_tree(tmp_path):
    # The real scanner path can build a metadata-only model for later AI/XML flows.

    (tmp_path / "src").mkdir()
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.email", "test@example.invalid")
    _run_git(tmp_path, "config", "user.name", "RepoDossier Test")
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", "Initial fixture repository")

    export = build_repository_export_from_scan(
        tmp_path,
        mode="ai",
        include_content=False,
    )

    assert export.mode == "ai"
    assert [entry.path for entry in export.files] == [
        "README.md",
        "src/app.py",
    ]
    assert [entry.content for entry in export.files] == [None, None]
    assert [entry.language for entry in export.files] == ["markdown", "python"]
    assert export.summary.total_tracked_files == 2
    assert export.summary.exported_text_files == 2
    assert api.tree_paths(export.tree) == (
        "README.md",
        "src",
        "src/app.py",
    )

    assert api.repository_export_readiness_status(
        export,
        include_content=False,
    ).valid


def _run_git(repo_path: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
