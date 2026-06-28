import subprocess
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


def test_important_files_prioritizes_project_config_docs_and_entrypoints(tmp_path: Path) -> None:
    context = make_ai_export_context_from_files(
        tmp_path,
        {
            "pyproject.toml": "[project]\nname = \"example\"\n",
            "README.md": "# Example\n",
            "src/example/__init__.py": "",
            "src/example/cli.py": "def main():\n    return 0\n",
            "src/example/scanner.py": "def scan():\n    return []\n",
        },
    )

    rendered = render_ai_export(context)

    assert "## Important Files" in rendered
    assert "- pyproject.toml\n  Reason: Python project configuration" in rendered
    assert "- README.md\n  Reason: Primary project documentation" in rendered
    assert "- src/example/cli.py" in rendered
    assert "CLI entry point" in rendered
    assert "- src/example/scanner.py" in rendered
    assert "Repository file scanning implementation" in rendered


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
    assert important_files_section.index("- pyproject.toml") < important_files_section.index("- README.md")


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
