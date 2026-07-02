from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.export_model_reports import (
    make_call_graph_report,
    make_database_schema_report,
    make_dependency_report,
    make_import_graph_report,
    make_recent_commit_report,
    make_secret_detection_summary,
    make_symbol_index,
    make_test_map_report,
    normalize_report_items,
    normalize_report_mapping,
)
from repodossier.export_model_serialization import repository_export_to_dict


def test_normalize_report_mapping_sorts_keys_and_copies_nested_values():
    original = {
        "z": 1,
        "a": {
            "b": 2,
            "a": 1,
        },
        "list": ["b", "a"],
        "set": {"y", "x"},
    }

    normalized = normalize_report_mapping(original)

    assert list(normalized) == ["a", "list", "set", "z"]
    assert list(normalized["a"]) == ["a", "b"]
    assert normalized["list"] == ["a", "b"]
    assert normalized["set"] == ["x", "y"]

    normalized["a"]["a"] = 99
    assert original["a"]["a"] == 1


def test_normalize_report_items_sorts_by_preferred_fields():
    items = (
        {"path": "src/b.py", "name": "b"},
        {"path": "src/a.py", "name": "a"},
        {"path": "src/a.py", "name": "z"},
    )

    normalized = normalize_report_items(items)

    assert normalized == (
        {"name": "a", "path": "src/a.py"},
        {"name": "z", "path": "src/a.py"},
        {"name": "b", "path": "src/b.py"},
    )


def test_make_dependency_report_normalizes_items():
    report = make_dependency_report(
        (
            {"package": "pytest", "source": "pyproject.toml"},
            {"package": "click", "source": "pyproject.toml"},
        )
    )

    assert report.items == (
        {"package": "click", "source": "pyproject.toml"},
        {"package": "pytest", "source": "pyproject.toml"},
    )


def test_make_database_schema_report_normalizes_items():
    report = make_database_schema_report(
        (
            {"table": "z_table", "columns": ["b", "a"]},
            {"table": "a_table", "columns": ["id"]},
        )
    )

    assert report.items == (
        {"columns": ["id"], "table": "a_table"},
        {"columns": ["a", "b"], "table": "z_table"},
    )


def test_make_secret_detection_summary_normalizes_findings_and_masked_files():
    summary = make_secret_detection_summary(
        findings=(
            {"path": "src/b.py", "kind": "token"},
            {"path": "src/a.py", "kind": "password"},
        ),
        masked_files=(
            "./src\\b.py",
            "src/a.py",
            "src/a.py",
        ),
    )

    assert summary.findings == (
        {"kind": "password", "path": "src/a.py"},
        {"kind": "token", "path": "src/b.py"},
    )
    assert summary.masked_files == ("src/a.py", "src/b.py")


def test_make_symbol_index_normalizes_symbols():
    index = make_symbol_index(
        (
            {"path": "src/b.py", "name": "B", "kind": "class"},
            {"path": "src/a.py", "name": "a", "kind": "function"},
        )
    )

    assert index.symbols == (
        {"kind": "function", "name": "a", "path": "src/a.py"},
        {"kind": "class", "name": "B", "path": "src/b.py"},
    )


def test_make_import_and_call_graph_reports_normalize_edges():
    import_graph = make_import_graph_report(
        (
            {"source": "b.py", "target": "a.py", "kind": "local"},
            {"source": "a.py", "target": "stdlib", "kind": "external"},
        )
    )
    call_graph = make_call_graph_report(
        (
            {"source": "b.run", "target": "a.load", "kind": "internal"},
            {"source": "a.run", "target": "print", "kind": "external"},
        )
    )

    assert import_graph.edges == (
        {"kind": "external", "source": "a.py", "target": "stdlib"},
        {"kind": "local", "source": "b.py", "target": "a.py"},
    )
    assert call_graph.edges == (
        {"kind": "external", "source": "a.run", "target": "print"},
        {"kind": "internal", "source": "b.run", "target": "a.load"},
    )


def test_make_test_map_and_recent_commit_reports_normalize_items():
    test_map = make_test_map_report(
        (
            {"source": "src/b.py", "test_file": "tests/test_b.py"},
            {"source": "src/a.py", "test_file": "tests/test_a.py"},
        )
    )
    recent = make_recent_commit_report(
        (
            {"short_hash": "b222222", "message": "Second"},
            {"short_hash": "a111111", "message": "First"},
        )
    )

    assert test_map.mappings == (
        {"source": "src/a.py", "test_file": "tests/test_a.py"},
        {"source": "src/b.py", "test_file": "tests/test_b.py"},
    )
    assert recent.commits == (
        {"message": "First", "short_hash": "a111111"},
        {"message": "Second", "short_hash": "b222222"},
    )


def test_reports_serialize_as_plain_export_model_data():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        dependencies=make_dependency_report(
            ({"package": "pytest", "source": "pyproject.toml"},)
        ),
        symbol_index=make_symbol_index(
            ({"path": "src/app.py", "name": "main", "kind": "function"},)
        ),
    )

    data = repository_export_to_dict(export)

    assert data["dependencies"]["items"] == [
        {"package": "pytest", "source": "pyproject.toml"},
    ]
    assert data["symbol_index"]["symbols"] == [
        {"kind": "function", "name": "main", "path": "src/app.py"},
    ]
