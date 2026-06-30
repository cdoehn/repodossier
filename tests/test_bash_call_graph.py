from __future__ import annotations

from repocontext.bash_call_graph import BashCallEdge
from repocontext.bash_call_graph import discover_bash_call_graph
from repocontext.bash_call_graph import discover_bash_call_graph_for_files


def _edge_set(edges: list[BashCallEdge]):
    return {(edge.caller, edge.callee) for edge in edges}


def test_discovers_simple_bash_function_calls():
    script = """main() {
  build_assets
  deploy_app "$target"
}

build_assets() {
  echo build
}

deploy_app() {
  restart_service
}

restart_service() {
  echo restart
}

rollback_app() {
  echo rollback
}
"""

    edges = discover_bash_call_graph(script, path="scripts/deploy.sh")

    assert _edge_set(edges) == {
        ("main", "build_assets"),
        ("main", "deploy_app"),
        ("deploy_app", "restart_service"),
    }
    assert all(isinstance(edge, BashCallEdge) for edge in edges)
    assert all(edge.caller_path == "scripts/deploy.sh" for edge in edges)
    assert all(edge.callee_path == "scripts/deploy.sh" for edge in edges)


def test_detects_conditionals_boolean_chains_and_pipelines():
    script = """main() {
  if build_assets; then deploy_app; fi
  build_assets && deploy_app || rollback_app
  deploy_app | tee deploy.log
}

build_assets() {
  echo build
}

deploy_app() {
  echo deploy
}

rollback_app() {
  echo rollback
}
"""

    edges = discover_bash_call_graph(script)

    assert _edge_set(edges) == {
        ("main", "build_assets"),
        ("main", "deploy_app"),
        ("main", "rollback_app"),
    }


def test_ignores_comments_strings_and_external_commands():
    script = """main() {
  # deploy_app
  echo "deploy_app"
  grep deploy_app file.txt
  sed 's/deploy_app/x/g' file.txt
}

deploy_app() {
  echo deploy
}
"""

    edges = discover_bash_call_graph(script)

    assert edges == []


def test_allows_recursive_edges():
    script = """retry_until_success() {
  retry_until_success
}
"""

    edges = discover_bash_call_graph(script)

    assert _edge_set(edges) == {("retry_until_success", "retry_until_success")}
    assert edges[0].call_line == 2
    assert edges[0].caller_line == 1
    assert edges[0].callee_line == 1


def test_discovers_cross_file_edges_for_known_bash_functions():
    files = {
        "scripts/build.sh": """build_assets() {
  echo build
}
""",
        "scripts/deploy.sh": """deploy_app() {
  build_assets
}
""",
    }

    edges = discover_bash_call_graph_for_files(files)

    assert _edge_set(edges) == {("deploy_app", "build_assets")}
    assert edges[0].caller_path == "scripts/deploy.sh"
    assert edges[0].callee_path == "scripts/build.sh"


def test_ignores_unknown_external_commands_even_when_they_look_like_calls():
    script = """main() {
  rsync_files
  restart_system_service
}
"""

    edges = discover_bash_call_graph(script)

    assert edges == []
