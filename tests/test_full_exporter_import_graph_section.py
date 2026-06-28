from dataclasses import dataclass
from pathlib import Path

from repocontext.exporters.full import (
    _build_import_graph_for_export,
    _format_import_graph_section,
)


@dataclass
class FakeExportFile:
    relative_path: str


def test_format_import_graph_section_renders_summary_dependencies_and_imports(tmp_path: Path) -> None:
    project_files = {
        "src/app/__init__.py": "",
        "src/app/main.py": """
import os
import app.utils
from .missing import nope
""",
        "src/app/utils.py": "",
    }

    export_files = []
    for relative_path, content in project_files.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        export_files.append(FakeExportFile(relative_path))

    graph = _build_import_graph_for_export(tmp_path, export_files)
    section = _format_import_graph_section(graph)

    assert "## Import Graph" in section
    assert "- Local modules: 3" in section
    assert "- Local dependencies: 1" in section
    assert "- External imports: 1" in section
    assert "- Unresolved imports: 1" in section
    assert "- app.main -> app.utils" in section
    assert "- os" in section
    assert "- app.main: missing.nope" in section


def test_format_import_graph_section_renders_none_for_empty_graph(tmp_path: Path) -> None:
    graph = _build_import_graph_for_export(tmp_path, [])
    section = _format_import_graph_section(graph)

    assert "## Import Graph" in section
    assert "- Local modules: 0" in section
    assert "Local dependencies:\n- none" in section
    assert "External imports:\n- none" in section
    assert "Unresolved imports:\n- none" in section
