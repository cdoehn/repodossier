import subprocess
import sqlite3
from pathlib import Path

from repocontext.exporters.ai import (
    AI_EXPORT_FILENAME,
    AI_EXPORT_SECTION_HEADINGS,
    AI_EXPORT_SECTION_ORDER,
    AIExportContext,
    create_ai_export_context,
    generate_ai_export,
    iter_ai_export_headings,
    render_ai_export,
    write_ai_export,
)
from repocontext.exporters.full import create_full_export_context
from repocontext.git import RepositoryInfo, TrackedFile
from repocontext.models import FileInfo


def make_repository_info(tmp_path: Path) -> RepositoryInfo:
    return RepositoryInfo(
        name="example",
        root_path=tmp_path,
        is_current_directory_root=True,
        branch="main",
        commit_hash="a" * 40,
        short_commit_hash="aaaaaaa",
        remote_url=None,
        is_dirty=False,
        tracked_files=[
            TrackedFile(path=Path("README.md")),
            TrackedFile(path=Path("src/app.py")),
        ],
        commit_metadata=None,
    )


def make_ai_export_context(tmp_path: Path) -> AIExportContext:
    repository_info = make_repository_info(tmp_path)
    files = [
        FileInfo(
            relative_path=Path("README.md"),
            absolute_path=tmp_path / "README.md",
            is_text=True,
            is_binary=False,
            language="markdown",
            line_count=1,
            estimated_tokens=4,
            content="# Example\n",
        ),
        FileInfo(
            relative_path=Path("src/app.py"),
            absolute_path=tmp_path / "src" / "app.py",
            is_text=True,
            is_binary=False,
            language="python",
            line_count=2,
            estimated_tokens=8,
            content="def main():\n    return 'source body must not leak'\n",
        ),
    ]
    full_context = create_full_export_context(repository_info, files)
    return create_ai_export_context(full_context)



def make_ai_export_context_from_files(
    tmp_path: Path,
    files: dict[str, str],
) -> AIExportContext:
    repository_info = RepositoryInfo(
        name="example",
        root_path=tmp_path,
        is_current_directory_root=True,
        branch="main",
        commit_hash="b" * 40,
        short_commit_hash="bbbbbbb",
        remote_url=None,
        is_dirty=False,
        tracked_files=[
            TrackedFile(path=Path(path))
            for path in sorted(files)
        ],
        commit_metadata=None,
    )

    scanned_files = []
    for path, content in sorted(files.items()):
        absolute_path = tmp_path / path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(content, encoding="utf-8")

        suffix = Path(path).suffix.lower()
        language = {
            ".md": "markdown",
            ".py": "python",
            ".toml": "toml",
            ".txt": "text",
        }.get(suffix, "text")

        scanned_files.append(
            FileInfo(
                relative_path=Path(path),
                absolute_path=absolute_path,
                is_text=True,
                is_binary=False,
                language=language,
                line_count=len(content.splitlines()),
                estimated_tokens=max(1, len(content) // 4),
                content=content,
            )
        )

    return create_ai_export_context(
        create_full_export_context(repository_info, scanned_files)
    )

def test_ai_export_section_order_matches_milestone_8_structure() -> None:
    assert AI_EXPORT_SECTION_ORDER == (
        "project",
        "architecture_summary",
        "important_files",
        "symbol_index",
        "import_graph",
        "call_graph",
        "notes",
    )


def test_ai_export_headings_are_stable() -> None:
    assert iter_ai_export_headings() == (
        "# AI CONTEXT",
        "## Project",
        "## Architecture Summary",
        "## Important Files",
        "## Symbol Index",
        "## Import Graph",
        "## Call Graph",
        "## Notes",
    )


def test_ai_export_headings_cover_every_ordered_section() -> None:
    assert set(AI_EXPORT_SECTION_HEADINGS) == set(AI_EXPORT_SECTION_ORDER)


def test_create_ai_export_context_wraps_full_export_context(tmp_path: Path) -> None:
    context = make_ai_export_context(tmp_path)

    assert context.repository_root == tmp_path
    assert context.full_context.tracked_file_count == 2



def test_architecture_summary_detects_python_cli_project(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "pyproject.toml": "[project.scripts]\nexample = \"example.cli:main\"\n",
            "src/example/__init__.py": "",
            "src/example/cli.py": "def main():\n    return 0\n",
            "tests/test_cli.py": "def test_cli():\n    assert True\n",
            "README.md": "# Example\n",
        },
    )

    rendered = render_ai_export(context)

    assert "## Architecture Summary" in rendered
    assert "Detected project type: Python CLI project" in rendered
    assert "Main entry points:" in rendered
    assert "- example: example.cli:main" in rendered
    assert "- src/example/cli.py" in rendered
    assert "Top-level directories:" in rendered
    assert "- src" in rendered
    assert "- tests" in rendered
    assert "Python package/module roots:" in rendered
    assert "- src/example" in rendered
    assert "Tests:" in rendered
    assert "- tests/" in rendered
    assert "Documentation:" in rendered
    assert "- README.md" in rendered


def test_architecture_summary_detects_python_project_without_pyproject(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "app.py": "def run():\n    return 1\n",
        },
    )

    rendered = render_ai_export(context)

    assert "Detected project type: Python project" in rendered
    assert "Main entry points:" in rendered
    assert "- none detected" in rendered


def test_architecture_summary_detects_core_repocontext_areas(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/repocontext/__init__.py": "",
            "src/repocontext/cli.py": "",
            "src/repocontext/exporters/ai.py": "",
            "src/repocontext/exporters/full.py": "",
            "src/repocontext/git.py": "",
            "src/repocontext/gitignore.py": "",
            "src/repocontext/import_graph.py": "",
            "src/repocontext/call_graph.py": "",
            "src/repocontext/scanner.py": "",
            "src/repocontext/symbols.py": "",
        },
    )

    rendered = render_ai_export(context)

    assert "- Command-line interface: src/repocontext/cli.py" in rendered
    assert "- AI export generation: src/repocontext/exporters/ai.py" in rendered
    assert "- Full export generation: src/repocontext/exporters/full.py" in rendered
    assert "- Git repository discovery: src/repocontext/git.py" in rendered
    assert "- .gitignore management: src/repocontext/gitignore.py" in rendered
    assert "- Import graph analysis: src/repocontext/import_graph.py" in rendered
    assert "- Call graph analysis: src/repocontext/call_graph.py" in rendered
    assert "- File scanning: src/repocontext/scanner.py" in rendered
    assert "- Symbol extraction: src/repocontext/symbols.py" in rendered


def test_important_files_uses_shared_ranking_for_entrypoints_and_central_files(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "pyproject.toml": """
[project]
name = "example"

[project.scripts]
example = "example.cli:main"
""",
            "README.md": "# Example\n",
            "src/example/__init__.py": "",
            "src/example/cli.py": "from example.core import run\n\n\ndef main():\n    return run()\n",
            "src/example/api.py": "from example.core import run\n\n\ndef handle():\n    return run()\n",
            "src/example/core.py": "def run():\n    return 0\n",
            "src/example/helper.py": "VALUE = 1\n",
        },
    )

    rendered = render_ai_export(context)

    assert "## Important Files" in rendered

    important_files_section = rendered.split("## Important Files", 1)[1].split("## Symbol Index", 1)[0]

    assert "- src/example/cli.py" in important_files_section
    assert "Project script entry point" in important_files_section
    assert "Likely Python entry point" in important_files_section

    assert "- src/example/core.py" in important_files_section
    assert (
        "Imported by 2 local files" in important_files_section
        or "Called by 2 local files" in important_files_section
    )

    assert "- README.md" in important_files_section
    assert "Primary project documentation" in important_files_section

    assert "- pyproject.toml" in important_files_section
    assert "Python project configuration" in important_files_section

    assert "- src/example/helper.py" not in important_files_section

    assert important_files_section.index("- src/example/cli.py") < important_files_section.index("- README.md")
    assert "- src/example/core.py" in important_files_section
    assert "- pyproject.toml" in important_files_section


def test_important_files_excludes_generated_exports(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "pyproject.toml": "[project]\nname = \"example\"\n",
            "full.txt": "generated full export\n",
            "ai.txt": "generated ai export\n",
            "docs.txt": "generated docs export\n",
            "changed.txt": "generated changed export\n",
        },
    )

    rendered = render_ai_export(context)
    important_files_section = rendered.split("## Important Files", 1)[1].split("## Symbol Index", 1)[0]

    assert "pyproject.toml" in important_files_section
    assert "full.txt" not in important_files_section
    assert "ai.txt" not in important_files_section
    assert "docs.txt" not in important_files_section
    assert "changed.txt" not in important_files_section


def test_important_files_ranking_is_deterministic(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/b.py": "def b():\n    return 2\n",
            "src/example/a.py": "def a():\n    return 1\n",
            "README.md": "# Example\n",
            "pyproject.toml": "[project]\nname = \"example\"\n",
        },
    )

    first_render = render_ai_export(context)
    second_render = render_ai_export(context)

    assert first_render == second_render
    important_files_section = first_render.split("## Important Files", 1)[1].split("## Symbol Index", 1)[0]
    assert important_files_section.index("- README.md") < important_files_section.index("- pyproject.toml")




def test_important_files_prioritizes_config_and_docs_before_large_test_files(tmp_path: Path) -> None:
    large_test_content = "\n".join(
        f"def test_case_{index}():\n    assert True\n"
        for index in range(80)
    )
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "pyproject.toml": "[project]\nname = \"example\"\n",
            "README.md": "# Example\n",
            "REPOCONTEXT_ARCHITECTURE.md": "# Architecture\n",
            "REPOCONTEXT_SPEC_v1.3.txt": "SPEC\n",
            "src/example/cli.py": "def main():\n    return 0\n",
            "tests/test_big_module.py": large_test_content,
        },
    )

    rendered = render_ai_export(context)
    important_files_section = rendered.split("## Important Files", 1)[1].split("## Symbol Index", 1)[0]

    assert important_files_section.index("- README.md") < important_files_section.index("- pyproject.toml")
    assert important_files_section.index("- README.md") < important_files_section.index("- REPOCONTEXT_ARCHITECTURE.md")
    assert important_files_section.index("- REPOCONTEXT_ARCHITECTURE.md") < important_files_section.index("- REPOCONTEXT_SPEC_v1.3.txt")
    assert important_files_section.index("- REPOCONTEXT_SPEC_v1.3.txt") < important_files_section.index("- src/example/cli.py")
    assert "- tests/test_big_module.py" not in important_files_section


def test_ai_export_notes_are_final_and_describe_static_analysis_limits(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/app.py": "def main():\n    return 1\n",
        },
    )

    rendered = render_ai_export(context)
    notes_section = rendered.split("## Notes", 1)[1]

    assert "Detailed section content will be expanded" not in notes_section
    assert "complete source dumps" in notes_section
    assert "Git-tracked scanner data" in notes_section
    assert "static Python AST analysis" in notes_section
    assert "best-effort and deterministic" in notes_section
    assert "Dynamic runtime behavior" in notes_section


def test_symbol_index_renders_classes_functions_and_methods(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/app.py": (
                "class Worker:\n"
                "    def run(self):\n"
                "        return 1\n"
                "\n"
                "def main():\n"
                "    return Worker().run()\n"
            ),
        },
    )

    rendered = render_ai_export(context)
    symbol_index_section = rendered.split("## Symbol Index", 1)[1].split("## Import Graph", 1)[0]

    assert "### src/example/app.py" in symbol_index_section
    assert "- class Worker:1" in symbol_index_section
    assert "- method Worker.run:2" in symbol_index_section
    assert "- function main:5" in symbol_index_section


def test_symbol_index_reports_no_python_symbols_for_symbol_free_python_file(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/constants.py": "VALUE = 1\n",
        },
    )

    rendered = render_ai_export(context)
    symbol_index_section = rendered.split("## Symbol Index", 1)[1].split("## Import Graph", 1)[0]

    assert "No Python symbols found." in symbol_index_section


def test_symbol_index_handles_syntax_errors_without_crashing(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/broken.py": "def broken(:\n    pass\n",
        },
    )

    rendered = render_ai_export(context)
    symbol_index_section = rendered.split("## Symbol Index", 1)[1].split("## Import Graph", 1)[0]

    assert "Analysis errors:" in symbol_index_section
    assert "src/example/broken.py" in symbol_index_section
    assert "Traceback" not in symbol_index_section



def test_ai_export_renders_empty_database_schema_section(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/app.py": "VALUE = 1\n",
        },
    )

    rendered = render_ai_export(context)

    assert "## Database Schema" in rendered
    database_schema_section = rendered.split("## Database Schema", 1)[1].split(
        "## Symbol Index",
        1,
    )[0]

    assert "Summary:" in database_schema_section
    assert "- Database files: 0" in database_schema_section
    assert "- SQL schema files: 0" in database_schema_section
    assert "- Tables: 0" in database_schema_section
    assert "No database schema files detected." in database_schema_section
    assert "- none detected" in database_schema_section
    assert rendered.index("## Important Files") < rendered.index("## Database Schema")
    assert rendered.index("## Database Schema") < rendered.index("## Symbol Index")


def test_ai_export_renders_sql_schema_table_summary_without_insert_data(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "schema.sql": (
                "CREATE TABLE users (\n"
                "  id INTEGER PRIMARY KEY,\n"
                "  name TEXT NOT NULL,\n"
                "  role_id INTEGER,\n"
                "  FOREIGN KEY(role_id) REFERENCES roles(id)\n"
                ");\n"
                "INSERT INTO users (name) VALUES ('VerySecretUserName');\n"
            ),
        },
    )

    rendered = render_ai_export(context)
    database_schema_section = rendered.split("## Database Schema", 1)[1].split(
        "## Symbol Index",
        1,
    )[0]

    assert "- SQL schema files: 1" in database_schema_section
    assert "- schema.sql" in database_schema_section
    assert "- users (schema.sql): id INTEGER PK, name TEXT NOT NULL, role_id INTEGER" in database_schema_section
    assert "- users.role_id -> roles.id" in database_schema_section
    assert "VerySecretUserName" not in rendered


def test_ai_export_renders_sqlite_schema_table_summary_without_table_data(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute("INSERT INTO users (name) VALUES ('VerySecretUserName')")
        connection.commit()
    finally:
        connection.close()

    repository_info = make_repository_info(tmp_path)
    database_file = FileInfo(
        relative_path=Path("app.sqlite"),
        absolute_path=database_path,
        is_text=False,
        is_binary=True,
        language=None,
        line_count=0,
        estimated_tokens=0,
        content=None,
    )
    context = create_ai_export_context(
        create_full_export_context(repository_info, [database_file])
    )

    rendered = render_ai_export(context)
    database_schema_section = rendered.split("## Database Schema", 1)[1].split(
        "## Symbol Index",
        1,
    )[0]

    assert "- Database files: 1" in database_schema_section
    assert "- app.sqlite" in database_schema_section
    assert "- users (app.sqlite): id INTEGER PK, name TEXT NOT NULL" in database_schema_section
    assert "VerySecretUserName" not in rendered


def test_ai_export_database_schema_output_is_deterministic(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "schema.sql": "CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT NOT NULL);",
        },
    )

    first_render = render_ai_export(context)
    second_render = render_ai_export(context)

    assert first_render == second_render

def test_import_graph_renders_internal_and_external_imports(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/__init__.py": "",
            "src/example/helper.py": "def help_me():\n    return 1\n",
            "src/example/app.py": (
                "import os\n"
                "from example.helper import help_me\n"
                "\n"
                "def main():\n"
                "    return help_me()\n"
            ),
        },
    )

    rendered = render_ai_export(context)
    import_graph_section = rendered.split("## Import Graph", 1)[1].split("## Call Graph", 1)[0]

    assert "Summary:" in import_graph_section
    assert "- Local modules: 3" in import_graph_section
    assert "Local imports by source file:" in import_graph_section
    assert "### src/example/app.py" in import_graph_section
    assert "Module: example.app" in import_graph_section
    assert "- example.helper (help_me, line 2)" in import_graph_section
    assert "External imports:" in import_graph_section
    assert "- example.app: os" in import_graph_section


def test_import_graph_renders_relative_imports(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/__init__.py": "",
            "src/example/helper.py": "VALUE = 1\n",
            "src/example/app.py": "from .helper import VALUE\n",
        },
    )

    rendered = render_ai_export(context)
    import_graph_section = rendered.split("## Import Graph", 1)[1].split("## Call Graph", 1)[0]

    assert "### src/example/app.py" in import_graph_section
    assert "- example.helper (VALUE, line 1)" in import_graph_section


def test_import_graph_handles_python_file_without_imports(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/app.py": "VALUE = 1\n",
        },
    )

    rendered = render_ai_export(context)
    import_graph_section = rendered.split("## Import Graph", 1)[1].split("## Call Graph", 1)[0]

    assert "- Local modules: 1" in import_graph_section
    assert "Local imports by source file:\n- none" in import_graph_section
    assert "External imports:\n- none" in import_graph_section
    assert "Unresolved imports:\n- none" in import_graph_section


def test_import_graph_handles_syntax_errors_without_raw_object_repr(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/broken.py": "from .helper import VALUE\n\ndef broken(:\n    pass\n",
            "src/example/helper.py": "VALUE = 1\n",
        },
    )

    rendered = render_ai_export(context)
    import_graph_section = rendered.split("## Import Graph", 1)[1].split("## Call Graph", 1)[0]

    assert "Analysis errors:" in import_graph_section
    assert "src/example/broken.py" in import_graph_section
    assert "SyntaxError" in import_graph_section
    assert "ImportReference(" not in import_graph_section
    assert "ImportEdge(" not in import_graph_section


def test_call_graph_renders_local_function_and_method_calls(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/app.py": (
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
            ),
        },
    )

    rendered = render_ai_export(context)
    call_graph_section = rendered.split("## Call Graph", 1)[1].split("## Notes", 1)[0]

    assert "Summary:" in call_graph_section
    assert "Internal calls by caller:" in call_graph_section
    assert "- example.app.main (src/example/app.py)" in call_graph_section
    assert "calls:" in call_graph_section
    assert "example.app.helper" in call_graph_section
    assert "- example.app.Worker.run (src/example/app.py)" in call_graph_section
    assert "example.app.Worker.done" in call_graph_section


def test_call_graph_renders_imported_local_function_calls(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/__init__.py": "",
            "src/example/helper.py": "def help_me():\n    return 1\n",
            "src/example/app.py": (
                "from example.helper import help_me\n"
                "\n"
                "def main():\n"
                "    return help_me()\n"
            ),
        },
    )

    rendered = render_ai_export(context)
    call_graph_section = rendered.split("## Call Graph", 1)[1].split("## Notes", 1)[0]

    assert "- example.app.main (src/example/app.py)" in call_graph_section
    assert "example.helper.help_me" in call_graph_section
    assert "imported_local" in call_graph_section


def test_call_graph_reports_empty_graph_cleanly(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/constants.py": "VALUE = 1\n",
        },
    )

    rendered = render_ai_export(context)
    call_graph_section = rendered.split("## Call Graph", 1)[1].split("## Notes", 1)[0]

    assert "No call graph edges found." in call_graph_section


def test_call_graph_output_is_deterministic(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "src/example/a.py": "def helper():\n    return 1\n\ndef main():\n    return helper()\n",
            "src/example/b.py": "def other():\n    return 2\n",
        },
    )

    first_render = render_ai_export(context)
    second_render = render_ai_export(context)

    assert first_render == second_render


def test_ai_export_filters_generated_export_files_from_analysis_inputs(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "ai.txt": "# AI CONTEXT\nSENTINEL_EXISTING_AI_EXPORT\n",
            "full.txt": "# Complete Source Export\nSENTINEL_EXISTING_FULL_EXPORT\n",
            "docs.txt": "SENTINEL_EXISTING_DOCS_EXPORT\n",
            "changed.txt": "SENTINEL_EXISTING_CHANGED_EXPORT\n",
            "src/example/app.py": "def main():\n    return 1\n",
        },
    )

    rendered = render_ai_export(context)

    assert "Scanned files: 1" in rendered
    assert "SENTINEL_EXISTING_AI_EXPORT" not in rendered
    assert "SENTINEL_EXISTING_FULL_EXPORT" not in rendered
    assert "SENTINEL_EXISTING_DOCS_EXPORT" not in rendered
    assert "SENTINEL_EXISTING_CHANGED_EXPORT" not in rendered

    important_files_section = rendered.split("## Important Files", 1)[1].split("## Symbol Index", 1)[0]
    symbol_index_section = rendered.split("## Symbol Index", 1)[1].split("## Import Graph", 1)[0]
    import_graph_section = rendered.split("## Import Graph", 1)[1].split("## Call Graph", 1)[0]
    call_graph_section = rendered.split("## Call Graph", 1)[1].split("## Notes", 1)[0]

    assert "ai.txt" not in important_files_section
    assert "full.txt" not in important_files_section
    assert "docs.txt" not in important_files_section
    assert "changed.txt" not in important_files_section

    assert "### ai.txt" not in symbol_index_section
    assert "### full.txt" not in symbol_index_section
    assert "### docs.txt" not in symbol_index_section
    assert "### changed.txt" not in symbol_index_section

    assert "ai.txt" not in import_graph_section
    assert "full.txt" not in import_graph_section
    assert "docs.txt" not in import_graph_section
    assert "changed.txt" not in import_graph_section

    assert "ai.txt" not in call_graph_section
    assert "full.txt" not in call_graph_section
    assert "docs.txt" not in call_graph_section
    assert "changed.txt" not in call_graph_section


def test_generate_ai_export_is_stable_when_ai_txt_already_exists(tmp_path: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    source_file = tmp_path / "app.py"
    source_file.write_text("def main():\n    return 1\n", encoding="utf-8")

    existing_ai_export = tmp_path / "ai.txt"
    existing_ai_export.write_text(
        "# AI CONTEXT\nSENTINEL_PREVIOUS_AI_EXPORT\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "app.py"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    output_path = generate_ai_export(tmp_path)
    first_render = output_path.read_text(encoding="utf-8")

    output_path = generate_ai_export(tmp_path)
    second_render = output_path.read_text(encoding="utf-8")

    assert first_render == second_render
    assert first_render.count("# AI CONTEXT") == 1
    assert "SENTINEL_PREVIOUS_AI_EXPORT" not in first_render
    assert "# Complete Source Export" not in first_render


def test_render_ai_export_contains_required_sections(tmp_path: Path) -> None:
    context = make_ai_export_context(tmp_path)

    rendered = render_ai_export(context)

    assert rendered.startswith("# AI CONTEXT\n")
    assert "## Project" in rendered
    assert "## Architecture Summary" in rendered
    assert "## Important Files" in rendered
    assert "## Symbol Index" in rendered
    assert "## Import Graph" in rendered
    assert "## Call Graph" in rendered
    assert "Repository: example" in rendered
    assert "Tracked files: 2" in rendered
    assert "Exported text files: 2" in rendered


def test_render_ai_export_does_not_include_complete_source_dump(tmp_path: Path) -> None:
    context = make_ai_export_context(tmp_path)

    rendered = render_ai_export(context)

    assert "# Complete Source Export" not in rendered
    assert "source body must not leak" not in rendered
    assert "```python" not in rendered


def test_render_ai_export_handles_empty_file_data(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    full_context = create_full_export_context(repository_info, [])
    context = create_ai_export_context(full_context)

    rendered = render_ai_export(context)

    assert "Tracked files: 2" in rendered
    assert "Scanned files: 0" in rendered
    assert "Exported text files: 0" in rendered


def test_write_ai_export_defaults_to_repository_root_ai_txt(tmp_path: Path) -> None:
    context = make_ai_export_context(tmp_path)

    output_path = write_ai_export(context)

    assert output_path == tmp_path / AI_EXPORT_FILENAME
    assert output_path.read_text(encoding="utf-8").startswith("# AI CONTEXT\n")
    assert not (tmp_path / f".{AI_EXPORT_FILENAME}.tmp").exists()

def test_generate_ai_export_writes_ai_txt_for_tracked_python_repo(tmp_path: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    source_file = tmp_path / "app.py"
    source_file.write_text("def main():\n    return 1\n", encoding="utf-8")

    subprocess.run(
        ["git", "add", "app.py"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    output_path = generate_ai_export(tmp_path)
    rendered = output_path.read_text(encoding="utf-8")

    assert output_path == tmp_path / "ai.txt"
    assert output_path.exists()
    assert rendered.startswith("# AI CONTEXT\n")
    assert "## Architecture Summary" in rendered
    assert "## Important Files" in rendered
    assert "## Symbol Index" in rendered
    assert "## Import Graph" in rendered
    assert "## Call Graph" in rendered
    assert rendered.strip()
    assert "# Complete Source Export" not in rendered
    assert "def main" not in rendered
