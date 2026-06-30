from __future__ import annotations

from pathlib import Path

from repodossier.changed import ChangedFileScan
from repodossier.changed_exporter import render_changed_export, write_changed_export
from repodossier.git import ChangedFile


class DummyFileInfo:
    def __init__(
        self,
        *,
        is_binary: bool = False,
        language: str = "python",
        line_count: int = 1,
        token_estimate: int = 3,
    ) -> None:
        self.is_binary = is_binary
        self.language = language
        self.line_count = line_count
        self.token_estimate = token_estimate


def make_scan(
    path: str,
    status: str,
    *,
    file_info: DummyFileInfo | None = None,
    is_untracked: bool = False,
    is_deleted: bool = False,
) -> ChangedFileScan:
    return ChangedFileScan(
        changed_file=ChangedFile(
            path=path,
            status=status,
            is_tracked=not is_untracked,
            is_untracked=is_untracked,
            is_deleted=is_deleted,
        ),
        file_info=file_info,
    )


def test_render_changed_export_contains_header_summary_and_overview(
    tmp_path: Path,
) -> None:
    (tmp_path / "app.py").write_text("print('changed')\n", encoding="utf-8")
    scans = [make_scan("app.py", "modified", file_info=DummyFileInfo())]

    output = render_changed_export(tmp_path, scans=scans)

    assert "# Changed Export" in output
    assert "Compare Mode: Working tree" in output
    assert "# Changed Files Summary" in output
    assert "- Total: 1" in output
    assert "- Modified: 1" in output
    assert "- `app.py` (modified)" in output


def test_render_changed_export_includes_text_file_contents(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("print('changed')\n", encoding="utf-8")
    scans = [
        make_scan(
            "src/app.py",
            "modified",
            file_info=DummyFileInfo(language="python", line_count=1, token_estimate=4),
        )
    ]

    output = render_changed_export(tmp_path, scans=scans)

    assert "# Changed File Contents" in output
    assert "## src/app.py" in output
    assert "- Language: python" in output
    assert "- Lines: 1" in output
    assert "- Estimated tokens: 4" in output
    assert "print('changed')" in output


def test_render_changed_export_lists_deleted_files_without_dumping_contents(
    tmp_path: Path,
) -> None:
    scans = [
        make_scan(
            "obsolete.py",
            "deleted",
            is_deleted=True,
            file_info=None,
        )
    ]

    output = render_changed_export(tmp_path, scans=scans)

    assert "- Deleted: 1" in output
    assert "# Deleted Files" in output
    assert "- `obsolete.py`" in output
    assert "## obsolete.py" not in output


def test_render_changed_export_skips_binary_file_contents(tmp_path: Path) -> None:
    (tmp_path / "image.bin").write_bytes(b"\x00\x01binary")
    scans = [
        make_scan(
            "image.bin",
            "modified",
            file_info=DummyFileInfo(is_binary=True),
        )
    ]

    output = render_changed_export(tmp_path, scans=scans)

    assert "- Binary/skipped files: 1" in output
    assert "# Binary / Skipped Files" in output
    assert "- `image.bin` (binary)" in output
    assert "\x00\x01binary" not in output


def test_render_changed_export_counts_added_untracked_and_renamed_files(
    tmp_path: Path,
) -> None:
    for path in ["added.py", "notes.txt", "renamed.py"]:
        (tmp_path / path).write_text(path, encoding="utf-8")

    scans = [
        make_scan("added.py", "added", file_info=DummyFileInfo()),
        make_scan("notes.txt", "untracked", file_info=DummyFileInfo(), is_untracked=True),
        make_scan("renamed.py", "renamed", file_info=DummyFileInfo()),
    ]

    output = render_changed_export(tmp_path, scans=scans)

    assert "- Added: 1" in output
    assert "- Renamed: 1" in output
    assert "- Untracked: 1" in output
    assert "- Text files: 3" in output


def test_render_changed_export_handles_empty_changed_set(tmp_path: Path) -> None:
    output = render_changed_export(tmp_path, scans=[])

    assert "- Total: 0" in output
    assert "No changed files detected." in output
    assert "No changed text file contents to include." in output
    assert "No deleted files." in output
    assert "No binary or skipped files." in output


def test_write_changed_export_writes_changed_txt(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('changed')\n", encoding="utf-8")
    output_path = tmp_path / "changed.txt"
    scans = [make_scan("app.py", "modified", file_info=DummyFileInfo())]

    result = write_changed_export(tmp_path, output_path, scans=scans)

    assert result == output_path
    assert output_path.exists()
    assert "# Changed Export" in output_path.read_text(encoding="utf-8")


def test_render_changed_export_includes_git_diff_section(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "app.py").write_text("print('changed')\n", encoding="utf-8")
    scans = [make_scan("app.py", "modified", file_info=DummyFileInfo())]

    def fake_get_diff(repo_path: Path, path: str | None = None) -> str:
        assert repo_path == tmp_path
        assert path == "app.py"
        return "diff --git a/app.py b/app.py\n-print('old')\n+print('changed')\n"

    monkeypatch.setattr("repodossier.changed_exporter.get_diff", fake_get_diff)

    output = render_changed_export(tmp_path, scans=scans)

    assert "# Git Diff" in output
    assert "## app.py" in output
    assert "```diff" in output
    assert "+print('changed')" in output


def test_render_changed_export_can_disable_git_diff_section(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('changed')\n", encoding="utf-8")
    scans = [make_scan("app.py", "modified", file_info=DummyFileInfo())]

    output = render_changed_export(tmp_path, scans=scans, include_diff=False)

    assert "# Git Diff" not in output
    assert "# Changed File Contents" in output


def test_render_changed_export_skips_binary_files_in_git_diff_section(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "image.bin").write_bytes(b"\x00\x01binary")
    scans = [
        make_scan(
            "image.bin",
            "modified",
            file_info=DummyFileInfo(is_binary=True),
        )
    ]

    def fake_get_diff(repo_path: Path, path: str | None = None) -> str:
        raise AssertionError("Binary files should not request git diff")

    monkeypatch.setattr("repodossier.changed_exporter.get_diff", fake_get_diff)

    output = render_changed_export(tmp_path, scans=scans)

    assert "# Git Diff" in output
    assert "No git diff available." in output
    assert "## image.bin" not in output


def test_render_changed_export_marks_missing_diff_for_untracked_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "notes.txt").write_text("new file\n", encoding="utf-8")
    scans = [
        make_scan(
            "notes.txt",
            "untracked",
            file_info=DummyFileInfo(language="text"),
            is_untracked=True,
        )
    ]

    monkeypatch.setattr("repodossier.changed_exporter.get_diff", lambda repo, path=None: "")

    output = render_changed_export(tmp_path, scans=scans)

    assert "# Git Diff" in output
    assert "## notes.txt" in output
    assert "No git diff available for this file." in output


def test_render_changed_export_uses_branch_compare_mode_and_branch_diff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "app.py").write_text("print('feature')\n", encoding="utf-8")
    scans = [make_scan("app.py", "modified", file_info=DummyFileInfo())]

    def fake_get_diff_against_branch(repo_path: Path, branch: str, path: str | None = None) -> str:
        assert repo_path == tmp_path
        assert branch == "main"
        assert path == "app.py"
        return "diff --git a/app.py b/app.py\n-print('main')\n+print('feature')\n"

    monkeypatch.setattr(
        "repodossier.changed_exporter.get_diff_against_branch",
        fake_get_diff_against_branch,
    )

    output = render_changed_export(tmp_path, scans=scans, branch="main")

    assert "Compare Mode: Against branch: main" in output
    assert "+print('feature')" in output


def test_write_changed_export_accepts_branch_argument(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_path = tmp_path / "changed.txt"
    (tmp_path / "app.py").write_text("print('feature')\n", encoding="utf-8")
    scans = [make_scan("app.py", "modified", file_info=DummyFileInfo())]

    monkeypatch.setattr(
        "repodossier.changed_exporter.get_diff_against_branch",
        lambda repo_path, branch, path=None: "",
    )

    write_changed_export(tmp_path, output_path, scans=scans, branch="main", include_diff=True)

    assert "Compare Mode: Against branch: main" in output_path.read_text(encoding="utf-8")

