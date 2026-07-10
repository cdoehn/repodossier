from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from repodossier.archive_cli import (
    ArchiveCliArguments,
    ArchiveSourceResolutionError,
    DEFAULT_ARCHIVE_NAME,
    ResolvedArchiveRepository,
    ResolvedArchiveSource,
    resolve_archive_inputs,
    resolve_source_folder,
)


def _git_init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return path


def _arguments(*sources: Path, output_dir: Path) -> ArchiveCliArguments:
    return ArchiveCliArguments(
        source_paths=tuple(sources),
        output_dir=output_dir,
        output_name=None,
        archive_name=DEFAULT_ARCHIVE_NAME,
    )


def test_repository_root_source_is_accepted(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")

    normalized, repository_root, repository_relative = resolve_source_folder(repo)

    assert normalized == repo.resolve()
    assert repository_root == repo.resolve()
    assert repository_relative == Path(".")


def test_repository_subfolder_source_is_accepted(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    source = repo / "src" / "backend"
    source.mkdir(parents=True)

    normalized, repository_root, repository_relative = resolve_source_folder(source)

    assert normalized == source.resolve()
    assert repository_root == repo.resolve()
    assert repository_relative == Path("src/backend")


def test_missing_source_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ArchiveSourceResolutionError, match="source folder does not exist"):
        resolve_source_folder(tmp_path / "missing")


def test_file_source_is_rejected(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    source_file = repo / "file.txt"
    source_file.write_text("x", encoding="utf-8")

    with pytest.raises(ArchiveSourceResolutionError, match="not a directory"):
        resolve_source_folder(source_file)


def test_non_git_folder_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "plain"
    source.mkdir()

    with pytest.raises(ArchiveSourceResolutionError, match="not inside a Git repository"):
        resolve_source_folder(source)


def test_relative_source_paths_are_resolved_against_cwd(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    source = repo / "backend"
    source.mkdir()

    normalized, repository_root, repository_relative = resolve_source_folder(
        Path("project/backend"),
        cwd=tmp_path,
    )

    assert normalized == source.resolve()
    assert repository_root == repo.resolve()
    assert repository_relative == Path("backend")


def test_multiple_sources_from_same_repository_share_one_repository_record(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    backend = repo / "backend"
    frontend = repo / "frontend"
    backend.mkdir()
    frontend.mkdir()

    resolved = resolve_archive_inputs(
        _arguments(backend, frontend, output_dir=tmp_path / "out")
    )

    assert len(resolved.sources) == 2
    assert len(resolved.repositories) == 1
    assert isinstance(resolved.repositories[0], ResolvedArchiveRepository)
    assert resolved.repositories[0].repository_root == repo.resolve()
    assert resolved.repositories[0].archive_path.as_posix() == "repositories/project"
    assert {source.repository_relative_path for source in resolved.sources} == {
        Path("backend"),
        Path("frontend"),
    }


def test_duplicate_equivalent_sources_are_deduplicated(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    source = repo / "backend"
    source.mkdir()

    resolved = resolve_archive_inputs(
        _arguments(source, source / ".." / "backend", output_dir=tmp_path / "out")
    )

    assert len(resolved.sources) == 1
    assert len(resolved.repositories) == 1
    assert resolved.sources[0].normalized_path == source.resolve()


def test_multiple_repositories_are_supported(tmp_path: Path) -> None:
    repo_a = _git_init(tmp_path / "repo-a")
    repo_b = _git_init(tmp_path / "repo-b")

    resolved = resolve_archive_inputs(
        _arguments(repo_a, repo_b, output_dir=tmp_path / "out")
    )

    assert len(resolved.sources) == 2
    assert len(resolved.repositories) == 2
    assert [repository.repository_id for repository in resolved.repositories] == [
        "repo-a",
        "repo-b",
    ]


def test_same_named_repositories_get_collision_free_archive_names(tmp_path: Path) -> None:
    repo_a = _git_init(tmp_path / "a" / "project")
    repo_b = _git_init(tmp_path / "b" / "project")

    resolved = resolve_archive_inputs(
        _arguments(repo_a, repo_b, output_dir=tmp_path / "out")
    )

    assert [repository.repository_id for repository in resolved.repositories] == [
        "project",
        "project-2",
    ]
    assert [repository.archive_path.as_posix() for repository in resolved.repositories] == [
        "repositories/project",
        "repositories/project-2",
    ]


def test_resolved_source_contains_future_archive_source_path(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    source = repo / "src" / "backend"
    source.mkdir(parents=True)

    resolved = resolve_archive_inputs(
        _arguments(source, output_dir=tmp_path / "out")
    )

    assert isinstance(resolved.sources[0], ResolvedArchiveSource)
    assert resolved.sources[0].archive_source_path.as_posix() == "repositories/project/src/backend"
    assert resolved.output_dir == (tmp_path / "out").resolve()
