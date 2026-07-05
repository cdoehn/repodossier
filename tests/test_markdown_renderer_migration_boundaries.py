"""Regression tests for the Milestone 4 Markdown renderer migration boundary.

Milestone 4 migrates Markdown rendering toward RepositoryExport as the
renderer input. These tests intentionally do not migrate behavior yet. They
capture the current public exporter boundaries and keep the renderer free of
scanner, Git, and analyzer responsibilities.
"""

from __future__ import annotations

import inspect
from types import ModuleType

import repodossier.changed_exporter as changed_exporter
import repodossier.exporters.ai as ai_exporter
import repodossier.exporters.docs as docs_exporter
import repodossier.exporters.full as full_exporter
import repodossier.renderers.markdown as markdown_renderer


def _assert_public_callables(module: ModuleType, names: tuple[str, ...]) -> None:
    missing = [name for name in names if not hasattr(module, name)]
    assert missing == []

    non_callable = [name for name in names if not callable(getattr(module, name))]
    assert non_callable == []


def test_legacy_markdown_exporter_public_boundaries_remain_callable() -> None:
    """The existing export entry points stay stable during renderer migration."""

    expected_public_callables = {
        full_exporter: (
            "create_full_export_context",
            "build_full_export_context",
            "render_full_export",
            "write_full_export",
            "generate_full_export",
        ),
        ai_exporter: (
            "create_ai_export_context",
            "build_ai_export_context",
            "render_ai_export",
            "write_ai_export",
            "generate_ai_export",
        ),
        docs_exporter: (
            "create_docs_export_context",
            "build_docs_export_context",
            "render_docs_export",
            "write_docs_export",
            "generate_docs_export",
        ),
        changed_exporter: (
            "render_changed_export",
            "write_changed_export",
            "collect_changed_file_scans",
        ),
    }

    for module, callable_names in expected_public_callables.items():
        _assert_public_callables(module, callable_names)


def test_markdown_renderer_render_signature_stays_model_first() -> None:
    """MarkdownRenderer.render should consume the structured export model."""

    signature = inspect.signature(markdown_renderer.MarkdownRenderer.render)
    parameters = tuple(signature.parameters.values())

    assert tuple(parameter.name for parameter in parameters) == ("self", "export")
    assert parameters[1].annotation in {
        "RepositoryExport",
        markdown_renderer.RepositoryExport,
    }


def test_markdown_renderer_does_not_import_scanner_git_or_analyzers() -> None:
    """The Markdown renderer boundary must not grow data collection logic."""

    source = inspect.getsource(markdown_renderer)

    forbidden_fragments = (
        "from repodossier.git",
        "import repodossier.git",
        "from repodossier.scanner",
        "import repodossier.scanner",
        "from repodossier.dependencies",
        "import repodossier.dependencies",
        "from repodossier.schema",
        "import repodossier.schema",
        "from repodossier.symbols",
        "import repodossier.symbols",
        "from repodossier.import_graph",
        "import repodossier.import_graph",
        "from repodossier.call_graph",
        "import repodossier.call_graph",
        "from repodossier.changed",
        "import repodossier.changed",
        "RepositoryScanner(",
        "get_repository_info(",
        "list_tracked_files(",
        "build_import_graph(",
        "build_call_graph(",
        "discover_symbols(",
        "analyze_dependencies(",
    )

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_markdown_renderer_does_not_depend_on_legacy_export_contexts() -> None:
    """Legacy exporter contexts stay outside the renderer module."""

    renderer_namespace = vars(markdown_renderer)

    for legacy_name in (
        "FullExportContext",
        "AIExportContext",
        "DocumentationExportContext",
        "ChangedFileScan",
        "ChangedExportContext",
    ):
        assert legacy_name not in renderer_namespace
