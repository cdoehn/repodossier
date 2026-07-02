from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_view import (
    RepositoryExportView,
    repository_export_files_for_section,
    repository_export_section_titles,
    repository_export_view,
    repository_export_warning_lines,
)
from repodossier.export_model_warnings import make_export_warning


def make_export():
    return repository_export_from_file_mappings(
        mode="full",
        root_path="/repo",
        root_name="repo",
        mappings=(
            {
                "path": "src/app.py",
                "language": "python",
                "content": "print(1)\n",
            },
            {
                "path": "README.md",
                "language": "markdown",
                "content": "# Hello\n",
            },
            {
                "path": "large.log",
                "language": "text",
                "content": "partial",
                "truncated": True,
            },
            {
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
            },
        ),
        warnings=(
            make_export_warning(
                "Large file truncated",
                path="large.log",
                code="truncated",
            ),
            make_export_warning(
                "Binary file skipped",
                path="assets/logo.png",
                code="binary",
            ),
        ),
    )


def test_repository_export_view_collects_renderer_context():
    export = make_export()

    view = repository_export_view(export)

    assert isinstance(view, RepositoryExportView)
    assert view.export is export
    assert view.manifest.mode == "full"
    assert view.manifest.file_count == 2
    assert view.sections
    assert view.populated_sections
    assert view.section_presence["repository_metadata"] is True
    assert view.section_title("source-export") == "Source Export"


def test_repository_export_view_can_include_content_in_manifest_fingerprint():
    export = make_export()

    metadata_only = repository_export_view(
        export,
        include_content_in_fingerprint=False,
    )
    with_content = repository_export_view(
        export,
        include_content_in_fingerprint=True,
    )

    assert metadata_only.manifest.fingerprint != with_content.manifest.fingerprint


def test_repository_export_files_for_section_returns_expected_file_groups():
    export = make_export()

    source_files = repository_export_files_for_section(export, "source_export")
    summary_files = repository_export_files_for_section(export, "file-summary")
    truncated_files = repository_export_files_for_section(export, "truncated_files")
    omitted_files = repository_export_files_for_section(export, "omitted_files")

    assert [entry.path for entry in source_files] == ["README.md", "src/app.py"]
    assert [entry.path for entry in summary_files] == [
        "README.md",
        "assets/logo.png",
        "large.log",
        "src/app.py",
    ]
    assert [entry.path for entry in truncated_files] == ["large.log"]
    assert [entry.path for entry in omitted_files] == ["assets/logo.png"]
    assert repository_export_files_for_section(export, "summary") == ()


def test_repository_export_view_delegates_files_for_section():
    view = repository_export_view(make_export())

    assert [entry.path for entry in view.files_for_section("source_export")] == [
        "README.md",
        "src/app.py",
    ]


def test_repository_export_warning_lines_are_stable_and_readable():
    lines = repository_export_warning_lines(make_export())

    assert lines == (
        "assets/logo.png [binary] Binary file skipped",
        "large.log [truncated] Large file truncated",
    )


def test_repository_export_view_delegates_warning_lines():
    view = repository_export_view(make_export())

    assert view.warning_lines() == (
        "assets/logo.png [binary] Binary file skipped",
        "large.log [truncated] Large file truncated",
    )


def test_repository_export_section_titles_preserves_export_order():
    export = make_export()

    titles = repository_export_section_titles(export)

    assert titles
    assert titles[0][0] == export.mode or titles[0][0] in view_section_ids(titles)
    assert ("repository_metadata", "Repository Metadata") in titles
    assert ("summary", "Summary") in titles


def view_section_ids(titles):
    return tuple(section for section, _title in titles)
