import subprocess
from pathlib import Path

from repocontext.exporters.docs import (
    ARCHITECTURE_DOCUMENTATION_CATEGORY,
    CHANGELOG_AND_CONTRIBUTION_CATEGORY,
    DOCUMENTATION_CATEGORY_ORDER,
    LICENSE_CATEGORY,
    OTHER_DOCS_CATEGORY,
    PRIMARY_DOCUMENTATION_CATEGORY,
    SPECIFICATION_DOCUMENTATION_CATEGORY,
    TASKS_AND_ROADMAP_CATEGORY,
    DocumentationExportContext,
    DocumentationFile,
    build_docs_export_context,
    categorize_documentation_file,
    create_docs_export_context,
    is_documentation_file,
)
from repocontext.exporters.full import create_full_export_context
from repocontext.git import RepositoryInfo, TrackedFile
from repocontext.models import FileInfo


def run_git_command(repository_root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


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
            TrackedFile(path=Path("REPOCONTEXT_SPEC_v1.3.txt")),
            TrackedFile(path=Path("docs/usage.md")),
            TrackedFile(path=Path("src/app.py")),
            TrackedFile(path=Path("full.txt")),
        ],
        commit_metadata=None,
    )


def make_file(
    tmp_path: Path,
    relative_path: str,
    *,
    is_text: bool = True,
    is_binary: bool = False,
    content: str | None = "content\n",
    line_count: int | None = 1,
    estimated_tokens: int | None = 2,
    error: str | None = None,
) -> FileInfo:
    return FileInfo(
        relative_path=Path(relative_path),
        absolute_path=tmp_path / relative_path,
        is_text=is_text,
        is_binary=is_binary,
        content=content,
        line_count=line_count,
        estimated_tokens=estimated_tokens,
        error=error,
    )


def make_docs_context(tmp_path: Path, files: list[FileInfo]) -> DocumentationExportContext:
    full_context = create_full_export_context(make_repository_info(tmp_path), files)
    return create_docs_export_context(full_context)


def test_documentation_file_detection_accepts_primary_documentation_files():
    assert is_documentation_file("README.md")
    assert is_documentation_file("README.rst")
    assert is_documentation_file("README.txt")
    assert is_documentation_file("README")
    assert categorize_documentation_file("README.md") == PRIMARY_DOCUMENTATION_CATEGORY


def test_documentation_file_detection_accepts_architecture_and_spec_files():
    assert is_documentation_file("ARCHITECTURE.md")
    assert is_documentation_file("REPOCONTEXT_ARCHITECTURE.md")
    assert is_documentation_file("SPEC.md")
    assert is_documentation_file("SPEC.txt")
    assert is_documentation_file("REPOCONTEXT_SPEC_v1.3.txt")

    assert categorize_documentation_file("REPOCONTEXT_ARCHITECTURE.md") == ARCHITECTURE_DOCUMENTATION_CATEGORY
    assert categorize_documentation_file("REPOCONTEXT_SPEC_v1.3.txt") == SPECIFICATION_DOCUMENTATION_CATEGORY


def test_documentation_file_detection_accepts_tasks_roadmap_and_planning_files():
    assert is_documentation_file("TASKS.md")
    assert is_documentation_file("ROADMAP.md")
    assert is_documentation_file("REPOCONTEXT_ROADMAP.md")
    assert is_documentation_file("planning/REPOCONTEXT_ROADMAP.md")
    assert is_documentation_file("planning/MILESTONE9.md")

    assert categorize_documentation_file("TASKS.md") == TASKS_AND_ROADMAP_CATEGORY
    assert categorize_documentation_file("planning/REPOCONTEXT_ROADMAP.md") == TASKS_AND_ROADMAP_CATEGORY


def test_documentation_file_detection_accepts_docs_directory_text_files():
    assert is_documentation_file("docs/usage.md")
    assert is_documentation_file("docs/reference.txt")
    assert is_documentation_file("docs/nested/guide.rst")

    assert categorize_documentation_file("docs/usage.md") == OTHER_DOCS_CATEGORY


def test_documentation_file_detection_accepts_changelog_contributing_and_license():
    assert is_documentation_file("CHANGELOG.md")
    assert is_documentation_file("CONTRIBUTING.md")
    assert is_documentation_file("LICENSE")
    assert is_documentation_file("LICENSE.md")

    assert categorize_documentation_file("CHANGELOG.md") == CHANGELOG_AND_CONTRIBUTION_CATEGORY
    assert categorize_documentation_file("CONTRIBUTING.md") == CHANGELOG_AND_CONTRIBUTION_CATEGORY
    assert categorize_documentation_file("LICENSE") == LICENSE_CATEGORY


def test_documentation_file_detection_rejects_code_tests_and_generated_exports():
    assert not is_documentation_file("src/repocontext/cli.py")
    assert not is_documentation_file("tests/test_cli.py")
    assert not is_documentation_file("pyproject.toml")

    assert not is_documentation_file("full.txt")
    assert not is_documentation_file("ai.txt")
    assert not is_documentation_file("docs.txt")
    assert not is_documentation_file("changed.txt")
    assert not is_documentation_file("docs/docs.txt")


def test_documentation_file_detection_rejects_binary_or_non_text_docs():
    assert not is_documentation_file("docs/manual.pdf")
    assert not is_documentation_file("docs/archive.zip")
    assert not is_documentation_file("README.md", is_binary=True)


def test_documentation_category_order_is_stable():
    assert DOCUMENTATION_CATEGORY_ORDER == (
        "Primary documentation",
        "Architecture documentation",
        "Specification documentation",
        "Tasks and roadmap",
        "Changelog and contribution docs",
        "License",
        "Other docs",
    )


def test_documentation_file_detection_is_case_insensitive():
    assert is_documentation_file("readme.MD")
    assert is_documentation_file("Docs/Usage.MD")
    assert is_documentation_file("planning/milestone9.MD")
    assert categorize_documentation_file("readme.MD") == PRIMARY_DOCUMENTATION_CATEGORY


def test_documentation_file_wraps_file_info_and_category(tmp_path: Path):
    file_info = make_file(
        tmp_path,
        "README.md",
        content="# Title\nBody\n",
        line_count=2,
        estimated_tokens=7,
    )
    documentation_file = DocumentationFile(
        file_info=file_info,
        category=PRIMARY_DOCUMENTATION_CATEGORY,
    )

    assert documentation_file.relative_path == Path("README.md")
    assert documentation_file.line_count == 2
    assert documentation_file.estimated_tokens == 7
    assert documentation_file.content == "# Title\nBody\n"


def test_create_docs_export_context_filters_to_exportable_documentation_files(tmp_path: Path):
    readme = make_file(tmp_path, "README.md", line_count=2, estimated_tokens=8)
    spec = make_file(tmp_path, "REPOCONTEXT_SPEC_v1.3.txt", line_count=3, estimated_tokens=12)
    code = make_file(tmp_path, "src/app.py", line_count=10, estimated_tokens=40)
    generated = make_file(tmp_path, "full.txt", line_count=100, estimated_tokens=400)
    binary_doc = make_file(
        tmp_path,
        "docs/manual.pdf",
        is_text=False,
        is_binary=True,
        content=None,
        line_count=None,
        estimated_tokens=None,
    )

    context = make_docs_context(tmp_path, [code, generated, spec, readme, binary_doc])

    assert [document.relative_path.as_posix() for document in context.documentation_files] == [
        "README.md",
        "REPOCONTEXT_SPEC_v1.3.txt",
    ]
    assert context.skipped_files == (binary_doc,)
    assert context.total_line_count == 5
    assert context.estimated_token_count == 20


def test_create_docs_export_context_keeps_category_order_deterministic(tmp_path: Path):
    usage = make_file(tmp_path, "docs/usage.md")
    roadmap = make_file(tmp_path, "planning/REPOCONTEXT_ROADMAP.md")
    readme = make_file(tmp_path, "README.md")

    context = make_docs_context(tmp_path, [usage, roadmap, readme])

    assert [document.relative_path.as_posix() for document in context.documentation_files] == [
        "README.md",
        "planning/REPOCONTEXT_ROADMAP.md",
        "docs/usage.md",
    ]


def test_create_docs_export_context_exposes_repository_and_scan_data(tmp_path: Path):
    readme = make_file(tmp_path, "README.md")
    code = make_file(tmp_path, "src/app.py")
    full_context = create_full_export_context(
        make_repository_info(tmp_path),
        [readme, code],
        warnings=["upstream warning"],
    )

    context = create_docs_export_context(full_context)

    assert context.full_context is full_context
    assert context.repository_root == tmp_path
    assert context.repository_info == full_context.repository_info
    assert context.scanned_files == (readme, code)


def test_create_docs_export_context_warns_when_no_documentation_files_exist(tmp_path: Path):
    code = make_file(tmp_path, "src/app.py")
    context = make_docs_context(tmp_path, [code])

    assert context.documentation_files == ()
    assert context.total_line_count == 0
    assert context.estimated_token_count == 0
    assert context.warnings == ("No documentation files found.",)


def test_create_docs_export_context_keeps_unreadable_docs_as_skipped_files(tmp_path: Path):
    broken = make_file(
        tmp_path,
        "docs/broken.md",
        content=None,
        error="Could not read file",
    )

    context = make_docs_context(tmp_path, [broken])

    assert context.documentation_files == ()
    assert context.skipped_files == (broken,)
    assert "Skipped unreadable documentation file: docs/broken.md: Could not read file" in context.warnings


def test_build_docs_export_context_reuses_full_export_pipeline_and_git_tracked_files(tmp_path: Path):
    run_git_command(tmp_path, "init")
    run_git_command(tmp_path, "config", "user.email", "tester@example.com")
    run_git_command(tmp_path, "config", "user.name", "Tester")

    (tmp_path / "src").mkdir()
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "full.txt").write_text("generated\n", encoding="utf-8")
    (tmp_path / "UNTRACKED_README.md").write_text("# Ignore me\n", encoding="utf-8")

    run_git_command(tmp_path, "add", "README.md", "src/app.py", "full.txt")
    run_git_command(tmp_path, "commit", "-m", "Initial commit")

    context = build_docs_export_context(tmp_path)

    assert [document.relative_path.as_posix() for document in context.documentation_files] == [
        "README.md",
    ]
    assert [file_info.relative_path.as_posix() for file_info in context.scanned_files] == [
        "README.md",
        "full.txt",
        "src/app.py",
    ]
