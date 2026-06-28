from repocontext.call_graph import CallEdge, CallGraph


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
