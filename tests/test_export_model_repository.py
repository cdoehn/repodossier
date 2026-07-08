import pytest

from repodossier.export_model import RepositoryMetadata
from repodossier.export_model_repository import (
    make_repository_metadata,
    normalize_optional_text,
    normalize_repository_root_name,
    normalize_repository_root_path,
    repository_metadata_display_name,
    repository_metadata_has_git,
    repository_name_from_root_path,
    update_repository_git_metadata,
)


def test_make_repository_metadata_normalizes_root_and_git_fields():
    metadata = make_repository_metadata(
        root_path=" /tmp/project/ ",
        root_name=" repo_dossier ",
        git_branch=" main ",
        git_commit=" abc123 ",
        git_dirty=False,
    )

    assert metadata == RepositoryMetadata(
        root_path="/tmp/project",
        root_name="repo_dossier",
        git_branch="main",
        git_commit="abc123",
        git_dirty=False,
    )


def test_make_repository_metadata_derives_root_name_from_path():
    metadata = make_repository_metadata(
        root_path="/tmp/repo_dossier",
    )

    assert metadata.root_name == "repo_dossier"


def test_make_repository_metadata_converts_backslashes_in_root_path():
    metadata = make_repository_metadata(
        root_path="C:\\work\\repo_dossier",
    )

    assert metadata.root_path == "C:/work/repo_dossier"
    assert metadata.root_name == "repo_dossier"


def test_make_repository_metadata_rejects_empty_root_path_and_name():
    with pytest.raises(ValueError, match="root_path must not be empty"):
        make_repository_metadata(root_path="   ")

    with pytest.raises(ValueError, match="root_name must not be empty"):
        make_repository_metadata(root_path="/repo", root_name="   ")


def test_update_repository_git_metadata_returns_immutable_copy():
    metadata = make_repository_metadata(
        root_path="/repo",
        root_name="repo",
        git_branch="main",
        git_commit="old",
        git_dirty=False,
    )

    updated = update_repository_git_metadata(
        metadata,
        git_branch="feature",
        git_commit="new",
        git_dirty=True,
    )

    assert metadata.git_branch == "main"
    assert metadata.git_commit == "old"
    assert metadata.git_dirty is False

    assert updated.git_branch == "feature"
    assert updated.git_commit == "new"
    assert updated.git_dirty is True


def test_update_repository_git_metadata_preserves_fields_when_arguments_are_none():
    metadata = make_repository_metadata(
        root_path="/repo",
        root_name="repo",
        git_branch="main",
        git_commit="abc123",
        git_dirty=False,
    )

    updated = update_repository_git_metadata(metadata)

    assert updated == metadata


def test_repository_metadata_has_git_detects_any_git_field():
    assert not repository_metadata_has_git(
        make_repository_metadata(root_path="/repo", root_name="repo")
    )
    assert repository_metadata_has_git(
        make_repository_metadata(
            root_path="/repo",
            root_name="repo",
            git_branch="main",
        )
    )
    assert repository_metadata_has_git(
        make_repository_metadata(
            root_path="/repo",
            root_name="repo",
            git_dirty=False,
        )
    )


def test_repository_metadata_display_name_includes_branch_when_present():
    plain = make_repository_metadata(root_path="/repo", root_name="repo")
    with_branch = make_repository_metadata(
        root_path="/repo",
        root_name="repo",
        git_branch="main",
    )

    assert repository_metadata_display_name(plain) == "repo"
    assert repository_metadata_display_name(with_branch) == "repo (main)"


def test_normalization_helpers_are_stable():
    assert normalize_repository_root_path(" /a/b/ ") == "/a/b"
    assert normalize_repository_root_name(" repo/ ") == "repo"
    assert repository_name_from_root_path("/a/b/repo") == "repo"
    assert normalize_optional_text(None) is None
    assert normalize_optional_text("  ") is None
    assert normalize_optional_text(" value ") == "value"
