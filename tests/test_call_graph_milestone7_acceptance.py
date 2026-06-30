"""Milestone 7 acceptance coverage for static Python call graphs."""

from __future__ import annotations

from pathlib import Path

from repodossier.call_graph import CallEdge, CallGraph, parse_calls_from_source
from repodossier.exporters.full import (
    _format_call_graph_section,
    create_full_export_context,
    render_full_export,
)
from repodossier.git import RepositoryInfo, TrackedFile
from repodossier.import_graph import build_import_graph
from repodossier.models import FileInfo
from repodossier.symbols import build_symbol_index


def test_milestone7_acceptance_direct_function_call_is_resolved_locally() -> None:
    source = (
        "def helper():\n"
        "    return 'ok'\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/pkg/main.py",
        module_name="pkg.main",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="helper",
            callee_qualified_name="pkg.main.helper",
            line_number=5,
            call_type="function",
            confidence="local",
        )
    ]


def test_milestone7_acceptance_nested_function_calls_are_all_collected() -> None:
    source = (
        "def load_data():\n"
        "    return 'raw'\n"
        "\n"
        "def transform(value):\n"
        "    return value\n"
        "\n"
        "def main():\n"
        "    return transform(load_data())\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/pkg/main.py",
        module_name="pkg.main",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="load_data",
            callee_qualified_name="pkg.main.load_data",
            line_number=8,
            call_type="function",
            confidence="local",
        ),
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="transform",
            callee_qualified_name="pkg.main.transform",
            line_number=8,
            call_type="function",
            confidence="local",
        ),
    ]


def test_milestone7_acceptance_self_method_call_is_resolved_locally() -> None:
    source = (
        "class Scanner:\n"
        "    def scan(self):\n"
        "        return self.scan_file()\n"
        "\n"
        "    def scan_file(self):\n"
        "        return None\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/pkg/scanner.py",
        module_name="pkg.scanner",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/pkg/scanner.py",
            caller_name="Scanner.scan",
            caller_qualified_name="pkg.scanner.Scanner.scan",
            callee_name="scan_file",
            callee_qualified_name="pkg.scanner.Scanner.scan_file",
            line_number=3,
            call_type="method",
            confidence="local_method",
        )
    ]


def test_milestone7_acceptance_unknown_object_method_call_is_not_falsely_resolved() -> None:
    source = (
        "def main(result):\n"
        "    return result.to_dict()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/pkg/main.py",
        module_name="pkg.main",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="to_dict",
            callee_qualified_name=None,
            line_number=2,
            call_type="method",
            confidence="unresolved",
        )
    ]


def test_milestone7_acceptance_imported_local_function_call_is_resolved(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src" / "pkg"
    source_root.mkdir(parents=True)

    helper_path = source_root / "helpers.py"
    main_path = source_root / "main.py"

    helper_path.write_text(
        "def helper():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    main_source = (
        "from pkg.helpers import helper\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )
    main_path.write_text(main_source, encoding="utf-8")

    source_paths = (helper_path, main_path)
    import_graph = build_import_graph(source_paths, repo_root=tmp_path)
    symbol_index = build_symbol_index(source_paths, base_path=tmp_path)

    graph = parse_calls_from_source(
        main_source,
        source_path=main_path,
        module_name="pkg.main",
        symbol_index=symbol_index,
        import_graph=import_graph,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file=main_path.as_posix(),
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="helper",
            callee_qualified_name="pkg.helpers.helper",
            line_number=4,
            call_type="function",
            confidence="imported_local",
        )
    ]


def test_milestone7_acceptance_external_and_chained_calls_are_marked_conservatively() -> None:
    source = (
        "from pathlib import Path\n"
        "\n"
        "def main():\n"
        "    return Path('x').read_text()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/pkg/main.py",
        module_name="pkg.main",
        import_graph=object(),
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="Path",
            callee_qualified_name="pathlib.Path",
            line_number=4,
            call_type="function",
            confidence="external",
        ),
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="read_text",
            callee_qualified_name=None,
            line_number=4,
            call_type="method",
            confidence="unresolved_method",
        ),
    ]


def test_milestone7_acceptance_deduplicates_identical_same_line_call_edges() -> None:
    source = (
        "def helper():\n"
        "    return 'ok'\n"
        "\n"
        "def main():\n"
        "    helper(); helper()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/pkg/main.py",
        module_name="pkg.main",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="helper",
            callee_qualified_name="pkg.main.helper",
            line_number=5,
            call_type="function",
            confidence="local",
        )
    ]

def test_milestone7_quality_keeps_same_call_when_it_occurs_on_different_lines() -> None:
    source = (
        "def helper():\n"
        "    return 'ok'\n"
        "\n"
        "def main():\n"
        "    helper()\n"
        "    helper()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/pkg/main.py",
        module_name="pkg.main",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="helper",
            callee_qualified_name="pkg.main.helper",
            line_number=5,
            call_type="function",
            confidence="local",
        ),
        CallEdge(
            caller_file="src/pkg/main.py",
            caller_name="main",
            caller_qualified_name="pkg.main.main",
            callee_name="helper",
            callee_qualified_name="pkg.main.helper",
            line_number=6,
            call_type="function",
            confidence="local",
        ),
    ]


def test_milestone7_quality_full_export_does_not_duplicate_same_call_location(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src" / "pkg"
    source_root.mkdir(parents=True)

    helper_path = source_root / "helpers.py"
    main_path = source_root / "main.py"

    helper_source = (
        "def helper():\n"
        "    return 'ok'\n"
    )
    main_source = (
        "from pkg.helpers import helper\n"
        "\n"
        "def main():\n"
        "    helper(); helper()\n"
        "    helper()\n"
    )

    helper_path.write_text(helper_source, encoding="utf-8")
    main_path.write_text(main_source, encoding="utf-8")

    files = [
        FileInfo(
            relative_path=Path("src/pkg/helpers.py"),
            absolute_path=helper_path,
            size_bytes=len(helper_source.encode("utf-8")),
            is_text=True,
            is_binary=False,
            language="python",
            line_count=2,
            estimated_tokens=10,
            content=helper_source,
        ),
        FileInfo(
            relative_path=Path("src/pkg/main.py"),
            absolute_path=main_path,
            size_bytes=len(main_source.encode("utf-8")),
            is_text=True,
            is_binary=False,
            language="python",
            line_count=5,
            estimated_tokens=20,
            content=main_source,
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
        tracked_files=[
            TrackedFile(path=Path("src/pkg/helpers.py")),
            TrackedFile(path=Path("src/pkg/main.py")),
        ],
        commit_metadata=None,
    )

    context = create_full_export_context(repository_info, files)
    rendered = render_full_export(context)

    assert rendered.count(
        "  - line 4: calls pkg.helpers.helper [function, imported_local]"
    ) == 1
    assert rendered.count(
        "  - line 5: calls pkg.helpers.helper [function, imported_local]"
    ) == 1


def test_milestone7_acceptance_full_export_contains_stable_call_graph_section(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src" / "pkg"
    source_root.mkdir(parents=True)

    init_path = source_root / "__init__.py"
    helper_path = source_root / "helpers.py"
    main_path = source_root / "main.py"

    init_source = ""
    helper_source = (
        "def helper():\n"
        "    return 'ok'\n"
    )
    main_source = (
        "from pkg.helpers import helper\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )

    init_path.write_text(init_source, encoding="utf-8")
    helper_path.write_text(helper_source, encoding="utf-8")
    main_path.write_text(main_source, encoding="utf-8")

    files = [
        FileInfo(
            relative_path=Path("src/pkg/__init__.py"),
            absolute_path=init_path,
            size_bytes=len(init_source.encode("utf-8")),
            is_text=True,
            is_binary=False,
            language="python",
            line_count=0,
            estimated_tokens=0,
            content=init_source,
        ),
        FileInfo(
            relative_path=Path("src/pkg/helpers.py"),
            absolute_path=helper_path,
            size_bytes=len(helper_source.encode("utf-8")),
            is_text=True,
            is_binary=False,
            language="python",
            line_count=2,
            estimated_tokens=10,
            content=helper_source,
        ),
        FileInfo(
            relative_path=Path("src/pkg/main.py"),
            absolute_path=main_path,
            size_bytes=len(main_source.encode("utf-8")),
            is_text=True,
            is_binary=False,
            language="python",
            line_count=4,
            estimated_tokens=20,
            content=main_source,
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
        tracked_files=[
            TrackedFile(path=Path("src/pkg/__init__.py")),
            TrackedFile(path=Path("src/pkg/helpers.py")),
            TrackedFile(path=Path("src/pkg/main.py")),
        ],
        commit_metadata=None,
    )

    context = create_full_export_context(repository_info, files)
    rendered = render_full_export(context)

    assert "## Call Graph" in rendered
    assert "Internal calls by caller:" in rendered
    assert "pkg.main.main (src/pkg/main.py)" in rendered
    assert "  - line 4: calls pkg.helpers.helper [function, imported_local]" in rendered
    assert rendered.count("pkg.main.main (src/pkg/main.py)") == 1

def test_milestone7_quality_limits_internal_call_graph_export_by_default() -> None:
    graph = CallGraph(
        [
            CallEdge(
                caller_file="src/pkg/main.py",
                caller_name="main",
                caller_qualified_name="pkg.main.main",
                callee_name=f"helper_{index:03d}",
                callee_qualified_name=f"pkg.main.helper_{index:03d}",
                line_number=index + 1,
                call_type="function",
                confidence="local",
            )
            for index in range(205)
        ]
    )

    section = _format_call_graph_section(graph)

    assert "- Call edges: 205" in section
    assert "- Local/internal calls: 205" in section
    assert section.count("  - line ") == 200
    assert "helper_199" in section
    assert "helper_200" not in section
    assert "- ... 5 more" in section


def test_milestone7_quality_limits_noisy_call_graph_export_groups_by_default() -> None:
    edges = []

    for index in range(30):
        edges.append(
            CallEdge(
                caller_file="src/pkg/main.py",
                caller_name="main",
                caller_qualified_name="pkg.main.main",
                callee_name=f"external_{index:03d}",
                callee_qualified_name=f"external.lib.external_{index:03d}",
                line_number=index + 1,
                call_type="function",
                confidence="external",
            )
        )
        edges.append(
            CallEdge(
                caller_file="src/pkg/main.py",
                caller_name="main",
                caller_qualified_name="pkg.main.main",
                callee_name=f"ambiguous_{index:03d}",
                callee_qualified_name=None,
                line_number=100 + index,
                call_type="function",
                confidence="ambiguous",
            )
        )
        edges.append(
            CallEdge(
                caller_file="src/pkg/main.py",
                caller_name="main",
                caller_qualified_name="pkg.main.main",
                callee_name=f"unresolved_{index:03d}",
                callee_qualified_name=None,
                line_number=200 + index,
                call_type="function",
                confidence="unresolved",
            )
        )

    section = _format_call_graph_section(CallGraph(edges))

    assert "- External calls: 30" in section
    assert "- Ambiguous calls: 30" in section
    assert "- Unresolved calls: 30" in section

    assert "external_024" in section
    assert "external_025" not in section
    assert "ambiguous_024" in section
    assert "ambiguous_025" not in section
    assert "unresolved_024" in section
    assert "unresolved_025" not in section

    assert section.count("- ... 5 more") == 3

