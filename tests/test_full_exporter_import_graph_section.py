from dataclasses import dataclass
from pathlib import Path

from repocontext.call_graph import CallEdge, CallGraph
from repocontext.import_graph import (
    ImportAnalysisError,
    ImportEdge,
    ImportGraph,
    ImportReference,
)

from repocontext.git import RepositoryInfo, TrackedFile
from repocontext.models import FileInfo

from repocontext.exporters.full import (
    _build_call_graph_for_export,
    _build_import_graph_for_export,
    _format_call_graph_section,
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




def test_render_full_export_appends_generated_import_graph_when_source_dump_mentions_same_heading(
    tmp_path: Path,
) -> None:
    context = _make_import_graph_full_export_context(tmp_path)

    heading_file = _write_import_graph_fixture_file(
        tmp_path,
        "docs/mentions-import-graph.md",
        "## Import Graph\nThis is only source content, not the generated section.\n",
    )

    context.repository_info.tracked_files.append(TrackedFile(path=heading_file.relative_path))
    context = create_full_export_context(
        context.repository_info,
        [*context.scanned_files, heading_file],
    )

    rendered = render_full_export(context)
    after_warnings = rendered.split("# Warnings", 1)[1]

    assert "## Import Graph" in after_warnings
    assert "Summary:" in after_warnings
    assert "- app.main -> app.utils" in after_warnings
    assert "External imports:\n- os" in after_warnings


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

def test_format_call_graph_section_summarizes_and_limits_edges() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="helper",
                callee_qualified_name="app.utils.helper",
                line_number=4,
                call_type="function",
                confidence="imported_local",
            ),
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="Path",
                callee_qualified_name="pathlib.Path",
                line_number=5,
                call_type="function",
                confidence="external",
            ),
        ]
    )

    section = _format_call_graph_section(
        graph,
        max_edges=1,
        max_external_edges=0,
    )

    assert section.startswith("## Call Graph")
    assert "- Call edges: 2" in section
    assert "- Local/internal calls: 1" in section
    assert "- External calls: 1" in section
    assert "- Ambiguous calls: 0" in section
    assert "- Unresolved calls: 0" in section
    assert (
        "Internal calls by caller:\n"
        "app.main.main (src/app/main.py)\n"
        "  - line 4: calls app.utils.helper [function, imported_local]"
    ) in section
    assert "External calls:\n- ... 1 more" in section
    assert "pathlib.Path" not in section

def test_format_call_graph_section_groups_multiple_edges_by_caller() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="prepare",
                callee_qualified_name="app.main.prepare",
                line_number=3,
                call_type="function",
                confidence="local",
            ),
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="run",
                callee_qualified_name="app.runner.run",
                line_number=4,
                call_type="function",
                confidence="imported_local",
            ),
            CallEdge(
                caller_file="src/app/worker.py",
                caller_name="work",
                caller_qualified_name="app.worker.work",
                callee_name="Path",
                callee_qualified_name="pathlib.Path",
                line_number=8,
                call_type="function",
                confidence="external",
            ),
        ]
    )

    section = _format_call_graph_section(graph)

    assert (
        "Internal calls by caller:\n"
        "app.main.main (src/app/main.py)\n"
        "  - line 3: calls app.main.prepare [function, local]\n"
        "  - line 4: calls app.runner.run [function, imported_local]"
    ) in section
    assert "app.worker.work (src/app/worker.py)" not in section
    assert (
        "External calls:\n"
        "- app.worker.work -> pathlib.Path (line 8, function, external)"
    ) in section

def test_format_call_graph_section_separates_and_limits_noisy_calls() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="helper",
                callee_qualified_name="app.helper",
                line_number=2,
                call_type="function",
                confidence="local",
            ),
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="Path",
                callee_qualified_name="pathlib.Path",
                line_number=3,
                call_type="function",
                confidence="external",
            ),
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="run",
                callee_qualified_name="subprocess.run",
                line_number=4,
                call_type="method",
                confidence="external",
            ),
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="maybe",
                callee_qualified_name=None,
                line_number=5,
                call_type="function",
                confidence="unresolved",
            ),
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="duplicate",
                callee_qualified_name=None,
                line_number=6,
                call_type="function",
                confidence="ambiguous",
            ),
        ]
    )

    section = _format_call_graph_section(
        graph,
        max_external_edges=1,
        max_unresolved_edges=1,
        max_ambiguous_edges=1,
    )

    assert "Internal calls by caller:" in section
    assert "app.main.main (src/app/main.py)" in section
    assert "  - line 2: calls app.helper [function, local]" in section

    assert "External calls:" in section
    assert "- app.main.main -> pathlib.Path (line 3, function, external)" in section
    assert "- app.main.main -> subprocess.run" not in section
    assert "- ... 1 more" in section

    assert "Ambiguous calls:" in section
    assert "- app.main.main -> duplicate (line 6, function, ambiguous)" in section

    assert "Unresolved calls:" in section
    assert "- app.main.main -> maybe (line 5, function, unresolved)" in section


def test_format_call_graph_section_shows_none_for_empty_noisy_groups() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/app/main.py",
                caller_name="main",
                caller_qualified_name="app.main.main",
                callee_name="helper",
                callee_qualified_name="app.helper",
                line_number=2,
                call_type="function",
                confidence="local",
            ),
        ]
    )

    section = _format_call_graph_section(graph)

    assert "External calls:\n- none" in section
    assert "Ambiguous calls:\n- none" in section
    assert "Unresolved calls:\n- none" in section

def test_format_call_graph_section_is_deterministic_for_unsorted_edges() -> None:
    first_graph = CallGraph(
        [
            CallEdge(
                caller_file="src/app/b.py",
                caller_name="run",
                caller_qualified_name="app.b.run",
                callee_name="Path",
                callee_qualified_name="pathlib.Path",
                line_number=8,
                call_type="function",
                confidence="external",
            ),
            CallEdge(
                caller_file="src/app/a.py",
                caller_name="main",
                caller_qualified_name="app.a.main",
                callee_name="helper",
                callee_qualified_name="app.a.helper",
                line_number=3,
                call_type="function",
                confidence="local",
            ),
            CallEdge(
                caller_file="src/app/a.py",
                caller_name="main",
                caller_qualified_name="app.a.main",
                callee_name="missing",
                callee_qualified_name=None,
                line_number=4,
                call_type="function",
                confidence="unresolved",
            ),
        ]
    )
    second_graph = CallGraph(list(reversed(first_graph.edges)))

    assert _format_call_graph_section(first_graph) == _format_call_graph_section(second_graph)


def test_format_call_graph_section_keeps_deterministic_group_order() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/app/z.py",
                caller_name="run",
                caller_qualified_name="app.z.run",
                callee_name="z_helper",
                callee_qualified_name="app.z.z_helper",
                line_number=5,
                call_type="function",
                confidence="local",
            ),
            CallEdge(
                caller_file="src/app/a.py",
                caller_name="main",
                caller_qualified_name="app.a.main",
                callee_name="a_helper",
                callee_qualified_name="app.a.a_helper",
                line_number=2,
                call_type="function",
                confidence="local",
            ),
        ]
    )

    section = _format_call_graph_section(graph)

    assert section.index("app.a.main (src/app/a.py)") < section.index("app.z.run (src/app/z.py)")

def test_build_call_graph_for_export_skips_syntax_error_python_files(
    tmp_path: Path,
) -> None:
    files = [
        _write_import_graph_fixture_file(tmp_path, "src/app/__init__.py", ""),
        _write_import_graph_fixture_file(
            tmp_path,
            "src/app/helpers.py",
            "def helper():\n"
            "    return 'ok'\n",
        ),
        _write_import_graph_fixture_file(
            tmp_path,
            "src/app/main.py",
            "from app.helpers import helper\n"
            "\n"
            "def main():\n"
            "    return helper()\n",
        ),
        _write_import_graph_fixture_file(
            tmp_path,
            "src/app/broken.py",
            "def broken(:\n"
            "    pass\n",
        ),
    ]

    import_graph = _build_import_graph_for_export(tmp_path, files)
    call_graph = _build_call_graph_for_export(
        tmp_path,
        files,
        import_graph=import_graph,
    )

    assert call_graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app/main.py",
            caller_name="main",
            caller_qualified_name="app.main.main",
            callee_name="helper",
            callee_qualified_name="app.helpers.helper",
            line_number=4,
            call_type="function",
            confidence="imported_local",
        )
    ]

    import_section = _format_import_graph_section(import_graph)
    assert "Analysis errors:" in import_section
    assert "SyntaxError" in import_section


def test_render_full_export_keeps_call_graph_when_one_python_file_has_syntax_error(
    tmp_path: Path,
) -> None:
    files = [
        _write_import_graph_fixture_file(tmp_path, "src/app/__init__.py", ""),
        _write_import_graph_fixture_file(
            tmp_path,
            "src/app/helpers.py",
            "def helper():\n"
            "    return 'ok'\n",
        ),
        _write_import_graph_fixture_file(
            tmp_path,
            "src/app/main.py",
            "from app.helpers import helper\n"
            "\n"
            "def main():\n"
            "    return helper()\n",
        ),
        _write_import_graph_fixture_file(
            tmp_path,
            "src/app/broken.py",
            "def broken(:\n"
            "    pass\n",
        ),
    ]

    repository_info = RepositoryInfo(
        name="example",
        root_path=tmp_path,
        is_current_directory_root=True,
        branch="main",
        commit_hash="a" * 40,
        short_commit_hash="aaaaaaa",
        remote_url=None,
        is_dirty=False,
        tracked_files=[TrackedFile(path=file_info.relative_path) for file_info in files],
        commit_metadata=None,
    )
    context = create_full_export_context(repository_info, files)

    rendered = render_full_export(context)

    assert "## Import Graph" in rendered
    assert "Analysis errors:" in rendered
    assert "SyntaxError" in rendered
    assert "## Call Graph" in rendered
    assert "Internal calls by caller:" in rendered
    assert "app.main.main (src/app/main.py)" in rendered
    assert (
        "  - line 4: calls app.helpers.helper "
        "[function, imported_local]"
    ) in rendered
    assert "Traceback" not in rendered


def test_render_full_export_call_graph_section_is_deterministic_for_file_order(
    tmp_path: Path,
) -> None:
    context = _make_call_graph_full_export_context(tmp_path)
    reversed_context = create_full_export_context(
        context.repository_info,
        tuple(reversed(context.scanned_files)),
        context.warnings,
    )

    assert render_full_export(context) == render_full_export(reversed_context)


def _make_call_graph_full_export_context(repo_root: Path):
    files = [
        _write_import_graph_fixture_file(repo_root, "src/app/__init__.py", ""),
        _write_import_graph_fixture_file(
            repo_root,
            "src/app/scanner.py",
            "def scan_single_file():\n"
            "    return None\n",
        ),
        _write_import_graph_fixture_file(
            repo_root,
            "src/app/main.py",
            "from app.scanner import scan_single_file\n"
            "\n"
            "def main():\n"
            "    return scan_single_file()\n",
        ),
        _write_import_graph_fixture_file(repo_root, "README.md", "# Example\n"),
    ]

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


def _rendered_call_graph_section(rendered_export: str) -> str:
    assert "## Call Graph" in rendered_export
    return rendered_export.split("## Call Graph", 1)[1]


def test_build_call_graph_for_export_uses_context_files_import_graph_and_symbols(
    tmp_path: Path,
) -> None:
    context = _make_call_graph_full_export_context(tmp_path)
    import_graph = _build_import_graph_for_export(
        context.repository_root,
        context.scanned_files,
    )

    call_graph = _build_call_graph_for_export(
        context.repository_root,
        context.scanned_files,
        import_graph=import_graph,
    )

    assert call_graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app/main.py",
            caller_name="main",
            caller_qualified_name="app.main.main",
            callee_name="scan_single_file",
            callee_qualified_name="app.scanner.scan_single_file",
            line_number=4,
            call_type="function",
            confidence="imported_local",
        )
    ]


def test_render_full_export_appends_call_graph_section_after_import_graph(
    tmp_path: Path,
) -> None:
    context = _make_call_graph_full_export_context(tmp_path)

    rendered = render_full_export(context)
    after_warnings = rendered.split("# Warnings", 1)[1]
    section = _rendered_call_graph_section(rendered)

    assert after_warnings.index("## Import Graph") < after_warnings.index("## Call Graph")
    assert "- Call edges: 1" in section
    assert "- Local/internal calls: 1" in section
    assert "app.main.main (src/app/main.py)" in section
    assert (
        "  - line 4: calls app.scanner.scan_single_file "
        "[function, imported_local]"
    ) in section


def test_write_full_export_persists_call_graph_section_to_full_txt(
    tmp_path: Path,
) -> None:
    context = _make_call_graph_full_export_context(tmp_path)

    output_path = write_full_export(context)

    content = output_path.read_text(encoding="utf-8")
    section = _rendered_call_graph_section(content)
    assert "- Call edges: 1" in section
    assert "app.main.main (src/app/main.py)" in section
    assert "  - line 4: calls app.scanner.scan_single_file" in section

