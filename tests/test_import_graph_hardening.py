from pathlib import Path

from repocontext.exporters.full import (
    _build_import_graph_for_export,
    _format_import_graph_section,
    _import_graph_export_source_path,
)
from repocontext.import_graph import build_import_graph
from repocontext.models import FileInfo


def _write_file(repo_root: Path, relative_path: str, content: str) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _graph_signature(graph):
    return {
        "modules": sorted((name, path.as_posix()) for name, path in graph.modules.items()),
        "edges": [
            (
                edge.source_module,
                edge.target_module,
                edge.import_type,
                edge.imported_name,
                edge.line_number,
            )
            for edge in graph.edges
        ],
        "external": [
            (
                reference.source_module,
                reference.imported_module,
                reference.imported_name,
                reference.line_number,
            )
            for reference in graph.external_imports
        ],
        "unresolved": [
            (
                reference.source_module,
                reference.imported_module,
                reference.imported_name,
                reference.line_number,
                reference.level,
            )
            for reference in graph.unresolved_imports
        ],
        "errors": [
            (
                error.source_path.as_posix(),
                error.error_type,
                error.line_number,
            )
            for error in graph.errors
        ],
    }


def test_import_graph_collects_syntax_errors_without_crashing(tmp_path: Path) -> None:
    paths = [
        _write_file(tmp_path, "src/app/__init__.py", ""),
        _write_file(
            tmp_path,
            "src/app/main.py",
            "import os\nimport app.utils\n",
        ),
        _write_file(
            tmp_path,
            "src/app/utils.py",
            "def helper():\n    return 'ok'\n",
        ),
        _write_file(
            tmp_path,
            "src/app/broken.py",
            "def broken(:\n    pass\n",
        ),
    ]

    graph = build_import_graph(paths, repo_root=tmp_path)
    section = _format_import_graph_section(graph)

    assert ("app.main", "app.utils") in {
        (edge.source_module, edge.target_module)
        for edge in graph.edges
    }
    assert len(graph.errors) == 1
    assert graph.errors[0].error_type == "SyntaxError"
    assert "- Analysis errors: 1" in section
    assert "Analysis errors:" in section
    assert "SyntaxError" in section


def test_import_graph_ignores_non_python_files(tmp_path: Path) -> None:
    paths = [
        _write_file(tmp_path, "src/app/main.py", "import os\n"),
        _write_file(tmp_path, "README.md", "import app.fake\n"),
        _write_file(tmp_path, "notes.txt", "from .missing import nope\n"),
    ]

    graph = build_import_graph(paths, repo_root=tmp_path)

    assert sorted(graph.modules) == ["app.main"]
    assert [reference.imported_module for reference in graph.external_imports] == ["os"]
    assert graph.unresolved_imports == ()
    assert graph.errors == ()


def test_import_graph_output_is_deterministic_for_source_path_order(tmp_path: Path) -> None:
    paths = [
        _write_file(tmp_path, "src/app/__init__.py", ""),
        _write_file(
            tmp_path,
            "src/app/main.py",
            "import os\n"
            "import app.utils\n"
            "from .missing import nope\n",
        ),
        _write_file(
            tmp_path,
            "src/app/utils.py",
            "import json\n",
        ),
    ]

    graph_from_normal_order = build_import_graph(paths, repo_root=tmp_path)
    graph_from_reversed_order = build_import_graph(tuple(reversed(paths)), repo_root=tmp_path)

    assert _graph_signature(graph_from_normal_order) == _graph_signature(
        graph_from_reversed_order
    )
    assert _format_import_graph_section(graph_from_normal_order) == _format_import_graph_section(
        graph_from_reversed_order
    )


def test_export_adapter_ignores_binary_errored_and_non_text_python_files(tmp_path: Path) -> None:
    good_path = _write_file(tmp_path, "src/app/main.py", "import os\n")
    binary_path = tmp_path / "src/app/binary.py"
    errored_path = tmp_path / "src/app/errored.py"
    non_text_path = tmp_path / "src/app/non_text.py"

    good_file = FileInfo(
        relative_path=Path("src/app/main.py"),
        absolute_path=good_path,
        is_text=True,
        is_binary=False,
        language="python",
        content="import os\n",
    )
    binary_file = FileInfo(
        relative_path=Path("src/app/binary.py"),
        absolute_path=binary_path,
        is_text=False,
        is_binary=True,
        language="python",
        content=None,
    )
    errored_file = FileInfo(
        relative_path=Path("src/app/errored.py"),
        absolute_path=errored_path,
        is_text=True,
        is_binary=False,
        language="python",
        content=None,
        error="Permission denied",
    )
    non_text_file = FileInfo(
        relative_path=Path("src/app/non_text.py"),
        absolute_path=non_text_path,
        is_text=False,
        is_binary=False,
        language="python",
        content=None,
    )

    assert _import_graph_export_source_path(good_file, tmp_path) == good_path
    assert _import_graph_export_source_path(binary_file, tmp_path) is None
    assert _import_graph_export_source_path(errored_file, tmp_path) is None
    assert _import_graph_export_source_path(non_text_file, tmp_path) is None

    graph = _build_import_graph_for_export(
        tmp_path,
        [binary_file, errored_file, good_file, non_text_file, "README.md"],
    )

    assert sorted(graph.modules) == ["app.main"]
    assert [reference.imported_module for reference in graph.external_imports] == ["os"]


def test_import_graph_module_does_not_require_external_graph_packages() -> None:
    source = Path("src/repocontext/import_graph.py").read_text(encoding="utf-8")

    assert "networkx" not in source
    assert "igraph" not in source
    assert "graphviz" not in source
