import pytest

from repodossier.export_model_paths import (
    ancestor_export_paths,
    export_path_depth,
    export_path_name,
    export_path_parent,
    normalize_export_path,
    normalize_export_paths,
    sort_export_paths,
)


def test_normalize_export_path_converts_backslashes_and_dot_segments():
    assert normalize_export_path("src\\repodossier\\cli.py") == "src/repodossier/cli.py"
    assert normalize_export_path("./src/./app.py") == "src/app.py"
    assert normalize_export_path(" docs/guide.md ") == "docs/guide.md"


def test_normalize_export_path_rejects_empty_absolute_and_escaping_paths():
    with pytest.raises(ValueError, match="must not be empty"):
        normalize_export_path("")

    with pytest.raises(ValueError, match="must be relative"):
        normalize_export_path("/etc/passwd")

    with pytest.raises(ValueError, match="must not escape repository"):
        normalize_export_path("../secret.txt")

    with pytest.raises(ValueError, match="must not escape repository"):
        normalize_export_path("src/../../secret.txt")


def test_normalize_export_paths_deduplicates_and_sorts_alphabetically():
    assert normalize_export_paths(
        {
            "src/app.py",
            "./README.md",
            "src\\app.py",
            "docs/guide.md",
        }
    ) == ("README.md", "docs/guide.md", "src/app.py")


def test_export_path_parent_returns_none_for_root_files():
    assert export_path_parent("README.md") is None
    assert export_path_parent("src/repodossier/cli.py") == "src/repodossier"


def test_export_path_name_returns_final_component():
    assert export_path_name("src/repodossier/cli.py") == "cli.py"
    assert export_path_name("README.md") == "README.md"


def test_export_path_depth_counts_components():
    assert export_path_depth("README.md") == 1
    assert export_path_depth("src/repodossier/cli.py") == 3


def test_sort_export_paths_orders_by_depth_then_name():
    assert sort_export_paths(
        [
            "src/repodossier/cli.py",
            "README.md",
            "src/app.py",
            "docs",
            "src",
        ]
    ) == (
        "README.md",
        "docs",
        "src",
        "src/app.py",
        "src/repodossier/cli.py",
    )


def test_ancestor_export_paths_returns_parent_chain():
    assert ancestor_export_paths("README.md") == ()
    assert ancestor_export_paths("src/repodossier/cli.py") == (
        "src",
        "src/repodossier",
    )
