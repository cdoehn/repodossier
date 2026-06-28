from pathlib import Path

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
        "complete_source_export",
        "warnings",
    )


def test_full_export_section_headings_are_markdown_headings() -> None:
    assert iter_full_export_headings() == (
        "# AI Quick Start",
        "# Repository Statistics",
        "# File Summary",
        "# Repository Tree",
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
    assert "| Path | Language | Lines | Tokens |" in rendered
    assert "| --- | --- | ---: | ---: |" in rendered
    assert "| README.md | Markdown | 3 | 10 |" in rendered
    assert "| src/module.py | Python | 2 | 8 |" in rendered
    assert "image.bin |" not in rendered
    assert "File Summary details will be expanded" not in rendered

    readme_position = rendered.index("| README.md | Markdown | 3 | 10 |")
    module_position = rendered.index("| src/module.py | Python | 2 | 8 |")
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

    assert "| notes.unknown | Unknown | 0 | 0 |" in rendered


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

    assert "| docs/weird\\|name.txt | Text | 1 | 2 |" in rendered


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
        "# Complete Source Export",
        1,
    )[0]
    assert repository_tree_section.strip() == "."


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
