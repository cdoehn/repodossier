from pathlib import Path

from repocontext.exporters.full import (
    FULL_EXPORT_SECTION_HEADINGS,
    FULL_EXPORT_SECTION_ORDER,
    FullExportContext,
    create_full_export_context,
    iter_full_export_headings,
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
