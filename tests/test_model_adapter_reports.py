"""Report preservation for RepositoryExport adapter helpers."""

from __future__ import annotations

import inspect

from repodossier.export_model import (
    CallGraphReport,
    DatabaseSchemaReport,
    DependencyReport,
    FileEntry,
    ImportGraphReport,
    SymbolIndex,
)
from repodossier.exporters.model_adapter import build_repository_export_from_entries
from repodossier.exporters.model_markdown import render_markdown_export_from_model


def _file_entry() -> FileEntry:
    return FileEntry(
        path="src/app.py",
        language="python",
        content="def main():\n    return 0\n",
        line_count=2,
        estimated_tokens=6,
    )


def test_build_repository_export_from_entries_preserves_analysis_reports() -> None:
    dependencies = DependencyReport(items=({"name": "PyYAML", "type": "runtime"},))
    database_schema = DatabaseSchemaReport(items=({"source": "schema.sql", "tables": 2},))
    symbol_index = SymbolIndex(symbols=({"path": "src/app.py", "symbol": "main"},))
    import_graph = ImportGraphReport(edges=({"source": "app", "target": "config"},))
    call_graph = CallGraphReport(edges=({"caller": "main", "callee": "run"},))

    export = build_repository_export_from_entries(
        mode="ai",
        root_path="/tmp/repo",
        files=(_file_entry(),),
        dependencies=dependencies,
        database_schema=database_schema,
        symbol_index=symbol_index,
        import_graph=import_graph,
        call_graph=call_graph,
    )

    assert export.dependencies is dependencies
    assert export.database_schema is database_schema
    assert export.symbol_index is symbol_index
    assert export.import_graph is import_graph
    assert export.call_graph is call_graph


def test_preserved_reports_are_visible_to_ai_markdown_renderer() -> None:
    export = build_repository_export_from_entries(
        mode="ai",
        root_path="/tmp/repo",
        files=(_file_entry(),),
        dependencies=DependencyReport(items=({"name": "PyYAML", "type": "runtime"},)),
        database_schema=DatabaseSchemaReport(items=({"source": "schema.sql", "tables": 2},)),
        symbol_index=SymbolIndex(symbols=({"path": "src/app.py", "symbol": "main"},)),
        import_graph=ImportGraphReport(edges=({"source": "app", "target": "config"},)),
        call_graph=CallGraphReport(edges=({"caller": "main", "callee": "run"},)),
    )

    rendered = render_markdown_export_from_model(export)

    assert rendered.startswith("# AI CONTEXT")
    assert "## Dependencies" in rendered
    assert "name: PyYAML" in rendered
    assert "## Database Schema" in rendered
    assert "tables: 2" in rendered
    assert "## Symbol Index" in rendered
    assert "symbol: main" in rendered
    assert "## Import Graph" in rendered
    assert "target: config" in rendered
    assert "## Call Graph" in rendered
    assert "callee: run" in rendered


def test_unsupplied_reports_keep_repository_export_defaults() -> None:
    export = build_repository_export_from_entries(
        mode="ai",
        root_path="/tmp/repo",
        files=(_file_entry(),),
    )

    assert export.dependencies.items == ()
    assert export.database_schema.items == ()
    assert export.symbol_index.symbols == ()
    assert export.import_graph.edges == ()
    assert export.call_graph.edges == ()


def test_model_adapter_report_support_stays_model_only() -> None:
    import repodossier.exporters.model_adapter as model_adapter

    source = inspect.getsource(model_adapter.build_repository_export_from_entries)

    forbidden_terms = (
        "RepositoryScanner",
        "list_tracked_files",
        "discover_repository",
        "analyze_dependencies",
        "analyze_database_schemas",
        "build_symbol_index",
        "build_import_graph",
        "build_call_graph",
        "collect_changed_file_scans",
        "git diff",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source
