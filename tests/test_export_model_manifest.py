from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_manifest import (
    RepositoryExportManifest,
    repository_export_manifest,
    repository_export_manifest_lines,
    repository_export_manifest_to_dict,
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
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
            },
            {
                "path": "large.log",
                "language": "text",
                "content": "partial",
                "truncated": True,
            },
        ),
        warnings=(
            make_export_warning(
                "Large file truncated",
                path="large.log",
                code="truncated",
            ),
        ),
    )


def test_repository_export_manifest_summarizes_export():
    export = make_export()

    manifest = repository_export_manifest(export)

    assert isinstance(manifest, RepositoryExportManifest)
    assert manifest.mode == "full"
    assert manifest.title == "Full Repository Export"
    assert manifest.root_name == "repo"
    assert manifest.root_path == "/repo"
    assert len(manifest.fingerprint) == 64
    assert manifest.file_count == 2
    assert manifest.omitted_file_count == 1
    assert manifest.truncated_file_count == 1
    assert manifest.warning_count == 1
    assert manifest.total_lines == 3
    assert manifest.estimated_tokens > 0
    assert manifest.languages == (
        ("binary", 1),
        ("markdown", 1),
        ("python", 1),
        ("text", 1),
    )
    assert "repository_metadata" in manifest.sections
    assert "summary" in manifest.sections
    assert "repository_metadata" in manifest.populated_sections
    assert "summary" in manifest.populated_sections


def test_repository_export_manifest_fingerprint_can_include_content():
    export = make_export()

    metadata_only = repository_export_manifest(
        export,
        include_content_in_fingerprint=False,
    )
    with_content = repository_export_manifest(
        export,
        include_content_in_fingerprint=True,
    )

    assert metadata_only.fingerprint != with_content.fingerprint


def test_repository_export_manifest_to_dict_is_json_ready():
    manifest = repository_export_manifest(make_export())

    data = repository_export_manifest_to_dict(manifest)

    assert data["mode"] == "full"
    assert data["root_name"] == "repo"
    assert data["file_count"] == 2
    assert data["omitted_file_count"] == 1
    assert data["truncated_file_count"] == 1
    assert data["warning_count"] == 1
    assert isinstance(data["sections"], list)
    assert isinstance(data["populated_sections"], list)
    assert data["languages"] == {
        "binary": 1,
        "markdown": 1,
        "python": 1,
        "text": 1,
    }


def test_repository_export_manifest_lines_are_stable_and_readable():
    lines = repository_export_manifest_lines(make_export())

    assert lines[0] == "mode: full"
    assert lines[1] == "title: Full Repository Export"
    assert "root_name: repo" in lines
    assert "files: 2" in lines
    assert "omitted_files: 1" in lines
    assert "truncated_files: 1" in lines
    assert "warnings: 1" in lines
    assert any(line.startswith("fingerprint: ") for line in lines)
    assert "languages: binary=1, markdown=1, python=1, text=1" in lines
    assert any(line.startswith("populated_sections: ") for line in lines)
