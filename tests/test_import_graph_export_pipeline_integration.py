from dataclasses import dataclass
from pathlib import Path

from repodossier.exporters.full import (
    _build_import_graph_for_export,
    _import_graph_export_source_path,
)


@dataclass
class FakeExportFile:
    relative_path: str


@dataclass
class FakeAbsoluteExportFile:
    path: Path


@dataclass
class FakeNonPathExportFile:
    name: str


def test_import_graph_export_source_path_accepts_relative_python_file(tmp_path: Path) -> None:
    assert _import_graph_export_source_path(
        FakeExportFile("src/app/main.py"),
        tmp_path,
    ) == tmp_path / "src/app/main.py"


def test_import_graph_export_source_path_accepts_absolute_python_file(tmp_path: Path) -> None:
    source_path = tmp_path / "src/app/main.py"

    assert _import_graph_export_source_path(
        FakeAbsoluteExportFile(source_path),
        tmp_path,
    ) == source_path


def test_import_graph_export_source_path_ignores_non_python_and_unknown_objects(tmp_path: Path) -> None:
    assert _import_graph_export_source_path(
        FakeExportFile("README.md"),
        tmp_path,
    ) is None
    assert _import_graph_export_source_path(
        FakeNonPathExportFile("main.py"),
        tmp_path,
    ) is None


def test_build_import_graph_for_export_uses_export_file_list(tmp_path: Path) -> None:
    project_files = {
        "src/app/__init__.py": "",
        "src/app/main.py": """
import os
import app.utils
from .missing import nope
""",
        "src/app/utils.py": "",
        "README.md": "# ignored\n",
    }

    export_files = []
    for relative_path, content in project_files.items():
        source_path = tmp_path / relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(content, encoding="utf-8")
        export_files.append(FakeExportFile(relative_path))

    graph = _build_import_graph_for_export(tmp_path, export_files)

    assert graph.modules == {
        "app": tmp_path / "src/app/__init__.py",
        "app.main": tmp_path / "src/app/main.py",
        "app.utils": tmp_path / "src/app/utils.py",
    }

    assert [
        (edge.source_module, edge.target_module)
        for edge in graph.edges
    ] == [
        ("app.main", "app.utils"),
    ]

    assert [
        (reference.source_module, reference.imported_module, reference.is_local)
        for reference in graph.external_imports
    ] == [
        ("app.main", "os", False),
    ]

    assert [
        (
            reference.source_module,
            reference.imported_module,
            reference.imported_name,
            reference.is_relative,
            reference.is_local,
        )
        for reference in graph.unresolved_imports
    ] == [
        ("app.main", "missing", "nope", True, False),
    ]

    assert graph.errors == ()
