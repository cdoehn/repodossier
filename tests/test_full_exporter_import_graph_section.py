from dataclasses import dataclass
from pathlib import Path

from repocontext.import_graph import (
    ImportAnalysisError,
    ImportEdge,
    ImportGraph,
    ImportReference,
)

from repocontext.git import RepositoryInfo, TrackedFile
from repocontext.models import FileInfo

from repocontext.exporters.full import (
    _build_import_graph_for_export,
    _format_import_graph_section,
    create_full_export_context,
    render_full_export,
    write_full_export,
)


@dataclass
class FakeExportFile:
    relative_path: str




def test_format_import_graph_section_sorts_dependencies_imports_and_errors() -> None:
    graph = ImportGraph(
        modules={
            "app.alpha": "src/app/alpha.py",
            "app.beta": "src/app/beta.py",
            "app.main": "src/app/main.py",
            "app.zeta": "src/app/zeta.py",
        },
        edges=[
            ImportEdge(
                source_module="app.zeta",
                target_module="app.beta",
                source_path="src/app/zeta.py",
                target_path="src/app/beta.py",
                import_type="import",
                line_number=9,
            ),
            ImportEdge(
                source_module="app.main",
                target_module="app.alpha",
                source_path="src/app/main.py",
                target_path="src/app/alpha.py",
                import_type="import",
                line_number=2,
            ),
            ImportEdge(
                source_module="app.main",
                target_module="app.beta",
                source_path="src/app/main.py",
                target_path="src/app/beta.py",
                import_type="from",
                imported_name="Beta",
                line_number=1,
            ),
        ],
        external_imports=[
            ImportReference(
                source_path="src/app/main.py",
                source_module="app.main",
                imported_module="zlib",
                import_type="import",
                line_number=3,
                is_local=False,
            ),
            ImportReference(
                source_path="src/app/main.py",
                source_module="app.main",
                imported_module="argparse",
                import_type="import",
                line_number=1,
                is_local=False,
            ),
        ],
        unresolved_imports=[
            ImportReference(
                source_path="src/app/zeta.py",
                source_module="app.zeta",
                imported_module="missing_z",
                imported_name="Thing",
                import_type="from",
                level=1,
                line_number=7,
                is_relative=True,
                is_local=False,
            ),
            ImportReference(
                source_path="src/app/main.py",
                source_module="app.main",
                imported_module="missing_a",
                imported_name="Thing",
                import_type="from",
                level=1,
                line_number=5,
                is_relative=True,
                is_local=False,
            ),
        ],
        errors=[
            ImportAnalysisError(
                source_path="src/app/zeta.py",
                error_type="SyntaxError",
                message="z error",
                line_number=1,
            ),
            ImportAnalysisError(
                source_path="src/app/alpha.py",
                error_type="SyntaxError",
                message="a error",
                line_number=1,
            ),
        ],
    )

    section = _format_import_graph_section(graph)

    assert section.index("- app.main -> app.alpha") < section.index("- app.main -> app.beta")
    assert section.index("- app.main -> app.beta") < section.index("- app.zeta -> app.beta")
    assert section.index("- argparse") < section.index("- zlib")
    assert section.index("- app.main: missing_a.Thing") < section.index("- app.zeta: missing_z.Thing")
    assert section.index("src/app/alpha.py: SyntaxError: a error") < section.index(
        "src/app/zeta.py: SyntaxError: z error"
    )


def test_format_import_graph_section_limits_large_lists() -> None:
    graph = ImportGraph(
        modules={
            "app.main": "src/app/main.py",
            "app.one": "src/app/one.py",
            "app.two": "src/app/two.py",
            "app.three": "src/app/three.py",
        },
        edges=[
            ImportEdge(
                source_module="app.main",
                target_module="app.one",
                source_path="src/app/main.py",
                target_path="src/app/one.py",
                import_type="import",
                line_number=1,
            ),
            ImportEdge(
                source_module="app.main",
                target_module="app.three",
                source_path="src/app/main.py",
                target_path="src/app/three.py",
                import_type="import",
                line_number=3,
            ),
            ImportEdge(
                source_module="app.main",
                target_module="app.two",
                source_path="src/app/main.py",
                target_path="src/app/two.py",
                import_type="import",
                line_number=2,
            ),
        ],
        external_imports=[
            ImportReference(
                source_path="src/app/main.py",
                source_module="app.main",
                imported_module="argparse",
                import_type="import",
                line_number=1,
                is_local=False,
            ),
            ImportReference(
                source_path="src/app/main.py",
                source_module="app.main",
                imported_module="json",
                import_type="import",
                line_number=2,
                is_local=False,
            ),
            ImportReference(
                source_path="src/app/main.py",
                source_module="app.main",
                imported_module="pathlib",
                import_type="import",
                line_number=3,
                is_local=False,
            ),
        ],
    )

    section = _format_import_graph_section(graph, max_edges=2, max_imports=2)

    assert "- app.main -> app.one" in section
    assert "- app.main -> app.three" in section
    assert "- app.main -> app.two" not in section
    assert "- argparse" in section
    assert "- json" in section
    assert "- pathlib" not in section
    assert section.count("- ... 1 more") >= 2




def _write_import_graph_fixture_file(
    repo_root: Path,
    relative_path: str,
    content: str,
) -> FileInfo:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    suffix = path.suffix.lower()
    if suffix == ".py":
        language = "python"
    elif suffix == ".md":
        language = "markdown"
    else:
        language = "text"

    return FileInfo(
        relative_path=Path(relative_path),
        absolute_path=path,
        is_text=True,
        is_binary=False,
        language=language,
        line_count=len(content.splitlines()),
        estimated_tokens=(len(content) + 3) // 4 if content else 0,
        content=content,
    )


def _make_import_graph_full_export_context(
    repo_root: Path,
    *,
    reverse_files: bool = False,
):
    files = [
        _write_import_graph_fixture_file(repo_root, "src/app/__init__.py", ""),
        _write_import_graph_fixture_file(
            repo_root,
            "src/app/main.py",
            "import os\n"
            "import app.utils\n"
            "from .missing import nope\n",
        ),
        _write_import_graph_fixture_file(
            repo_root,
            "src/app/utils.py",
            "def helper():\n"
            "    return 'ok'\n",
        ),
        _write_import_graph_fixture_file(repo_root, "README.md", "# Example\n"),
    ]

    if reverse_files:
        files = list(reversed(files))

    repository_info = RepositoryInfo(
        name="example",
        root_path=repo_root,
        is_current_directory_root=True,
        branch="main",
        commit_hash="a" * 40,
        short_commit_hash="aaaaaaa",
        remote_url=None,
        is_dirty=False,
        tracked_files=[TrackedFile(path=file_info.relative_path) for file_info in files],
        commit_metadata=None,
    )

    return create_full_export_context(repository_info, files)


def _rendered_import_graph_section(rendered_export: str) -> str:
    assert "## Import Graph" in rendered_export
    return rendered_export.split("## Import Graph", 1)[1]


def test_render_full_export_includes_import_graph_section_from_context_files(
    tmp_path: Path,
) -> None:
    context = _make_import_graph_full_export_context(tmp_path)

    rendered = render_full_export(context)
    section = _rendered_import_graph_section(rendered)

    assert "Summary:" in section
    assert "- Local modules: 3" in section
    assert "- Local dependencies: 1" in section
    assert "- External imports: 1" in section
    assert "- Unresolved imports: 1" in section
    assert "Local dependencies:\n- app.main -> app.utils" in section
    assert "External imports:\n- os" in section
    assert "Unresolved imports:\n- app.main: missing.nope" in section


def test_write_full_export_persists_import_graph_section_to_full_txt(
    tmp_path: Path,
) -> None:
    context = _make_import_graph_full_export_context(tmp_path)

    output_path = write_full_export(context)

    assert output_path == tmp_path / "full.txt"
    content = output_path.read_text(encoding="utf-8")
    section = _rendered_import_graph_section(content)
    assert "- app.main -> app.utils" in section
    assert "- os" in section
    assert "- app.main: missing.nope" in section


def test_render_full_export_import_graph_output_is_deterministic_for_file_order(
    tmp_path: Path,
) -> None:
    normal_context = _make_import_graph_full_export_context(tmp_path)
    reversed_context = _make_import_graph_full_export_context(
        tmp_path,
        reverse_files=True,
    )

    assert render_full_export(normal_context) == render_full_export(reversed_context)


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
