from repocontext.call_graph import (
    CallEdge,
    CallGraph,
    parse_calls_from_source,
)


def test_call_edge_exposes_stable_caller_and_callee_keys():
    edge = CallEdge(
        caller_file="repocontext/exporter.py",
        caller_name="export",
        caller_qualified_name="repocontext.exporter.export",
        callee_name="render",
        callee_qualified_name="repocontext.exporter.render",
        line_number=12,
        call_type="function",
        confidence="local",
    )

    assert edge.caller_key == "repocontext.exporter.export"
    assert edge.callee_key == "repocontext.exporter.render"
    assert edge.to_dict() == {
        "caller_file": "repocontext/exporter.py",
        "caller_name": "export",
        "caller_qualified_name": "repocontext.exporter.export",
        "callee_name": "render",
        "callee_qualified_name": "repocontext.exporter.render",
        "line_number": 12,
        "call_type": "function",
        "confidence": "local",
    }


def test_call_graph_deduplicates_identical_edges():
    edge = CallEdge(
        caller_file="repocontext/cli.py",
        caller_name="main",
        caller_qualified_name="repocontext.cli.main",
        callee_name="run",
        callee_qualified_name="repocontext.cli.run",
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
        caller_file="repocontext/cli.py",
        caller_name="main",
        caller_qualified_name="repocontext.cli.main",
        callee_name="parse_args",
        callee_qualified_name="repocontext.cli.parse_args",
        line_number=12,
        call_type="function",
        confidence="local",
    )
    second = CallEdge(
        caller_file="repocontext/cli.py",
        caller_name="main",
        caller_qualified_name="repocontext.cli.main",
        callee_name="run_export",
        callee_qualified_name="repocontext.exporter.run_export",
        line_number=18,
        call_type="function",
        confidence="imported_local",
    )
    graph = CallGraph([second, first])

    assert graph.get_calls_from("repocontext.cli.main") == (first, second)
    assert graph.get_callers_of("repocontext.cli.parse_args") == (first,)
    assert graph.callees_by_symbol["repocontext.cli.main"] == (first, second)
    assert graph.callers_by_symbol["repocontext.exporter.run_export"] == (second,)


def test_call_graph_text_output_is_grouped_and_stable():
    graph = CallGraph(
        [
            CallEdge(
                caller_file="repocontext/cli.py",
                caller_name="main",
                caller_qualified_name="repocontext.cli.main",
                callee_name="run",
                callee_qualified_name="repocontext.cli.run",
                line_number=22,
                call_type="function",
                confidence="local",
            ),
            CallEdge(
                caller_file="repocontext/cli.py",
                caller_name="main",
                caller_qualified_name="repocontext.cli.main",
                callee_name="parse_args",
                callee_qualified_name="repocontext.cli.parse_args",
                line_number=10,
                call_type="function",
                confidence="local",
            ),
        ]
    )

    assert graph.to_text() == (
        "repocontext.cli.main (repocontext/cli.py)\n"
        "  - line 10: calls repocontext.cli.parse_args [function, local]\n"
        "  - line 22: calls repocontext.cli.run [function, local]"
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
            callee_qualified_name=None,
            line_number=5,
            call_type="function",
            confidence="unresolved",
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

