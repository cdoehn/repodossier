from __future__ import annotations

from pathlib import Path

from repodossier.changed import collect_changed_file_scans, scan_changed_file
from repodossier.git import ChangedFile


class DummyFileInfo:
    def __init__(self, path: Path, is_binary: bool = False) -> None:
        self.path = path
        self.is_binary = is_binary


def test_scan_changed_file_uses_scanner_for_existing_changed_file(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    changed_file = ChangedFile(path="src/app.py", status="modified")
    file_path = repo / "src/app.py"
    file_path.parent.mkdir()
    file_path.write_text("print('hello')\n", encoding="utf-8")

    scanned_paths: list[Path] = []

    def scanner(path: Path) -> DummyFileInfo:
        scanned_paths.append(path)
        return DummyFileInfo(path)

    result = scan_changed_file(repo, changed_file, scanner=scanner)

    assert result.path == "src/app.py"
    assert result.status == "modified"
    assert result.file_info is not None
    assert scanned_paths == [file_path]


def test_scan_changed_file_does_not_scan_deleted_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    changed_file = ChangedFile(
        path="obsolete.py",
        status="deleted",
        is_deleted=True,
    )

    def scanner(path: Path) -> DummyFileInfo:
        raise AssertionError(f"Deleted file should not be scanned: {path}")

    result = scan_changed_file(repo, changed_file, scanner=scanner)

    assert result.path == "obsolete.py"
    assert result.status == "deleted"
    assert result.is_deleted is True
    assert result.file_info is None


def test_scan_changed_file_handles_missing_non_deleted_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    changed_file = ChangedFile(path="missing.py", status="modified")

    def scanner(path: Path) -> DummyFileInfo:
        raise AssertionError(f"Missing file should not be scanned: {path}")

    result = scan_changed_file(repo, changed_file, scanner=scanner)

    assert result.path == "missing.py"
    assert result.file_info is None


def test_scan_changed_file_uses_default_repository_scanner(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    file_path = repo / "src" / "app.py"
    file_path.parent.mkdir()
    file_path.write_text("print('hello')\n", encoding="utf-8")

    result = scan_changed_file(
        repo,
        ChangedFile(path="src/app.py", status="modified"),
    )

    assert result.path == "src/app.py"
    assert result.status == "modified"
    assert result.file_info is not None
    assert result.file_info.relative_path == Path("src/app.py")
    assert result.file_info.absolute_path == file_path.resolve()
    assert result.file_info.is_text is True
    assert result.file_info.is_binary is False
    assert result.file_info.language == "python"
    assert result.file_info.content == "print('hello')\n"


def test_collect_changed_file_scans_returns_stable_sorted_results(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    for relative_path in ["b.py", "a.py"]:
        (repo / relative_path).write_text(relative_path, encoding="utf-8")

    changed_files = [
        ChangedFile(path="b.py", status="modified"),
        ChangedFile(path="deleted.py", status="deleted", is_deleted=True),
        ChangedFile(path="a.py", status="modified"),
    ]

    result = collect_changed_file_scans(
        repo,
        changed_files=changed_files,
        scanner=lambda path: DummyFileInfo(path),
    )

    assert [item.path for item in result] == ["a.py", "b.py", "deleted.py"]
    assert result[0].file_info is not None
    assert result[1].file_info is not None
    assert result[2].file_info is None


def test_changed_file_scan_exposes_binary_flag_from_file_info(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "image.bin").write_bytes(b"\x00\x01")
    changed_file = ChangedFile(path="image.bin", status="modified")

    result = scan_changed_file(
        repo,
        changed_file,
        scanner=lambda path: DummyFileInfo(path, is_binary=True),
    )

    assert result.is_binary is True


def test_collect_changed_file_scans_uses_branch_comparison_when_branch_is_given(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "feature.py").write_text("feature\n", encoding="utf-8")

    def fake_get_changed_files_against_branch(path: Path, branch: str) -> list[ChangedFile]:
        assert path == repo
        assert branch == "main"
        return [ChangedFile(path="feature.py", status="modified")]

    monkeypatch.setattr(
        "repodossier.changed.get_changed_files_against_branch",
        fake_get_changed_files_against_branch,
    )

    result = collect_changed_file_scans(
        repo,
        branch="main",
        scanner=lambda path: DummyFileInfo(path),
    )

    assert [item.path for item in result] == ["feature.py"]

