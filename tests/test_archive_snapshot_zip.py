from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path, PurePosixPath

import pytest

import repodossier.archive_cli as archive_cli
from repodossier.archive_cli import (
    ArchiveCliArguments,
    ArchiveCreationError,
    DEFAULT_ARCHIVE_NAME,
    ResolvedArchiveRepository,
    create_archive_dossier,
    resolve_archive_inputs,
)
from repodossier.cli import main


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    result = _git(path, "init")
    assert result.returncode == 0, result.stderr
    assert _git(path, "config", "user.name", "Example User").returncode == 0
    assert _git(path, "config", "user.email", "example@example.invalid").returncode == 0
    return path


def _commit(repo: Path, message: str = "snapshot") -> None:
    result = _git(repo, "commit", "-m", message)
    assert result.returncode == 0, result.stderr


def _args(*sources: Path, output_dir: Path, output_name: str | None = None) -> ArchiveCliArguments:
    return ArchiveCliArguments(
        source_paths=tuple(sources),
        output_dir=output_dir,
        output_name=output_name,
        archive_name=DEFAULT_ARCHIVE_NAME,
    )


def _zip_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def _zip_text(path: Path, name: str) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read(name).decode("utf-8")


def test_snapshot_uses_committed_head_and_excludes_working_tree_and_git_metadata(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "tracked.txt").write_text("committed content", encoding="utf-8")
    (repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    assert _git(repo, "add", "tracked.txt", ".gitignore").returncode == 0
    _commit(repo, "committed baseline")

    (repo / "tracked.txt").write_text("unstaged working-tree content", encoding="utf-8")
    (repo / "staged.txt").write_text("staged but uncommitted", encoding="utf-8")
    assert _git(repo, "add", "staged.txt").returncode == 0
    (repo / "untracked.txt").write_text("untracked", encoding="utf-8")
    (repo / "ignored.txt").write_text("ignored", encoding="utf-8")

    output_dir = tmp_path / "out"
    result = create_archive_dossier(resolve_archive_inputs(_args(repo, output_dir=output_dir)))

    assert result.archive_path == output_dir / DEFAULT_ARCHIVE_NAME
    names = _zip_names(result.archive_path)
    assert "reports/archive-manifest.txt" in names
    assert "repositories/project/tracked.txt" in names
    assert "repositories/project/.gitignore" in names
    assert "repositories/project/staged.txt" not in names
    assert "repositories/project/untracked.txt" not in names
    assert "repositories/project/ignored.txt" not in names
    assert not any(name.startswith("repositories/project/.git/") for name in names)
    assert _zip_text(result.archive_path, "repositories/project/tracked.txt") == "committed content"


def test_git_archive_is_invoked_with_expected_core_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = ResolvedArchiveRepository(
        repository_root=tmp_path / "project",
        repository_id="project",
        archive_path=PurePosixPath("repositories/project"),
    )
    repository.repository_root.mkdir()
    destination = tmp_path / "snapshot.zip"
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured["command"] = command
        captured["cwd"] = kwargs.get("cwd")
        with zipfile.ZipFile(destination, "w") as archive:
            archive.writestr("repositories/project/file.txt", "content")
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(archive_cli.subprocess, "run", fake_run)

    archive_cli._run_git_archive(repository, destination)

    assert captured["command"] == [
        "git",
        "archive",
        "--format=zip",
        f"--output={destination}",
        "--prefix=repositories/project/",
        "HEAD",
    ]
    assert captured["cwd"] == repository.repository_root


def test_archive_requires_a_committed_head(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "staged.txt").write_text("not committed", encoding="utf-8")
    assert _git(repo, "add", "staged.txt").returncode == 0
    output_dir = tmp_path / "out"

    with pytest.raises(ArchiveCreationError, match="committed HEAD snapshot"):
        create_archive_dossier(resolve_archive_inputs(_args(repo, output_dir=output_dir)))

    assert not (output_dir / DEFAULT_ARCHIVE_NAME).exists()
    assert not list(output_dir.glob("*.git-archive-*.zip*"))


def test_untracked_output_directory_inside_repository_is_not_archived(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "tracked.txt").write_text("tracked", encoding="utf-8")
    assert _git(repo, "add", "tracked.txt").returncode == 0
    _commit(repo)
    output_dir = repo / "out"
    output_dir.mkdir()
    (output_dir / "old.txt").write_text("old output", encoding="utf-8")

    result = create_archive_dossier(resolve_archive_inputs(_args(repo, output_dir=output_dir)))

    names = _zip_names(result.archive_path)
    assert "repositories/project/tracked.txt" in names
    assert not any(name.startswith("repositories/project/out/") for name in names)


def test_multiple_sources_from_same_repository_create_one_snapshot(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    backend = repo / "backend"
    frontend = repo / "frontend"
    backend.mkdir()
    frontend.mkdir()
    (backend / "a.txt").write_text("a", encoding="utf-8")
    (frontend / "b.txt").write_text("b", encoding="utf-8")
    assert _git(repo, "add", ".").returncode == 0
    _commit(repo)

    result = create_archive_dossier(
        resolve_archive_inputs(_args(backend, frontend, output_dir=tmp_path / "out"))
    )

    names = _zip_names(result.archive_path)
    assert "repositories/project/backend/a.txt" in names
    assert "repositories/project/frontend/b.txt" in names
    assert not any(name.startswith("repositories/project-2/") for name in names)


def test_multiple_repositories_are_written_to_one_archive(tmp_path: Path) -> None:
    repo_a = _git_init(tmp_path / "repo-a")
    repo_b = _git_init(tmp_path / "repo-b")
    (repo_a / "a.txt").write_text("a", encoding="utf-8")
    (repo_b / "b.txt").write_text("b", encoding="utf-8")
    assert _git(repo_a, "add", ".").returncode == 0
    assert _git(repo_b, "add", ".").returncode == 0
    _commit(repo_a)
    _commit(repo_b)

    result = create_archive_dossier(
        resolve_archive_inputs(_args(repo_a, repo_b, output_dir=tmp_path / "out"))
    )

    names = _zip_names(result.archive_path)
    assert "reports/archive-manifest.txt" in names
    assert "repositories/repo-a/a.txt" in names
    assert "repositories/repo-b/b.txt" in names


def test_output_name_is_used_exactly_even_with_non_zip_extension(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "file.txt").write_text("content", encoding="utf-8")
    assert _git(repo, "add", "file.txt").returncode == 0
    _commit(repo)

    result = create_archive_dossier(
        resolve_archive_inputs(
            _args(repo, output_dir=tmp_path / "out", output_name="projektpaket.xml")
        )
    )

    assert result.archive_path.name == "projektpaket.xml"
    with zipfile.ZipFile(result.archive_path) as archive:
        assert "repositories/project/file.txt" in archive.namelist()


def test_existing_target_file_is_not_overwritten(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "file.txt").write_text("content", encoding="utf-8")
    assert _git(repo, "add", "file.txt").returncode == 0
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    target = output_dir / DEFAULT_ARCHIVE_NAME
    target.write_text("do not overwrite", encoding="utf-8")

    with pytest.raises(ArchiveCreationError, match="already exists"):
        create_archive_dossier(resolve_archive_inputs(_args(repo, output_dir=output_dir)))

    assert target.read_text(encoding="utf-8") == "do not overwrite"


def test_temporary_archives_are_removed_when_writing_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "file.txt").write_text("content", encoding="utf-8")
    assert _git(repo, "add", "file.txt").returncode == 0
    _commit(repo)
    output_dir = tmp_path / "out"

    def fail_manifest(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("forced manifest failure")

    monkeypatch.setattr(archive_cli, "_write_archive_manifest", fail_manifest)

    with pytest.raises(ArchiveCreationError, match="forced manifest failure"):
        create_archive_dossier(resolve_archive_inputs(_args(repo, output_dir=output_dir)))

    assert not list(output_dir.glob(".*.tmp-*"))
    assert not list(output_dir.glob("*.git-archive-*.zip*"))
    assert not (output_dir / DEFAULT_ARCHIVE_NAME).exists()


def test_cli_creates_archive_and_prints_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "file.txt").write_text("content", encoding="utf-8")
    assert _git(repo, "add", "file.txt").returncode == 0
    _commit(repo)
    output_dir = tmp_path / "out"

    exit_code = main([str(repo), str(output_dir), "--output-name", "bundle.zip"])

    captured = capsys.readouterr()
    assert exit_code == 0
    archive_path = output_dir / "bundle.zip"
    assert f"Wrote archive: {archive_path}" in captured.out
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    assert "reports/archive-manifest.txt" in names
    assert "repositories/project/file.txt" in names
