import pytest

from repodossier.export_model import FileEntry, RepositoryExport, RepositoryMetadata
from repodossier.export_model_tree import (
    build_file_tree,
    build_file_tree_from_entries,
    build_file_tree_from_export,
    flatten_file_tree,
    tree_paths,
)


def test_build_file_tree_returns_empty_tuple_for_empty_input():
    assert build_file_tree([]) == ()


def test_build_file_tree_builds_deterministic_nested_tree():
    tree = build_file_tree(
        [
            "src/repodossier/cli.py",
            "README.md",
            "src/repodossier/export_model.py",
            "docs/guide.md",
        ]
    )

    assert [entry.path for entry in tree] == [
        "README.md",
        "docs",
        "src",
    ]

    docs = tree[1]
    src = tree[2]

    assert docs.entry_type == "directory"
    assert [entry.path for entry in docs.children] == ["docs/guide.md"]

    assert src.entry_type == "directory"
    assert [entry.path for entry in src.children] == ["src/repodossier"]

    repodossier = src.children[0]
    assert repodossier.entry_type == "directory"
    assert [entry.path for entry in repodossier.children] == [
        "src/repodossier/cli.py",
        "src/repodossier/export_model.py",
    ]


def test_build_file_tree_normalizes_and_deduplicates_paths():
    tree = build_file_tree(
        [
            "./src/app.py",
            "src\\app.py",
            "src/utils.py",
        ]
    )

    assert tree_paths(tree) == (
        "src",
        "src/app.py",
        "src/utils.py",
    )


def test_build_file_tree_rejects_file_directory_conflicts():
    with pytest.raises(ValueError, match="both files and directories"):
        build_file_tree(["src", "src/app.py"])


def test_build_file_tree_from_entries_uses_entry_paths():
    entries = (
        FileEntry(path="src/app.py", language="python"),
        FileEntry(path="README.md", language="markdown"),
    )

    tree = build_file_tree_from_entries(entries)

    assert tree_paths(tree) == (
        "README.md",
        "src",
        "src/app.py",
    )


def test_build_file_tree_from_export_uses_known_files_once():
    export = RepositoryExport(
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
        ),
    )

    tree = build_file_tree_from_export(export)

    assert tree_paths(tree) == (
        "README.md",
        "assets",
        "assets/logo.png",
        "src",
        "src/app.py",
        "src/large.py",
    )


def test_flatten_file_tree_returns_preorder_entries():
    tree = build_file_tree(["src/pkg/app.py", "src/pkg/utils.py"])

    flattened = flatten_file_tree(tree)

    assert [entry.path for entry in flattened] == [
        "src",
        "src/pkg",
        "src/pkg/app.py",
        "src/pkg/utils.py",
    ]


def test_tree_paths_returns_preorder_paths():
    tree = build_file_tree(["b/file.txt", "a/file.txt"])

    assert tree_paths(tree) == (
        "a",
        "a/file.txt",
        "b",
        "b/file.txt",
    )
