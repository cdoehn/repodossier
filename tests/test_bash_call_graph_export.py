from __future__ import annotations

from importlib import import_module
from pathlib import Path


exporter = import_module("repocontext.changed_exporter")


def test_append_bash_call_graph_section_to_export_with_shell_file():
    script = """main() {
  build_assets
  deploy_app
}

build_assets() {
  echo build
}

deploy_app() {
  echo deploy
}
"""

    output = exporter._append_bash_call_graph_section_to_export(
        "## Call Graph\n\n- existing_python_call -> target\n",
        {"files": [{"path": Path("scripts/deploy.sh"), "content": script}]},
    )

    assert "## Bash Call Graph" in output
    assert "scripts/deploy.sh:main -> scripts/deploy.sh:build_assets" in output
    assert "scripts/deploy.sh:main -> scripts/deploy.sh:deploy_app" in output
    assert "echo" not in output


def test_append_bash_call_graph_section_leaves_exports_without_bash_edges_unchanged():
    output = exporter._append_bash_call_graph_section_to_export(
        "## Call Graph\n\n- existing_python_call -> target\n",
        {"files": [{"path": Path("src/app.py"), "content": "print('ok')\n"}]},
    )

    assert output == "## Call Graph\n\n- existing_python_call -> target\n"


def test_append_bash_call_graph_section_accepts_path_to_real_shell_file(tmp_path):
    script_path = tmp_path / "run.sh"
    script_path.write_text(
        """main() {
  helper
}

helper() {
  echo ok
}
""",
        encoding="utf-8",
    )

    output = exporter._append_bash_call_graph_section_to_export(
        "## Call Graph\n",
        {"files": [script_path]},
    )

    assert "## Bash Call Graph" in output
    assert f"{script_path}:main -> {script_path}:helper" in output
