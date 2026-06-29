from pathlib import Path
import sqlite3

from repocontext.exporters.full import (
    FULL_EXPORT_SECTION_HEADINGS,
    FULL_EXPORT_SECTION_ORDER,
    FullExportContext,
    create_full_export_context,
    iter_full_export_headings,
    render_full_export,
    write_full_export,
)
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
            TrackedFile(path=Path("src/module.py")),
            TrackedFile(path=Path("README.md")),
            TrackedFile(path=Path("image.bin")),
        ],
        commit_metadata=None,
    )


def test_full_export_section_order_matches_milestone_3_structure() -> None:
    assert FULL_EXPORT_SECTION_ORDER == (
        "ai_quick_start",
        "repository_statistics",
        "file_summary",
        "repository_tree",
        "dependencies",
        "database_schema",
        "complete_source_export",
        "warnings",
    )


def test_full_export_section_headings_are_markdown_headings() -> None:
    assert iter_full_export_headings() == (
        "# AI Quick Start",
        "# Repository Statistics",
        "# File Summary",
        "# Repository Tree",
        "# Dependencies",
        "# Database Schema",
        "# Complete Source Export",
        "# Warnings",
    )


def test_full_export_headings_cover_every_ordered_section() -> None:
    assert set(FULL_EXPORT_SECTION_HEADINGS) == set(FULL_EXPORT_SECTION_ORDER)


def test_full_export_context_normalizes_sequences_to_tuples(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    file_info = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        content="# Example\n",
    )

    context = FullExportContext(
        repository_info=repository_info,
        scanned_files=[file_info],
        warnings=["example warning"],
    )

    assert context.scanned_files == (file_info,)
    assert context.warnings == ("example warning",)


def test_full_export_context_exposes_repository_basics(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    context = create_full_export_context(repository_info, [])

    assert context.repository_root == tmp_path
    assert context.tracked_file_count == 3


def test_full_export_context_sorts_scanned_files_by_relative_path(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    files = [
        FileInfo(relative_path=Path("src/module.py"), absolute_path=tmp_path / "src/module.py"),
        FileInfo(relative_path=Path("README.md"), absolute_path=tmp_path / "README.md"),
        FileInfo(relative_path=Path("docs/notes.txt"), absolute_path=tmp_path / "docs/notes.txt"),
    ]

    context = create_full_export_context(repository_info, files)

    assert [file_info.relative_path.as_posix() for file_info in context.sorted_files] == [
        "README.md",
        "docs/notes.txt",
        "src/module.py",
    ]


def test_full_export_context_filters_exported_text_files(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    exported = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        line_count=2,
        estimated_tokens=5,
        content="# Example\nText\n",
    )
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )
    errored = FileInfo(
        relative_path=Path("broken.txt"),
        absolute_path=tmp_path / "broken.txt",
        is_text=True,
        is_binary=False,
        content=None,
        error="Could not read file",
    )

    context = create_full_export_context(repository_info, [binary, errored, exported])

    assert context.exported_text_files == (exported,)
    assert context.skipped_binary_files == (binary,)
    assert context.errored_files == (errored,)


def test_full_export_context_totals_use_exported_text_files_only(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    first = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        line_count=3,
        estimated_tokens=10,
        content="one\ntwo\nthree\n",
    )
    second = FileInfo(
        relative_path=Path("src/module.py"),
        absolute_path=tmp_path / "src/module.py",
        is_text=True,
        is_binary=False,
        line_count=2,
        estimated_tokens=8,
        content="print('hello')\nprint('world')\n",
    )
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        line_count=None,
        estimated_tokens=None,
        content=None,
    )

    context = create_full_export_context(repository_info, [binary, first, second])

    assert context.total_line_count == 5
    assert context.total_estimated_tokens == 18


def test_render_full_export_renders_ai_quick_start_details(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    pyproject = FileInfo(
        relative_path=Path("pyproject.toml"),
        absolute_path=tmp_path / "pyproject.toml",
        is_text=True,
        is_binary=False,
        language="toml",
        line_count=10,
        estimated_tokens=20,
        content=(
            '[project]\n'
            'description = "AI-friendly exports of Git repositories."\n'
            '\n'
            '[project.scripts]\n'
            'repocontext = "repocontext.cli:main"\n'
            '\n'
            '[project.optional-dependencies]\n'
            'dev = ["pytest>=7.4"]\n'
        ),
    )
    module = FileInfo(
        relative_path=Path("src/repocontext/cli.py"),
        absolute_path=tmp_path / "src/repocontext/cli.py",
        is_text=True,
        is_binary=False,
        language="python",
        line_count=3,
        estimated_tokens=6,
        content="def main():\n    return 0\n",
    )
    test_file = FileInfo(
        relative_path=Path("tests/test_cli.py"),
        absolute_path=tmp_path / "tests/test_cli.py",
        is_text=True,
        is_binary=False,
        language="python",
        line_count=2,
        estimated_tokens=4,
        content="def test_cli():\n    assert True\n",
    )

    context = create_full_export_context(repository_info, [pyproject, module, test_file])
    rendered = render_full_export(context)

    assert "# AI Quick Start" in rendered
    assert "Project type: Python CLI project" in rendered
    assert "Primary language: Python" in rendered
    assert "Package manager: pyproject.toml" in rendered
    assert "Test framework: pytest" in rendered
    assert "Entrypoints: repocontext" in rendered
    assert "Purpose: AI-friendly exports of Git repositories." in rendered
    assert "AI Quick Start details will be expanded" not in rendered


def test_render_full_export_uses_readme_for_project_purpose(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    readme = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=3,
        estimated_tokens=8,
        content="# Example Project\n\nCreates concise repository context exports.\n",
    )

    context = create_full_export_context(repository_info, [readme])
    rendered = render_full_export(context)

    assert "Purpose: Creates concise repository context exports." in rendered


def test_render_full_export_ai_quick_start_uses_unknown_fallbacks(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    context = create_full_export_context(repository_info, [])

    rendered = render_full_export(context)

    assert "Project type: Unknown Git repository" in rendered
    assert "Primary language: Unknown" in rendered
    assert "Package manager: Unknown" in rendered
    assert "Test framework: Unknown" in rendered
    assert "Entrypoints: Unknown" in rendered
    assert "Purpose: Unknown" in rendered


def test_render_full_export_renders_file_summary_table(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    second = FileInfo(
        relative_path=Path("src/module.py"),
        absolute_path=tmp_path / "src/module.py",
        is_text=True,
        is_binary=False,
        language="python",
        line_count=2,
        estimated_tokens=8,
        content="print('hello')\nprint('world')\n",
    )
    first = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=3,
        estimated_tokens=10,
        content="# Example\n\nText\n",
    )
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )

    context = create_full_export_context(repository_info, [second, binary, first])
    rendered = render_full_export(context)

    assert "# File Summary" in rendered
    assert "Exported text files: 2" in rendered
    assert "Total lines: 5" in rendered
    assert "Estimated tokens: 18" in rendered
    assert "## Markdown (1 file)" in rendered
    assert "- `README.md` — 3 lines, ~10 tokens" in rendered
    assert "## Python (1 file)" in rendered
    assert "- `src/module.py` — 2 lines, ~8 tokens" in rendered
    file_summary_section = rendered.split("# File Summary", 1)[1].split(
        "# Repository Tree",
        1,
    )[0]

    assert "image.bin" not in file_summary_section
    assert "File Summary details will be expanded" not in file_summary_section

    readme_position = rendered.index("- `README.md` — 3 lines, ~10 tokens")
    module_position = rendered.index("- `src/module.py` — 2 lines, ~8 tokens")
    assert readme_position < module_position


def test_render_full_export_file_summary_handles_unknown_language_and_missing_counts(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    file_info = FileInfo(
        relative_path=Path("notes.unknown"),
        absolute_path=tmp_path / "notes.unknown",
        is_text=True,
        is_binary=False,
        language=None,
        line_count=None,
        estimated_tokens=None,
        content="notes\n",
    )

    context = create_full_export_context(repository_info, [file_info])
    rendered = render_full_export(context)

    assert "## Unknown (1 file)" in rendered
    assert "- `notes.unknown` — 0 lines, ~0 tokens" in rendered


def test_render_full_export_file_summary_handles_no_exportable_text_files(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )

    context = create_full_export_context(repository_info, [binary])
    rendered = render_full_export(context)

    assert "# File Summary" in rendered
    assert "No exportable text files." in rendered


def test_render_full_export_file_summary_escapes_markdown_table_pipes(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    file_info = FileInfo(
        relative_path=Path("docs/weird|name.txt"),
        absolute_path=tmp_path / "docs" / "weird|name.txt",
        is_text=True,
        is_binary=False,
        language="text",
        line_count=1,
        estimated_tokens=2,
        content="text\n",
    )

    context = create_full_export_context(repository_info, [file_info])
    rendered = render_full_export(context)

    assert "## Text (1 file)" in rendered
    assert "- `docs/weird|name.txt` — 1 line, ~2 tokens" in rendered


def test_render_full_export_renders_repository_tree(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    files = [
        FileInfo(
            relative_path=Path("src/repocontext/scanner.py"),
            absolute_path=tmp_path / "src/repocontext/scanner.py",
            is_text=True,
            is_binary=False,
            language="python",
            content="scanner\n",
        ),
        FileInfo(
            relative_path=Path("README.md"),
            absolute_path=tmp_path / "README.md",
            is_text=True,
            is_binary=False,
            language="markdown",
            content="# Readme\n",
        ),
        FileInfo(
            relative_path=Path("src/repocontext/cli.py"),
            absolute_path=tmp_path / "src/repocontext/cli.py",
            is_text=True,
            is_binary=False,
            language="python",
            content="cli\n",
        ),
        FileInfo(
            relative_path=Path("tests/test_cli.py"),
            absolute_path=tmp_path / "tests/test_cli.py",
            is_text=True,
            is_binary=False,
            language="python",
            content="test\n",
        ),
        FileInfo(
            relative_path=Path("image.bin"),
            absolute_path=tmp_path / "image.bin",
            is_text=False,
            is_binary=True,
            content=None,
        ),
    ]

    context = create_full_export_context(repository_info, files)
    rendered = render_full_export(context)

    assert "# Repository Tree" in rendered
    assert "Repository Tree rendering will be expanded" not in rendered
    assert "." in rendered
    assert "├── README.md" in rendered
    assert "├── image.bin [binary skipped]" in rendered
    assert "├── src" in rendered
    assert "│   └── repocontext" in rendered
    assert "│       ├── cli.py" in rendered
    assert "│       └── scanner.py" in rendered
    assert "└── tests" in rendered
    assert "    └── test_cli.py" in rendered


def test_render_full_export_repository_tree_marks_errored_files(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    errored = FileInfo(
        relative_path=Path("broken.txt"),
        absolute_path=tmp_path / "broken.txt",
        is_text=True,
        is_binary=False,
        content=None,
        error="Could not read file",
    )

    context = create_full_export_context(repository_info, [errored])
    rendered = render_full_export(context)

    assert "└── broken.txt [error]" in rendered


def test_render_full_export_repository_tree_handles_empty_repository(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    repository_info.tracked_files.clear()
    context = create_full_export_context(repository_info, [])

    rendered = render_full_export(context)

    repository_tree_section = rendered.split("# Repository Tree", 1)[1].split(
        "# Dependencies",
        1,
    )[0]
    assert repository_tree_section.strip() == "."



def test_render_full_export_renders_empty_database_schema_section(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    readme = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=1,
        estimated_tokens=3,
        content="# Example\n",
    )

    context = create_full_export_context(repository_info, [readme])
    rendered = render_full_export(context)

    assert "# Database Schema" in rendered
    database_schema_section = rendered.split("# Database Schema", 1)[1].split(
        "# Complete Source Export",
        1,
    )[0]

    assert "## Summary" in database_schema_section
    assert "Database files: 0" in database_schema_section
    assert "SQL schema files: 0" in database_schema_section
    assert "Tables: 0" in database_schema_section
    assert "Views: 0" in database_schema_section
    assert "No database schema files detected." in database_schema_section
    assert "No schema warnings." in database_schema_section


def test_render_full_export_renders_sqlite_database_schema_without_data(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    database_path = tmp_path / "app.sqlite"

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute("INSERT INTO users (name) VALUES ('VerySecretUserName')")
        connection.commit()
    finally:
        connection.close()

    database_file = FileInfo(
        relative_path=Path("app.sqlite"),
        absolute_path=database_path,
        is_text=False,
        is_binary=True,
        language=None,
        content=None,
    )

    context = create_full_export_context(repository_info, [database_file])
    rendered = render_full_export(context)
    database_schema_section = rendered.split("# Database Schema", 1)[1].split(
        "# Complete Source Export",
        1,
    )[0]

    assert "Database files: 1" in database_schema_section
    assert "- app.sqlite" in database_schema_section
    assert "### users" in database_schema_section
    assert "Source: app.sqlite" in database_schema_section
    assert "- id INTEGER PRIMARY KEY NULL" in database_schema_section
    assert "- name TEXT NOT NULL" in database_schema_section
    assert "VerySecretUserName" not in rendered


def test_render_full_export_renders_sql_schema_file_tables(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    sql_path = tmp_path / "schema.sql"
    sql_content = """
    CREATE TABLE roles (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """
    sql_path.write_text(sql_content, encoding="utf-8")

    sql_file = FileInfo(
        relative_path=Path("schema.sql"),
        absolute_path=sql_path,
        is_text=True,
        is_binary=False,
        language="sql",
        line_count=4,
        estimated_tokens=12,
        content=sql_content,
    )

    context = create_full_export_context(repository_info, [sql_file])
    rendered = render_full_export(context)
    database_schema_section = rendered.split("# Database Schema", 1)[1].split(
        "# Complete Source Export",
        1,
    )[0]

    assert "SQL schema files: 1" in database_schema_section
    assert "- schema.sql" in database_schema_section
    assert "### roles" in database_schema_section
    assert "- id INTEGER PRIMARY KEY" in database_schema_section
    assert "- name TEXT NOT NULL" in database_schema_section
    assert "CREATE TABLE roles" in database_schema_section


def test_render_full_export_renders_schema_warnings_for_bad_database(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    broken_path = tmp_path / "broken.sqlite"
    broken_path.write_bytes(b"not sqlite")

    broken_file = FileInfo(
        relative_path=Path("broken.sqlite"),
        absolute_path=broken_path,
        is_text=False,
        is_binary=True,
        language=None,
        content=None,
    )

    context = create_full_export_context(repository_info, [broken_file])
    rendered = render_full_export(context)
    database_schema_section = rendered.split("# Database Schema", 1)[1].split(
        "# Complete Source Export",
        1,
    )[0]

    assert "Warnings: 1" in database_schema_section
    assert "broken.sqlite: file extension suggests SQLite but magic header is missing" in database_schema_section


def test_render_full_export_database_schema_appears_before_complete_source_export(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    context = create_full_export_context(repository_info, [])

    rendered = render_full_export(context)

    assert rendered.index("# Dependencies") < rendered.index("# Database Schema")
    assert rendered.index("# Database Schema") < rendered.index("# Complete Source Export")

def test_render_full_export_renders_complete_source_export(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    module = FileInfo(
        relative_path=Path("src/module.py"),
        absolute_path=tmp_path / "src/module.py",
        is_text=True,
        is_binary=False,
        language="python",
        line_count=1,
        estimated_tokens=4,
        content="print('hello')\n",
    )
    readme = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=2,
        estimated_tokens=8,
        content="# Example\n\nOverview\n",
    )
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )

    context = create_full_export_context(repository_info, [module, binary, readme])
    rendered = render_full_export(context)
    code_fence = chr(96) * 3

    assert "# Complete Source Export" in rendered
    assert "Complete Source Export rendering will be expanded" not in rendered

    assert "## File: README.md" in rendered
    assert f"{code_fence}markdown" in rendered
    assert "# Example\n\nOverview\n" in rendered

    assert "## File: src/module.py" in rendered
    assert f"{code_fence}python" in rendered
    assert "print('hello')\n" in rendered

    assert "## File: image.bin" not in rendered

    readme_position = rendered.index("## File: README.md")
    module_position = rendered.index("## File: src/module.py")
    assert readme_position < module_position


def test_render_full_export_complete_source_export_handles_no_exportable_files(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )

    context = create_full_export_context(repository_info, [binary])
    rendered = render_full_export(context)

    complete_source_section = rendered.split("# Complete Source Export", 1)[1].split(
        "# Warnings",
        1,
    )[0]
    assert "No exportable text files." in complete_source_section


def test_render_full_export_complete_source_export_uses_longer_fence_for_nested_fences(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    backtick = chr(96)
    nested_fence = backtick * 3
    longer_fence = backtick * 4
    readme = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=5,
        estimated_tokens=20,
        content=(
            "# Example\n\n"
            f"{nested_fence}python\n"
            "print('inside markdown')\n"
            f"{nested_fence}\n"
        ),
    )

    context = create_full_export_context(repository_info, [readme])
    rendered = render_full_export(context)

    complete_source_section = rendered.split("# Complete Source Export", 1)[1].split(
        "# Warnings",
        1,
    )[0]

    assert f"{longer_fence}markdown" in complete_source_section
    assert f"{nested_fence}python" in complete_source_section
    assert complete_source_section.rstrip().endswith(longer_fence)


def test_render_full_export_complete_source_export_uses_text_for_unknown_language(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    file_info = FileInfo(
        relative_path=Path("notes.unknown"),
        absolute_path=tmp_path / "notes.unknown",
        is_text=True,
        is_binary=False,
        language=None,
        line_count=1,
        estimated_tokens=2,
        content="notes\n",
    )

    context = create_full_export_context(repository_info, [file_info])
    rendered = render_full_export(context)
    code_fence = chr(96) * 3

    assert f"{code_fence}text" in rendered
    assert "notes\n" in rendered


def test_render_full_export_warnings_renders_no_warnings_state(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    exported = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=1,
        estimated_tokens=3,
        content="# Example\n",
    )

    context = create_full_export_context(repository_info, [exported])
    rendered = render_full_export(context)

    warnings_section = rendered.split("# Warnings", 1)[1]
    assert "No warnings." in warnings_section
    assert "Warning rendering will be expanded" not in warnings_section


def test_render_full_export_warnings_reports_binary_and_errored_files(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    exported = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=1,
        estimated_tokens=3,
        content="# Example\n",
    )
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )
    errored = FileInfo(
        relative_path=Path("broken.txt"),
        absolute_path=tmp_path / "broken.txt",
        is_text=True,
        is_binary=False,
        content=None,
        error="Permission denied",
    )

    context = create_full_export_context(
        repository_info,
        [exported, binary, errored],
        warnings=["Manual warning"],
    )
    rendered = render_full_export(context)

    warnings_section = rendered.split("# Warnings", 1)[1]
    assert "- Manual warning" in warnings_section
    assert "- Skipped binary file: image.bin" in warnings_section
    assert "- Could not read file: broken.txt (Permission denied)" in warnings_section
    assert "No warnings." not in warnings_section


def test_render_full_export_warnings_reports_empty_repository(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    repository_info.tracked_files.clear()

    context = create_full_export_context(repository_info, [])
    rendered = render_full_export(context)

    warnings_section = rendered.split("# Warnings", 1)[1]
    assert "- No Git-tracked files found." in warnings_section
    assert "- No exportable text files found." not in warnings_section


def test_render_full_export_warnings_reports_no_exportable_text_files(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )

    context = create_full_export_context(repository_info, [binary])
    rendered = render_full_export(context)

    warnings_section = rendered.split("# Warnings", 1)[1]
    assert "- Skipped binary file: image.bin" in warnings_section
    assert "- No exportable text files found." in warnings_section


def test_write_full_export_overwrites_existing_full_txt(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    existing_output = tmp_path / "full.txt"
    existing_output.write_text("old export\n", encoding="utf-8")
    file_info = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        language="markdown",
        line_count=1,
        estimated_tokens=3,
        content="# New Export\n",
    )
    context = create_full_export_context(repository_info, [file_info])

    output_path = write_full_export(context)

    assert output_path == existing_output
    content = output_path.read_text(encoding="utf-8")
    assert "old export" not in content
    assert "# New Export" in content


def test_write_full_export_uses_atomic_temporary_file_and_cleans_it_up(
    tmp_path: Path,
) -> None:
    repository_info = make_repository_info(tmp_path)
    context = create_full_export_context(repository_info, [])

    output_path = write_full_export(context)

    temporary_path = tmp_path / ".full.txt.tmp"
    assert output_path == tmp_path / "full.txt"
    assert output_path.exists()
    assert not temporary_path.exists()


def test_write_full_export_supports_custom_output_path(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    context = create_full_export_context(repository_info, [])
    custom_output = tmp_path / "exports" / "custom-full.txt"

    output_path = write_full_export(context, custom_output)

    assert output_path == custom_output.resolve()
    assert custom_output.exists()
    assert "# AI Quick Start" in custom_output.read_text(encoding="utf-8")
    assert not (tmp_path / "full.txt").exists()


def test_write_full_export_writes_utf8_output(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    unicode_file = FileInfo(
        relative_path=Path("unicode.txt"),
        absolute_path=tmp_path / "unicode.txt",
        is_text=True,
        is_binary=False,
        language="text",
        line_count=1,
        estimated_tokens=8,
        content="äöü ÄÖÜ 😀 こんにちは\n",
    )
    context = create_full_export_context(repository_info, [unicode_file])

    output_path = write_full_export(context)

    assert "äöü ÄÖÜ 😀 こんにちは" in output_path.read_text(encoding="utf-8")


def test_full_export_context_counts_file_types_from_scanned_files(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    files = [
        FileInfo(relative_path=Path("README.md"), absolute_path=tmp_path / "README.md"),
        FileInfo(relative_path=Path("src/module.py"), absolute_path=tmp_path / "src/module.py"),
        FileInfo(relative_path=Path("image.bin"), absolute_path=tmp_path / "image.bin"),
        FileInfo(relative_path=Path("LICENSE"), absolute_path=tmp_path / "LICENSE"),
    ]

    context = create_full_export_context(repository_info, files)

    assert context.file_type_counts == (
        (".bin", 1),
        (".md", 1),
        (".py", 1),
        ("[no extension]", 1),
    )


def test_render_full_export_renders_complete_repository_statistics(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    exported = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        line_count=2,
        estimated_tokens=6,
        content="# Example\nText\n",
    )
    binary = FileInfo(
        relative_path=Path("image.bin"),
        absolute_path=tmp_path / "image.bin",
        is_text=False,
        is_binary=True,
        content=None,
    )
    errored = FileInfo(
        relative_path=Path("broken.txt"),
        absolute_path=tmp_path / "broken.txt",
        is_text=True,
        is_binary=False,
        content=None,
        error="Could not read file",
    )

    context = create_full_export_context(repository_info, [binary, errored, exported])
    rendered = render_full_export(context)

    assert "# Repository Statistics" in rendered
    assert "Total tracked files: 3" in rendered
    assert "Scanned files: 3" in rendered
    assert "Exported text files: 1" in rendered
    assert "Skipped binary files: 1" in rendered
    assert "Errored files: 1" in rendered
    assert "Total lines: 2" in rendered
    assert "Estimated tokens: 6" in rendered
    assert "File types:" in rendered
    assert "- .bin: 1" in rendered
    assert "- .md: 1" in rendered
    assert "- .txt: 1" in rendered
    assert "Repository statistics will be expanded" not in rendered


def test_render_full_export_contains_sections_in_stable_order(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    context = create_full_export_context(repository_info, [])

    rendered = render_full_export(context)

    positions = [rendered.index(heading) for heading in iter_full_export_headings()]
    assert positions == sorted(positions)


def test_render_full_export_includes_basic_orchestration_counts(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    exported = FileInfo(
        relative_path=Path("README.md"),
        absolute_path=tmp_path / "README.md",
        is_text=True,
        is_binary=False,
        line_count=1,
        estimated_tokens=4,
        content="readme\n",
    )

    context = create_full_export_context(repository_info, [exported])
    rendered = render_full_export(context)

    assert "Total tracked files: 3" in rendered
    assert "Scanned files: 1" in rendered
    assert "Exported text files: 1" in rendered


def test_write_full_export_writes_full_txt_to_repository_root(tmp_path: Path) -> None:
    repository_info = make_repository_info(tmp_path)
    context = create_full_export_context(repository_info, [])

    output_path = write_full_export(context)

    assert output_path == tmp_path / "full.txt"
    assert output_path.exists()
    assert "# AI Quick Start" in output_path.read_text(encoding="utf-8")


def test_full_command_masks_secret_values_and_reports_summary(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)

    clear_secret = "sk-live-1234567890abcdefSECRET"
    (repo / "config.py").write_text(
        f'OPENAI_API_KEY = "{clear_secret}"\nprint("safe")\n',
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "config.py"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=RepoContext Test",
            "-c",
            "user.email=repocontext@example.invalid",
            "commit",
            "-m",
            "init",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src_path = str(project_root / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [sys.executable, "-m", "repocontext", "full"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr + result.stdout

    full_export = (repo / "full.txt").read_text(encoding="utf-8")

    assert clear_secret not in full_export
    assert "***REDACTED***" in full_export
    assert "# Secret Detection" in full_export
    assert "Total findings: 1" in full_export
    assert "- API_KEY: 1" in full_export
    assert 'print("safe")' in full_export


def test_full_secret_detection_section_is_inserted_before_complete_source_export():
    from repocontext.exporters.full import (
        _format_full_secret_detection_section,
        _insert_full_secret_detection_section,
    )
    from repocontext.secrets import SecretFinding

    finding = SecretFinding(
        file_path="config.py",
        line_number=1,
        secret_type="API_KEY",
        matched_text='OPENAI_API_KEY = "sk-live-1234567890abcdefSECRET"',
        masked_text='OPENAI_API_KEY = "sk-l***REDACTED***CRET"',
        variable_name="OPENAI_API_KEY",
        confidence="high",
    )

    rendered = "\n".join(
        [
            "# AI Quick Start",
            "",
            "# Repository Statistics",
            "",
            "# Complete Source Export",
            "",
            "## File: config.py",
            "",
            'OPENAI_API_KEY = "sk-l***REDACTED***CRET"',
            "",
        ]
    )

    secret_section = _format_full_secret_detection_section([finding])
    output = _insert_full_secret_detection_section(rendered, secret_section)

    assert "# Secret Detection" in output
    assert output.index("# Secret Detection") < output.index("# Complete Source Export")
    assert "Total findings: 1" in output
    assert "API_KEY: 1" in output
    assert "sk-live-1234567890abcdefSECRET" not in output

