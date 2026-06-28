from pathlib import Path

from repocontext.exporters.ai import (
    AI_EXPORT_FILENAME,
    AI_EXPORT_SECTION_HEADINGS,
    AI_EXPORT_SECTION_ORDER,
    AIExportContext,
    create_ai_export_context,
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
