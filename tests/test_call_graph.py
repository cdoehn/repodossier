import ast

from repodossier.call_graph import (
    CallEdge,
    CallGraph,
    ImportAlias,
    build_call_graph_from_ast,
    collect_import_aliases_from_source,
    parse_calls_from_source,
    resolve_import_aliases_with_import_graph,
)
from repodossier.import_graph import build_import_graph
from repodossier.symbols import FileSymbolIndex, SymbolInfo


def test_call_edge_exposes_stable_caller_and_callee_keys():
    edge = CallEdge(
        caller_file="repodossier/exporter.py",
        caller_name="export",
        caller_qualified_name="repodossier.exporter.export",
        callee_name="render",
        callee_qualified_name="repodossier.exporter.render",
        line_number=12,
        call_type="function",
        confidence="local",
    )

    assert edge.caller_key == "repodossier.exporter.export"
    assert edge.callee_key == "repodossier.exporter.render"
    assert edge.to_dict() == {
        "caller_file": "repodossier/exporter.py",
        "caller_name": "export",
        "caller_qualified_name": "repodossier.exporter.export",
        "callee_name": "render",
        "callee_qualified_name": "repodossier.exporter.render",
        "line_number": 12,
        "call_type": "function",
        "confidence": "local",
    }


def test_call_graph_deduplicates_identical_edges():
    edge = CallEdge(
        caller_file="repodossier/cli.py",
        caller_name="main",
        caller_qualified_name="repodossier.cli.main",
        callee_name="run",
        callee_qualified_name="repodossier.cli.run",
        line_number=20,
        call_type="function",
        confidence="local",
    )
    graph = CallGraph()

    assert graph.add_edge(edge) is True
    assert graph.add_edge(edge) is False

    assert graph.edges == [edge]
    assert graph.sorted_edges() == [edge]


def test_call_graph_returns_edges_in_deterministic_order():
    later_edge = CallEdge(
        caller_file="b.py",
        caller_name="main",
        caller_qualified_name="b.main",
        callee_name="z",
        line_number=30,
        call_type="function",
        confidence="unresolved",
    )
    earlier_edge = CallEdge(
        caller_file="a.py",
        caller_name="main",
        caller_qualified_name="a.main",
        callee_name="a",
        line_number=10,
        call_type="function",
        confidence="unresolved",
    )
    middle_edge = CallEdge(
        caller_file="a.py",
        caller_name="main",
        caller_qualified_name="a.main",
        callee_name="b",
        line_number=20,
        call_type="function",
        confidence="unresolved",
    )

    graph = CallGraph([later_edge, middle_edge, earlier_edge])

    assert graph.sorted_edges() == [earlier_edge, middle_edge, later_edge]
    assert graph.to_dict()["edges"][0]["callee_name"] == "a"


def test_call_graph_groups_outgoing_and_incoming_edges():
    first = CallEdge(
        caller_file="repodossier/cli.py",
        caller_name="main",
        caller_qualified_name="repodossier.cli.main",
        callee_name="parse_args",
        callee_qualified_name="repodossier.cli.parse_args",
        line_number=12,
        call_type="function",
        confidence="local",
    )
    second = CallEdge(
        caller_file="repodossier/cli.py",
        caller_name="main",
        caller_qualified_name="repodossier.cli.main",
        callee_name="run_export",
        callee_qualified_name="repodossier.exporter.run_export",
        line_number=18,
        call_type="function",
        confidence="imported_local",
    )
    graph = CallGraph([second, first])

    assert graph.get_calls_from("repodossier.cli.main") == (first, second)
    assert graph.get_callers_of("repodossier.cli.parse_args") == (first,)
    assert graph.callees_by_symbol["repodossier.cli.main"] == (first, second)
    assert graph.callers_by_symbol["repodossier.exporter.run_export"] == (second,)


def test_call_graph_text_output_is_grouped_and_stable():
    graph = CallGraph(
        [
            CallEdge(
                caller_file="repodossier/cli.py",
                caller_name="main",
                caller_qualified_name="repodossier.cli.main",
                callee_name="run",
                callee_qualified_name="repodossier.cli.run",
                line_number=22,
                call_type="function",
                confidence="local",
            ),
            CallEdge(
                caller_file="repodossier/cli.py",
                caller_name="main",
                caller_qualified_name="repodossier.cli.main",
                callee_name="parse_args",
                callee_qualified_name="repodossier.cli.parse_args",
                line_number=10,
                call_type="function",
                confidence="local",
            ),
        ]
    )

    assert graph.to_text() == (
        "repodossier.cli.main (repodossier/cli.py)\n"
        "  - line 10: calls repodossier.cli.parse_args [function, local]\n"
        "  - line 22: calls repodossier.cli.run [function, local]"
    )


def test_empty_call_graph_text_is_explicit():
    assert CallGraph().to_text() == "No call graph edges found."

def test_parse_calls_from_source_detects_direct_function_call():
    source = (
        "def helper():\n"
        "    return 1\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="helper",
            callee_qualified_name="app.helper",
            line_number=5,
            call_type="function",
            confidence="local",
        )
    ]


def test_parse_calls_from_source_tracks_module_level_caller_context():
    source = (
        "initialize()\n"
        "\n"
        "def main():\n"
        "    run()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="<module>",
            caller_qualified_name="app.<module>",
            callee_name="initialize",
            callee_qualified_name=None,
            line_number=1,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="run",
            callee_qualified_name=None,
            line_number=4,
            call_type="function",
            confidence="unresolved",
        ),
    ]


def test_parse_calls_from_source_tracks_method_caller_context():
    source = (
        "class Service:\n"
        "    def run(self):\n"
        "        helper()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="Service.run",
            caller_qualified_name="app.Service.run",
            callee_name="helper",
            callee_qualified_name=None,
            line_number=3,
            call_type="function",
            confidence="unresolved",
        )
    ]



def test_parse_calls_from_source_detects_nested_function_calls():
    source = (
        "def main(raw):\n"
        "    return transform(load_data(raw))\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="load_data",
            callee_qualified_name=None,
            line_number=2,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="transform",
            callee_qualified_name=None,
            line_number=2,
            call_type="function",
            confidence="unresolved",
        ),
    ]


def test_parse_calls_from_source_detects_multiple_nested_function_calls_in_expression():
    source = (
        "def main(raw):\n"
        "    value = validate(parse(raw))\n"
        "    return finalize(value)\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="parse",
            callee_qualified_name=None,
            line_number=2,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="validate",
            callee_qualified_name=None,
            line_number=2,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="finalize",
            callee_qualified_name=None,
            line_number=3,
            call_type="function",
            confidence="unresolved",
        ),
    ]


def test_parse_calls_from_source_detects_multiple_module_level_calls():
    source = (
        "setup_logging()\n"
        "main()\n"
        "cli()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="<module>",
            caller_qualified_name="app.<module>",
            callee_name="setup_logging",
            callee_qualified_name=None,
            line_number=1,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="<module>",
            caller_qualified_name="app.<module>",
            callee_name="main",
            callee_qualified_name=None,
            line_number=2,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="<module>",
            caller_qualified_name="app.<module>",
            callee_name="cli",
            callee_qualified_name=None,
            line_number=3,
            call_type="function",
            confidence="unresolved",
        ),
    ]

def test_parse_calls_from_source_detects_attribute_method_call_without_local_resolution():
    source = (
        "def main():\n"
        "    service.run()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="run",
            callee_qualified_name=None,
            line_number=2,
            call_type="method",
            confidence="unresolved",
        )
    ]

def test_parse_calls_from_source_detects_several_attribute_method_calls():
    source = (
        "def main(result, scanner):\n"
        "    scanner.scan()\n"
        "    result.to_dict()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="scan",
            callee_qualified_name=None,
            line_number=2,
            call_type="method",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="to_dict",
            callee_qualified_name=None,
            line_number=3,
            call_type="method",
            confidence="unresolved",
        ),
    ]


def test_parse_calls_from_source_keeps_function_and_method_calls_distinct():
    source = (
        "def main(service):\n"
        "    prepare()\n"
        "    service.run()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="prepare",
            callee_qualified_name=None,
            line_number=2,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="run",
            callee_qualified_name=None,
            line_number=3,
            call_type="method",
            confidence="unresolved",
        ),
    ]

def test_parse_calls_from_source_resolves_self_method_call_to_current_class():
    source = (
        "class Scanner:\n"
        "    def scan(self):\n"
        "        self.scan_file()\n"
        "\n"
        "    def scan_file(self):\n"
        "        pass\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/scanner.py",
        module_name="app.scanner",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/scanner.py",
            caller_name="Scanner.scan",
            caller_qualified_name="app.scanner.Scanner.scan",
            callee_name="scan_file",
            callee_qualified_name="app.scanner.Scanner.scan_file",
            line_number=3,
            call_type="method",
            confidence="local_method",
        )
    ]


def test_parse_calls_from_source_resolves_private_self_method_call_to_current_class():
    source = (
        "class Scanner:\n"
        "    def scan(self):\n"
        "        self._estimate_tokens()\n"
        "\n"
        "    def _estimate_tokens(self):\n"
        "        pass\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/scanner.py",
        module_name="app.scanner",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/scanner.py",
            caller_name="Scanner.scan",
            caller_qualified_name="app.scanner.Scanner.scan",
            callee_name="_estimate_tokens",
            callee_qualified_name="app.scanner.Scanner._estimate_tokens",
            line_number=3,
            call_type="method",
            confidence="local_method",
        )
    ]


def test_parse_calls_from_source_does_not_resolve_non_self_method_call_as_local_method():
    source = (
        "class Scanner:\n"
        "    def scan(self, other):\n"
        "        other.scan_file()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/scanner.py",
        module_name="app.scanner",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/scanner.py",
            caller_name="Scanner.scan",
            caller_qualified_name="app.scanner.Scanner.scan",
            callee_name="scan_file",
            callee_qualified_name=None,
            line_number=3,
            call_type="method",
            confidence="unresolved",
        )
    ]

def test_parse_calls_from_source_resolves_cls_method_call_to_current_class():
    source = (
        "class Config:\n"
        "    @classmethod\n"
        "    def load(cls):\n"
        "        return cls.from_path()\n"
        "\n"
        "    @classmethod\n"
        "    def from_path(cls):\n"
        "        return cls()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/config.py",
        module_name="app.config",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/config.py",
            caller_name="Config.from_path",
            caller_qualified_name="app.config.Config.from_path",
            callee_name="cls",
            callee_qualified_name=None,
            line_number=8,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/config.py",
            caller_name="Config.load",
            caller_qualified_name="app.config.Config.load",
            callee_name="from_path",
            callee_qualified_name="app.config.Config.from_path",
            line_number=4,
            call_type="method",
            confidence="local_method",
        ),
    ]


def test_parse_calls_from_source_resolves_class_name_method_call_for_known_class():
    source = (
        "class Config:\n"
        "    def load(self):\n"
        "        return Config.from_path()\n"
        "\n"
        "    @staticmethod\n"
        "    def from_path():\n"
        "        return Config()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/config.py",
        module_name="app.config",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/config.py",
            caller_name="Config.from_path",
            caller_qualified_name="app.config.Config.from_path",
            callee_name="Config",
            callee_qualified_name=None,
            line_number=7,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/config.py",
            caller_name="Config.load",
            caller_qualified_name="app.config.Config.load",
            callee_name="from_path",
            callee_qualified_name="app.config.Config.from_path",
            line_number=3,
            call_type="method",
            confidence="local_method",
        ),
    ]


def test_parse_calls_from_source_resolves_other_known_class_method_call():
    source = (
        "class Factory:\n"
        "    @staticmethod\n"
        "    def create():\n"
        "        return object()\n"
        "\n"
        "class Service:\n"
        "    def build(self):\n"
        "        return Factory.create()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/service.py",
        module_name="app.service",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/service.py",
            caller_name="Factory.create",
            caller_qualified_name="app.service.Factory.create",
            callee_name="object",
            callee_qualified_name=None,
            line_number=4,
            call_type="function",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/service.py",
            caller_name="Service.build",
            caller_qualified_name="app.service.Service.build",
            callee_name="create",
            callee_qualified_name="app.service.Factory.create",
            line_number=8,
            call_type="method",
            confidence="local_method",
        ),
    ]


def test_parse_calls_from_source_does_not_resolve_unknown_class_name_method_call():
    source = (
        "class Service:\n"
        "    def build(self):\n"
        "        return MissingFactory.create()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/service.py",
        module_name="app.service",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/service.py",
            caller_name="Service.build",
            caller_qualified_name="app.service.Service.build",
            callee_name="create",
            callee_qualified_name=None,
            line_number=3,
            call_type="method",
            confidence="unresolved",
        )
    ]

def test_parse_calls_from_source_marks_chained_method_call_conservatively():
    source = (
        "def main(path):\n"
        "    return path.read_text().splitlines()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="read_text",
            callee_qualified_name=None,
            line_number=2,
            call_type="method",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="splitlines",
            callee_qualified_name=None,
            line_number=2,
            call_type="method",
            confidence="unresolved_method",
        ),
    ]


def test_parse_calls_from_source_marks_chained_call_after_unknown_method_conservatively():
    source = (
        "def main(scanner):\n"
        "    return scanner.scan().to_export()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="scan",
            callee_qualified_name=None,
            line_number=2,
            call_type="method",
            confidence="unresolved",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="to_export",
            callee_qualified_name=None,
            line_number=2,
            call_type="method",
            confidence="unresolved_method",
        ),
    ]


def test_parse_calls_from_source_keeps_self_call_local_inside_chain_but_chain_unresolved():
    source = (
        "class Loader:\n"
        "    def run(self):\n"
        "        return self.load().normalize()\n"
        "\n"
        "    def load(self):\n"
        "        return self\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/loader.py",
        module_name="app.loader",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/loader.py",
            caller_name="Loader.run",
            caller_qualified_name="app.loader.Loader.run",
            callee_name="load",
            callee_qualified_name="app.loader.Loader.load",
            line_number=3,
            call_type="method",
            confidence="local_method",
        ),
        CallEdge(
            caller_file="src/loader.py",
            caller_name="Loader.run",
            caller_qualified_name="app.loader.Loader.run",
            callee_name="normalize",
            callee_qualified_name=None,
            line_number=3,
            call_type="method",
            confidence="unresolved_method",
        ),
    ]

def test_parse_calls_from_source_keeps_unknown_direct_function_call_unresolved():
    source = (
        "def main():\n"
        "    return missing_helper()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="missing_helper",
            callee_qualified_name=None,
            line_number=2,
            call_type="function",
            confidence="unresolved",
        )
    ]


def test_parse_calls_from_source_resolves_async_local_function_call():
    source = (
        "async def load_data():\n"
        "    return 1\n"
        "\n"
        "def main():\n"
        "    return load_data()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="load_data",
            callee_qualified_name="app.load_data",
            line_number=5,
            call_type="function",
            confidence="local",
        )
    ]


def test_build_call_graph_from_ast_can_use_existing_symbol_index_for_local_functions():
    source = (
        "def main():\n"
        "    return helper()\n"
    )
    tree = ast.parse(source, filename="src/app.py")
    symbol_index = [
        FileSymbolIndex(
            file_path="src/app.py",
            symbols=[
                SymbolInfo(
                    name="helper",
                    kind="function",
                    file_path="src/app.py",
                    line_start=10,
                )
            ],
        )
    ]

    graph = build_call_graph_from_ast(
        tree,
        source_path="src/app.py",
        module_name="app",
        symbol_index=symbol_index,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="helper",
            callee_qualified_name="app.helper",
            line_number=2,
            call_type="function",
            confidence="local",
        )
    ]

def test_parse_calls_from_source_marks_duplicate_local_function_name_ambiguous():
    source = (
        "def helper():\n"
        "    return 1\n"
        "\n"
        "def helper():\n"
        "    return 2\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="helper",
            callee_qualified_name=None,
            line_number=8,
            call_type="function",
            confidence="ambiguous",
        )
    ]


def test_parse_calls_from_source_marks_duplicate_self_method_name_ambiguous():
    source = (
        "class Exporter:\n"
        "    def export(self):\n"
        "        self.render()\n"
        "\n"
        "    def render(self):\n"
        "        return 'a'\n"
        "\n"
        "    def render(self):\n"
        "        return 'b'\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/exporter.py",
        module_name="app.exporter",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/exporter.py",
            caller_name="Exporter.export",
            caller_qualified_name="app.exporter.Exporter.export",
            callee_name="render",
            callee_qualified_name=None,
            line_number=3,
            call_type="method",
            confidence="ambiguous",
        )
    ]


def test_parse_calls_from_source_keeps_missing_self_method_unresolved():
    source = (
        "class Exporter:\n"
        "    def export(self):\n"
        "        self.render()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/exporter.py",
        module_name="app.exporter",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/exporter.py",
            caller_name="Exporter.export",
            caller_qualified_name="app.exporter.Exporter.export",
            callee_name="render",
            callee_qualified_name=None,
            line_number=3,
            call_type="method",
            confidence="unresolved",
        )
    ]


def test_build_call_graph_from_ast_uses_symbol_index_for_same_class_method_resolution():
    source = (
        "class Exporter:\n"
        "    def export(self):\n"
        "        self.render()\n"
    )
    tree = ast.parse(source, filename="src/exporter.py")
    symbol_index = [
        FileSymbolIndex(
            file_path="src/exporter.py",
            symbols=[
                SymbolInfo(
                    name="render",
                    kind="method",
                    file_path="src/exporter.py",
                    line_start=20,
                    parent="Exporter",
                )
            ],
        )
    ]

    graph = build_call_graph_from_ast(
        tree,
        source_path="src/exporter.py",
        module_name="app.exporter",
        symbol_index=symbol_index,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/exporter.py",
            caller_name="Exporter.export",
            caller_qualified_name="app.exporter.Exporter.export",
            callee_name="render",
            callee_qualified_name="app.exporter.Exporter.render",
            line_number=3,
            call_type="method",
            confidence="local_method",
        )
    ]

def test_collect_import_aliases_from_source_collects_plain_import():
    aliases = collect_import_aliases_from_source(
        "import pathlib\n",
        source_path="src/app.py",
    )

    assert aliases == {
        "pathlib": ImportAlias(
            local_name="pathlib",
            qualified_name="pathlib",
            module_name="pathlib",
            imported_name=None,
            alias=None,
            import_type="import",
            level=0,
            line_number=1,
            is_relative=False,
        )
    }


def test_collect_import_aliases_from_source_collects_import_as_alias():
    aliases = collect_import_aliases_from_source(
        "import pathlib as pl\n",
        source_path="src/app.py",
    )

    assert aliases == {
        "pl": ImportAlias(
            local_name="pl",
            qualified_name="pathlib",
            module_name="pathlib",
            imported_name=None,
            alias="pl",
            import_type="import",
            level=0,
            line_number=1,
            is_relative=False,
        )
    }


def test_collect_import_aliases_from_source_collects_from_import_name():
    aliases = collect_import_aliases_from_source(
        "from repodossier.scanner import scan_single_file\n",
        source_path="src/app.py",
    )

    assert aliases == {
        "scan_single_file": ImportAlias(
            local_name="scan_single_file",
            qualified_name="repodossier.scanner.scan_single_file",
            module_name="repodossier.scanner",
            imported_name="scan_single_file",
            alias=None,
            import_type="from",
            level=0,
            line_number=1,
            is_relative=False,
        )
    }


def test_collect_import_aliases_from_source_collects_from_import_as_alias():
    aliases = collect_import_aliases_from_source(
        "from repodossier.scanner import scan_single_file as scan\n",
        source_path="src/app.py",
    )

    assert aliases == {
        "scan": ImportAlias(
            local_name="scan",
            qualified_name="repodossier.scanner.scan_single_file",
            module_name="repodossier.scanner",
            imported_name="scan_single_file",
            alias="scan",
            import_type="from",
            level=0,
            line_number=1,
            is_relative=False,
        )
    }


def test_collect_import_aliases_from_source_collects_relative_from_import():
    aliases = collect_import_aliases_from_source(
        "from .scanner import scan_single_file\n",
        source_path="src/app.py",
    )

    assert aliases == {
        "scan_single_file": ImportAlias(
            local_name="scan_single_file",
            qualified_name=".scanner.scan_single_file",
            module_name=".scanner",
            imported_name="scan_single_file",
            alias=None,
            import_type="from",
            level=1,
            line_number=1,
            is_relative=True,
        )
    }


def test_collect_import_aliases_from_source_ignores_wildcard_imports():
    aliases = collect_import_aliases_from_source(
        "from repodossier.scanner import *\n",
        source_path="src/app.py",
    )

    assert aliases == {}


def test_parse_calls_from_source_keeps_import_aliases_available_on_visitor():
    tree = ast.parse(
        "import pathlib as pl\n"
        "\n"
        "def main():\n"
        "    return pl.Path('x')\n",
        filename="src/app.py",
    )

    graph = build_call_graph_from_ast(
        tree,
        source_path="src/app.py",
        module_name="app",
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="Path",
            callee_qualified_name=None,
            line_number=4,
            call_type="method",
            confidence="unresolved",
        )
    ]

def test_resolve_import_aliases_with_import_graph_marks_from_import_as_local(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text("def scan_single_file():\n    return None\n", encoding="utf-8")
    app_path.write_text(
        "from repodossier.scanner import scan_single_file\n"
        "\n"
        "def main():\n"
        "    return scan_single_file()\n",
        encoding="utf-8",
    )

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )
    aliases = collect_import_aliases_from_source(
        app_path.read_text(encoding="utf-8"),
        source_path=app_path,
    )

    resolved_aliases = resolve_import_aliases_with_import_graph(
        aliases,
        import_graph,
        source_module="repodossier.app",
        source_path=app_path,
    )

    assert resolved_aliases == {
        "scan_single_file": ImportAlias(
            local_name="scan_single_file",
            qualified_name="repodossier.scanner.scan_single_file",
            module_name="repodossier.scanner",
            imported_name="scan_single_file",
            alias=None,
            import_type="from",
            level=0,
            line_number=1,
            is_relative=False,
            is_local=True,
            resolved_module="repodossier.scanner",
            resolved_path=scanner_path.as_posix(),
        )
    }


def test_resolve_import_aliases_with_import_graph_marks_plain_import_alias_as_local(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text("def scan_single_file():\n    return None\n", encoding="utf-8")
    app_path.write_text(
        "import repodossier.scanner as scanner\n"
        "\n"
        "def main():\n"
        "    return scanner.scan_single_file()\n",
        encoding="utf-8",
    )

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )
    aliases = collect_import_aliases_from_source(
        app_path.read_text(encoding="utf-8"),
        source_path=app_path,
    )

    resolved_aliases = resolve_import_aliases_with_import_graph(
        aliases,
        import_graph,
        source_module="repodossier.app",
        source_path=app_path,
    )

    assert resolved_aliases == {
        "scanner": ImportAlias(
            local_name="scanner",
            qualified_name="repodossier.scanner",
            module_name="repodossier.scanner",
            imported_name=None,
            alias="scanner",
            import_type="import",
            level=0,
            line_number=1,
            is_relative=False,
            is_local=True,
            resolved_module="repodossier.scanner",
            resolved_path=scanner_path.as_posix(),
        )
    }


def test_resolve_import_aliases_with_import_graph_marks_external_alias_as_not_local():
    aliases = collect_import_aliases_from_source(
        "import pathlib as pl\n",
        source_path="src/app.py",
    )

    resolved_aliases = resolve_import_aliases_with_import_graph(
        aliases,
        import_graph=object(),
        source_module="app",
        source_path="src/app.py",
    )

    assert resolved_aliases == {
        "pl": ImportAlias(
            local_name="pl",
            qualified_name="pathlib",
            module_name="pathlib",
            imported_name=None,
            alias="pl",
            import_type="import",
            level=0,
            line_number=1,
            is_relative=False,
            is_local=False,
            resolved_module=None,
            resolved_path=None,
        )
    }


def test_build_call_graph_from_ast_accepts_import_graph_for_alias_resolution(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text("def scan_single_file():\n    return None\n", encoding="utf-8")
    app_source = (
        "from repodossier.scanner import scan_single_file\n"
        "\n"
        "def main():\n"
        "    return scan_single_file()\n"
    )
    app_path.write_text(app_source, encoding="utf-8")

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )

    graph = build_call_graph_from_ast(
        ast.parse(app_source, filename=app_path.as_posix()),
        source_path=app_path,
        module_name="repodossier.app",
        import_graph=import_graph,
    )

    # 7.5.b verbindet nur Alias-Mapping mit dem Import Graph.
    # Die eigentliche imported_local-Auflösung kommt erst in 7.5.c.
    assert graph.sorted_edges() == [
        CallEdge(
            caller_file=app_path.as_posix(),
            caller_name="main",
            caller_qualified_name="repodossier.app.main",
            callee_name="scan_single_file",
            callee_qualified_name=None,
            line_number=4,
            call_type="function",
            confidence="unresolved",
        )
    ]

def test_parse_calls_from_source_resolves_imported_local_function_call(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text(
        "def scan_single_file():\n"
        "    return None\n",
        encoding="utf-8",
    )
    app_source = (
        "from repodossier.scanner import scan_single_file\n"
        "\n"
        "def main():\n"
        "    return scan_single_file()\n"
    )
    app_path.write_text(app_source, encoding="utf-8")

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )
    symbol_index = [
        FileSymbolIndex(
            file_path=scanner_path.as_posix(),
            symbols=[
                SymbolInfo(
                    name="scan_single_file",
                    kind="function",
                    file_path=scanner_path.as_posix(),
                    line_start=1,
                )
            ],
        )
    ]

    graph = parse_calls_from_source(
        app_source,
        source_path=app_path,
        module_name="repodossier.app",
        symbol_index=symbol_index,
        import_graph=import_graph,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file=app_path.as_posix(),
            caller_name="main",
            caller_qualified_name="repodossier.app.main",
            callee_name="scan_single_file",
            callee_qualified_name="repodossier.scanner.scan_single_file",
            line_number=4,
            call_type="function",
            confidence="imported_local",
        )
    ]


def test_parse_calls_from_source_resolves_imported_local_function_alias_call(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text(
        "def scan_single_file():\n"
        "    return None\n",
        encoding="utf-8",
    )
    app_source = (
        "from repodossier.scanner import scan_single_file as scan\n"
        "\n"
        "def main():\n"
        "    return scan()\n"
    )
    app_path.write_text(app_source, encoding="utf-8")

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )
    symbol_index = [
        FileSymbolIndex(
            file_path=scanner_path.as_posix(),
            symbols=[
                SymbolInfo(
                    name="scan_single_file",
                    kind="function",
                    file_path=scanner_path.as_posix(),
                    line_start=1,
                )
            ],
        )
    ]

    graph = parse_calls_from_source(
        app_source,
        source_path=app_path,
        module_name="repodossier.app",
        symbol_index=symbol_index,
        import_graph=import_graph,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file=app_path.as_posix(),
            caller_name="main",
            caller_qualified_name="repodossier.app.main",
            callee_name="scan",
            callee_qualified_name="repodossier.scanner.scan_single_file",
            line_number=4,
            call_type="function",
            confidence="imported_local",
        )
    ]


def test_parse_calls_from_source_keeps_imported_call_unresolved_when_symbol_is_missing(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text(
        "def other_function():\n"
        "    return None\n",
        encoding="utf-8",
    )
    app_source = (
        "from repodossier.scanner import scan_single_file\n"
        "\n"
        "def main():\n"
        "    return scan_single_file()\n"
    )
    app_path.write_text(app_source, encoding="utf-8")

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )
    symbol_index = [
        FileSymbolIndex(
            file_path=scanner_path.as_posix(),
            symbols=[
                SymbolInfo(
                    name="other_function",
                    kind="function",
                    file_path=scanner_path.as_posix(),
                    line_start=1,
                )
            ],
        )
    ]

    graph = parse_calls_from_source(
        app_source,
        source_path=app_path,
        module_name="repodossier.app",
        symbol_index=symbol_index,
        import_graph=import_graph,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file=app_path.as_posix(),
            caller_name="main",
            caller_qualified_name="repodossier.app.main",
            callee_name="scan_single_file",
            callee_qualified_name=None,
            line_number=4,
            call_type="function",
            confidence="unresolved",
        )
    ]


def test_parse_calls_from_source_marks_local_and_imported_same_name_ambiguous(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text(
        "def helper():\n"
        "    return None\n",
        encoding="utf-8",
    )
    app_source = (
        "from repodossier.scanner import helper\n"
        "\n"
        "def helper():\n"
        "    return 1\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )
    app_path.write_text(app_source, encoding="utf-8")

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )
    symbol_index = [
        FileSymbolIndex(
            file_path=scanner_path.as_posix(),
            symbols=[
                SymbolInfo(
                    name="helper",
                    kind="function",
                    file_path=scanner_path.as_posix(),
                    line_start=1,
                )
            ],
        )
    ]

    graph = parse_calls_from_source(
        app_source,
        source_path=app_path,
        module_name="repodossier.app",
        symbol_index=symbol_index,
        import_graph=import_graph,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file=app_path.as_posix(),
            caller_name="main",
            caller_qualified_name="repodossier.app.main",
            callee_name="helper",
            callee_qualified_name=None,
            line_number=7,
            call_type="function",
            confidence="ambiguous",
        )
    ]

def test_parse_calls_from_source_marks_from_import_call_as_external():
    source = (
        "from pathlib import Path\n"
        "\n"
        "def main():\n"
        "    return Path('x')\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
        import_graph=object(),
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="Path",
            callee_qualified_name="pathlib.Path",
            line_number=4,
            call_type="function",
            confidence="external",
        )
    ]


def test_parse_calls_from_source_marks_import_alias_attribute_call_as_external():
    source = (
        "import pathlib as pl\n"
        "\n"
        "def main():\n"
        "    return pl.Path('x')\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
        import_graph=object(),
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="Path",
            callee_qualified_name="pathlib.Path",
            line_number=4,
            call_type="method",
            confidence="external",
        )
    ]


def test_parse_calls_from_source_marks_plain_import_attribute_call_as_external():
    source = (
        "import subprocess\n"
        "\n"
        "def main():\n"
        "    return subprocess.run(['echo', 'ok'])\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
        import_graph=object(),
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="run",
            callee_qualified_name="subprocess.run",
            line_number=4,
            call_type="method",
            confidence="external",
        )
    ]


def test_parse_calls_from_source_keeps_local_import_alias_attribute_call_unresolved_not_external(tmp_path):
    source_root = tmp_path / "src" / "repodossier"
    source_root.mkdir(parents=True)
    scanner_path = source_root / "scanner.py"
    app_path = source_root / "app.py"

    scanner_path.write_text(
        "def scan_single_file():\n"
        "    return None\n",
        encoding="utf-8",
    )
    app_source = (
        "import repodossier.scanner as scanner\n"
        "\n"
        "def main():\n"
        "    return scanner.scan_single_file()\n"
    )
    app_path.write_text(app_source, encoding="utf-8")

    import_graph = build_import_graph(
        [scanner_path, app_path],
        repo_root=tmp_path,
    )

    graph = parse_calls_from_source(
        app_source,
        source_path=app_path,
        module_name="repodossier.app",
        import_graph=import_graph,
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file=app_path.as_posix(),
            caller_name="main",
            caller_qualified_name="repodossier.app.main",
            callee_name="scan_single_file",
            callee_qualified_name=None,
            line_number=4,
            call_type="method",
            confidence="unresolved",
        )
    ]


def test_parse_calls_from_source_marks_external_alias_and_chain_conservatively():
    source = (
        "from pathlib import Path\n"
        "\n"
        "def main():\n"
        "    return Path('x').read_text()\n"
    )

    graph = parse_calls_from_source(
        source,
        source_path="src/app.py",
        module_name="app",
        import_graph=object(),
    )

    assert graph.sorted_edges() == [
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="Path",
            callee_qualified_name="pathlib.Path",
            line_number=4,
            call_type="function",
            confidence="external",
        ),
        CallEdge(
            caller_file="src/app.py",
            caller_name="main",
            caller_qualified_name="app.main",
            callee_name="read_text",
            callee_qualified_name=None,
            line_number=4,
            call_type="method",
            confidence="unresolved_method",
        ),
    ]

def test_symbol_index_does_not_make_same_file_local_calls_ambiguous(tmp_path):
    from repodossier.call_graph import parse_calls_from_source
    from repodossier.symbols import build_symbol_index

    source_path = tmp_path / "src" / "example" / "app.py"
    source_path.parent.mkdir(parents=True)
    source = (
        "def helper():\n"
        "    return 1\n"
        "\n"
        "class Worker:\n"
        "    def run(self):\n"
        "        return self.done()\n"
        "\n"
        "    def done(self):\n"
        "        return helper()\n"
        "\n"
        "def main():\n"
        "    return helper()\n"
    )
    source_path.write_text(source, encoding="utf-8")

    symbol_index = build_symbol_index([source_path], base_path=tmp_path)
    graph = parse_calls_from_source(
        source,
        source_path="src/example/app.py",
        module_name="example.app",
        symbol_index=symbol_index,
    )

    edges = graph.sorted_edges()
    edge_pairs = {
        (edge.caller_key, edge.callee_key, edge.confidence)
        for edge in edges
    }

    assert ("example.app.main", "example.app.helper", "local") in edge_pairs
    assert ("example.app.Worker.done", "example.app.helper", "local") in edge_pairs
    assert ("example.app.Worker.run", "example.app.Worker.done", "local_method") in edge_pairs
    assert not any(edge.confidence == "ambiguous" for edge in edges)
