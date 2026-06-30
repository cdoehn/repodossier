import subprocess
from pathlib import Path

from repocontext.exporters import (
    DOCS_EXPORT_FILENAME as PUBLIC_DOCS_EXPORT_FILENAME,
    generate_docs_export as public_generate_docs_export,
    write_docs_export as public_write_docs_export,
)
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
from repocontext.exporters.docs import (
    DOCS_EXPORT_DOCUMENT_HEADING,
    DOCS_EXPORT_SECTION_HEADINGS,
    DOCS_EXPORT_SECTION_ORDER,
    iter_docs_export_headings,
    render_docs_export,
    write_docs_export,
    generate_docs_export,
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
            TrackedFile(path=Path("planning/spec.md")),
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
    assert is_documentation_file("architecture.md")
    assert is_documentation_file("SPEC.md")
    assert is_documentation_file("SPEC.txt")
    assert is_documentation_file("planning/spec.md")

    assert categorize_documentation_file("architecture.md") == ARCHITECTURE_DOCUMENTATION_CATEGORY
    assert categorize_documentation_file("planning/spec.md") == SPECIFICATION_DOCUMENTATION_CATEGORY


def test_documentation_file_detection_accepts_tasks_roadmap_and_planning_files():
    assert is_documentation_file("TASKS.md")
    assert is_documentation_file("ROADMAP.md")
    assert is_documentation_file("REPOCONTEXT_ROADMAP.md")
    assert is_documentation_file("planning/archive/1.0.0/roadmap.md")
    assert is_documentation_file("planning/archive/1.0.0/milestone9.md")

    assert categorize_documentation_file("TASKS.md") == TASKS_AND_ROADMAP_CATEGORY
    assert categorize_documentation_file("planning/archive/1.0.0/roadmap.md") == TASKS_AND_ROADMAP_CATEGORY


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


def test_docs_export_section_order_matches_milestone_9_structure():
    assert DOCS_EXPORT_DOCUMENT_HEADING == "# Documentation Context"
    assert DOCS_EXPORT_SECTION_ORDER == (
        "documentation_quick_start",
        "documentation_summary",
        "documentation_files",
        "extracted_documents",
        "warnings",
    )
    assert iter_docs_export_headings() == (
        "# Documentation Context",
        "## Documentation Quick Start",
        "## Documentation Summary",
        "## Documentation Files",
        "## Extracted Documents",
        "## Warnings",
    )


def test_docs_export_headings_cover_every_ordered_section():
    assert set(DOCS_EXPORT_SECTION_HEADINGS) == set(DOCS_EXPORT_SECTION_ORDER)


def test_render_docs_export_contains_required_sections_in_stable_order(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [
            make_file(tmp_path, "README.md", content="# Readme\n"),
            make_file(tmp_path, "planning/spec.md", content="Spec\n"),
        ],
    )

    rendered = render_docs_export(context)

    positions = [rendered.index(heading) for heading in iter_docs_export_headings()]
    assert positions == sorted(positions)
    assert rendered.endswith("\n")


def test_render_docs_export_quick_start_summarizes_repository_docs(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [
            make_file(tmp_path, "README.md", line_count=2, estimated_tokens=1200),
            make_file(
                tmp_path,
                "planning/archive/1.0.0/roadmap.md",
                line_count=3,
                estimated_tokens=2400,
            ),
        ],
    )

    rendered = render_docs_export(context)

    assert "Repository: example" in rendered
    assert "Documentation files: 2" in rendered
    assert "Total documentation lines: 5" in rendered
    assert "Estimated documentation tokens: 3,600" in rendered
    assert "Purpose: Documentation-only export for AI review." in rendered
    assert "- Primary documentation: 1" in rendered
    assert "- Tasks and roadmap: 1" in rendered


def test_render_docs_export_summary_groups_files_by_category(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [
            make_file(tmp_path, "docs/usage.md", line_count=7, estimated_tokens=70),
            make_file(tmp_path, "README.md", line_count=2, estimated_tokens=20),
            make_file(
                tmp_path,
                "architecture.md",
                line_count=5,
                estimated_tokens=50,
            ),
        ],
    )

    rendered = render_docs_export(context)

    assert "Primary documentation:\n- README.md — 2 lines, ~20 tokens" in rendered
    assert (
        "Architecture documentation:\n"
        "- architecture.md — 5 lines, ~50 tokens"
    ) in rendered
    assert "Other docs:\n- docs/usage.md — 7 lines, ~70 tokens" in rendered
    assert rendered.index("Primary documentation:") < rendered.index("Architecture documentation:")
    assert rendered.index("Architecture documentation:") < rendered.index("Other docs:")


def test_render_docs_export_manifest_lists_docs_as_markdown_table(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [
            make_file(tmp_path, "README.md", line_count=2, estimated_tokens=20),
            make_file(tmp_path, "docs/usage.md", line_count=3, estimated_tokens=30),
        ],
    )

    rendered = render_docs_export(context)

    assert "| Path | Category | Lines | Tokens |" in rendered
    assert "| --- | --- | ---: | ---: |" in rendered
    assert "| README.md | Primary documentation | 2 | 20 |" in rendered
    assert "| docs/usage.md | Other docs | 3 | 30 |" in rendered


def test_render_docs_export_extracts_document_contents_and_excludes_code(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [
            make_file(tmp_path, "README.md", content="# Readme\nBody\n"),
            make_file(tmp_path, "src/app.py", content="print('no')\n"),
        ],
    )

    rendered = render_docs_export(context)

    assert "### File: README.md" in rendered
    assert "```markdown\n# Readme\nBody\n```" in rendered
    assert "### File: src/app.py" not in rendered
    assert "print('no')" not in rendered


def test_render_docs_export_uses_longer_fence_for_markdown_with_code_fences(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [
            make_file(
                tmp_path,
                "README.md",
                content="# Readme\n\n```python\nprint('nested')\n```\n",
            ),
        ],
    )

    rendered = render_docs_export(context)

    assert "````markdown\n# Readme" in rendered
    assert "\n````\n\n## Warnings" in rendered


def test_render_docs_export_renders_warnings_or_no_warning_state(tmp_path: Path):
    clean_context = make_docs_context(tmp_path, [make_file(tmp_path, "README.md")])
    broken_context = make_docs_context(
        tmp_path,
        [
            make_file(
                tmp_path,
                "docs/broken.md",
                content=None,
                error="Could not read file",
            )
        ],
    )

    clean_rendered = render_docs_export(clean_context)
    broken_rendered = render_docs_export(broken_context)

    assert "## Warnings\n\nNo warnings." in clean_rendered
    assert "- No documentation files found." in broken_rendered
    assert (
        "- Skipped unreadable documentation file: docs/broken.md: Could not read file"
        in broken_rendered
    )


def test_render_docs_export_handles_no_documentation_files(tmp_path: Path):
    context = make_docs_context(tmp_path, [make_file(tmp_path, "src/app.py")])

    rendered = render_docs_export(context)

    assert "Documentation files: 0" in rendered
    assert "Document types:\n- none" in rendered
    assert "No documentation files found." in rendered
    assert "No documentation files exported." in rendered
    assert "No documentation files available for extraction." in rendered


def test_documentation_file_detection_is_case_insensitive():
    assert is_documentation_file("readme.MD")
    assert is_documentation_file("Docs/Usage.MD")
    assert is_documentation_file("planning/archive/1.0.0/milestone9.MD")
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
    spec = make_file(tmp_path, "planning/spec.md", line_count=3, estimated_tokens=12)
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
        "planning/spec.md",
    ]
    assert context.skipped_files == (binary_doc, generated)
    assert "Skipped binary documentation file: docs/manual.pdf" in context.warnings
    assert "Skipped generated RepoContext export file: full.txt" in context.warnings
    assert context.total_line_count == 5
    assert context.estimated_token_count == 20


def test_create_docs_export_context_keeps_category_order_deterministic(tmp_path: Path):
    usage = make_file(tmp_path, "docs/usage.md")
    roadmap = make_file(tmp_path, "planning/archive/1.0.0/roadmap.md")
    readme = make_file(tmp_path, "README.md")

    context = make_docs_context(tmp_path, [usage, roadmap, readme])

    assert [document.relative_path.as_posix() for document in context.documentation_files] == [
        "README.md",
        "planning/archive/1.0.0/roadmap.md",
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


def test_write_docs_export_defaults_to_repository_root_docs_txt(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [make_file(tmp_path, "README.md", content="# Readme\n")],
    )

    output_path = write_docs_export(context)

    assert output_path == tmp_path / "docs.txt"
    assert output_path.read_text(encoding="utf-8").startswith("# Documentation Context")
    assert not (tmp_path / ".docs.txt.tmp").exists()


def test_write_docs_export_overwrites_existing_docs_txt(tmp_path: Path):
    (tmp_path / "docs.txt").write_text("old docs export\n", encoding="utf-8")
    context = make_docs_context(
        tmp_path,
        [make_file(tmp_path, "README.md", content="# New docs\n")],
    )

    output_path = write_docs_export(context)

    content = output_path.read_text(encoding="utf-8")
    assert "old docs export" not in content
    assert "# New docs" in content


def test_write_docs_export_supports_custom_output_path(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [make_file(tmp_path, "README.md", content="# Readme\n")],
    )
    output_path = tmp_path / "custom" / "documentation.txt"

    written_path = write_docs_export(context, output_path)

    assert written_path == output_path
    assert output_path.read_text(encoding="utf-8").startswith("# Documentation Context")


def test_write_docs_export_writes_utf8_output(tmp_path: Path):
    context = make_docs_context(
        tmp_path,
        [make_file(tmp_path, "README.md", content="# Grüße\n")],
    )

    output_path = write_docs_export(context)

    assert "Grüße" in output_path.read_text(encoding="utf-8")


def test_generate_docs_export_writes_docs_txt_for_tracked_documentation_repo(tmp_path: Path):
    run_git_command(tmp_path, "init")
    run_git_command(tmp_path, "config", "user.email", "tester@example.com")
    run_git_command(tmp_path, "config", "user.name", "Tester")

    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

    run_git_command(tmp_path, "add", "README.md", "src/app.py")
    run_git_command(tmp_path, "commit", "-m", "Initial commit")

    output_path = generate_docs_export(tmp_path)

    assert output_path == tmp_path / "docs.txt"
    content = output_path.read_text(encoding="utf-8")
    assert "# Documentation Context" in content
    assert "### File: README.md" in content
    assert "### File: src/app.py" not in content
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8").count("docs.txt") == 1


def test_public_exporter_init_exposes_docs_export_helpers():
    assert PUBLIC_DOCS_EXPORT_FILENAME == "docs.txt"
    assert public_generate_docs_export is generate_docs_export
    assert public_write_docs_export is write_docs_export


def test_create_docs_export_context_warns_for_tracked_generated_exports(tmp_path: Path):
    readme = make_file(tmp_path, "README.md", content="# Readme\n")
    previous_docs_export = make_file(
        tmp_path,
        "docs.txt",
        content="# Old Documentation Context\nSHOULD_NOT_APPEAR\n",
        line_count=2,
        estimated_tokens=20,
    )
    previous_ai_export = make_file(
        tmp_path,
        "ai.txt",
        content="# AI CONTEXT\nSHOULD_NOT_APPEAR\n",
        line_count=2,
        estimated_tokens=20,
    )

    context = make_docs_context(
        tmp_path,
        [previous_docs_export, readme, previous_ai_export],
    )
    rendered = render_docs_export(context)

    assert [document.relative_path.as_posix() for document in context.documentation_files] == [
        "README.md",
    ]
    assert [file_info.relative_path.as_posix() for file_info in context.skipped_files] == [
        "ai.txt",
        "docs.txt",
    ]
    assert "Skipped generated RepoContext export file: ai.txt" in context.warnings
    assert "Skipped generated RepoContext export file: docs.txt" in context.warnings
    assert "SHOULD_NOT_APPEAR" not in rendered
    assert "### File: docs.txt" not in rendered
    assert "### File: ai.txt" not in rendered


def test_generate_docs_export_is_stable_when_docs_txt_is_already_tracked(
    tmp_path: Path,
):
    run_git_command(tmp_path, "init")
    run_git_command(tmp_path, "config", "user.email", "tester@example.com")
    run_git_command(tmp_path, "config", "user.name", "Tester")

    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "docs.txt").write_text(
        "# Old Documentation Context\nSELF_REFERENCE_SHOULD_NOT_APPEAR\n",
        encoding="utf-8",
    )

    run_git_command(tmp_path, "add", "README.md", "docs.txt")
    run_git_command(tmp_path, "commit", "-m", "Initial commit")

    first_output_path = generate_docs_export(tmp_path)
    first_content = first_output_path.read_text(encoding="utf-8")
    second_output_path = generate_docs_export(tmp_path)
    second_content = second_output_path.read_text(encoding="utf-8")

    assert first_output_path == tmp_path / "docs.txt"
    assert second_output_path == tmp_path / "docs.txt"
    assert first_content == second_content
    assert "SELF_REFERENCE_SHOULD_NOT_APPEAR" not in second_content
    assert "### File: docs.txt" not in second_content
    assert "Skipped generated RepoContext export file: docs.txt" in second_content


def test_build_docs_export_context_ignores_untracked_documentation_files(
    tmp_path: Path,
):
    run_git_command(tmp_path, "init")
    run_git_command(tmp_path, "config", "user.email", "tester@example.com")
    run_git_command(tmp_path, "config", "user.name", "Tester")

    (tmp_path / "README.md").write_text("# Tracked\n", encoding="utf-8")
    (tmp_path / "TASKS.md").write_text("# Untracked\n", encoding="utf-8")

    run_git_command(tmp_path, "add", "README.md")
    run_git_command(tmp_path, "commit", "-m", "Initial commit")

    context = build_docs_export_context(tmp_path)

    assert [document.relative_path.as_posix() for document in context.documentation_files] == [
        "README.md",
    ]
    assert "TASKS.md" not in render_docs_export(context)


def test_create_docs_export_context_reports_binary_docs_as_warning(tmp_path: Path):
    binary_manual = make_file(
        tmp_path,
        "docs/manual.pdf",
        is_text=False,
        is_binary=True,
        content=None,
        line_count=None,
        estimated_tokens=None,
    )

    context = make_docs_context(tmp_path, [binary_manual])

    assert context.documentation_files == ()
    assert context.skipped_files == (binary_manual,)
    assert "Skipped binary documentation file: docs/manual.pdf" in context.warnings
    assert "No documentation files found." in context.warnings


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


def test_docs_export_masks_secret_values_and_reports_summary(monkeypatch):
    from repocontext.exporters import docs as docs_exporter

    clear_secret = "ghp_1234567890abcdefSECRET"

    def fake_render(*args, **kwargs):
        return (
            "# Documentation Export\n\n"
            "## README.md\n\n"
            f'GITHUB_TOKEN = "{clear_secret}"\n'
            "This line is safe documentation.\n"
        )

    monkeypatch.setattr(docs_exporter, "_render_docs_export_unmasked", fake_render)

    rendered = docs_exporter.render_docs_export(object())

    assert clear_secret not in rendered
    assert "***REDACTED***" in rendered
    assert "# Secret Detection" in rendered
    assert "Potential secrets were masked in documentation content." in rendered
    assert "Potential secrets masked: 1" in rendered
    assert "- TOKEN: 1" in rendered
    assert "This line is safe documentation." in rendered
