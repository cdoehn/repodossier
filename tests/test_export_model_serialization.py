from repodossier.export_model import (
    ExportConfigurationSummary,
    ExportSummary,
    ExportWarning,
    FileEntry,
    FileTreeEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
)
from repodossier.export_model_serialization import (
    repository_export_to_dict,
    to_plain_data,
)


def test_repository_export_to_dict_converts_model_to_plain_data():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(
            root_path="/repo",
            root_name="repo",
            git_branch="main",
            git_commit="abc123",
            git_dirty=False,
        ),
        configuration=ExportConfigurationSummary(
            config_active=True,
            config_path="repodossier.yml",
            include_paths=("src",),
            exclude_globs=("*.pyc",),
            limits={"max_file_bytes": 1000},
        ),
        summary=ExportSummary(
            total_tracked_files=2,
            scanned_files=2,
            exported_text_files=1,
            file_type_statistics={".py": 1, ".md": 1},
            language_statistics=LanguageStatistics(
                counts={"python": 1, "markdown": 1}
            ),
        ),
        tree=(
            FileTreeEntry(
                path="src",
                entry_type="directory",
                children=(
                    FileTreeEntry(
                        path="src/app.py",
                        entry_type="file",
                    ),
                ),
            ),
        ),
        files=(
            FileEntry(
                path="src/app.py",
                language="python",
                line_count=3,
                content="print('hello')",
            ),
        ),
        warnings=(
            ExportWarning(
                message="example warning",
                path="src/app.py",
                code="example",
            ),
        ),
    )

    data = repository_export_to_dict(export)

    assert data["mode"] == "full"
    assert data["repository"]["root_name"] == "repo"
    assert data["repository"]["git_branch"] == "main"
    assert data["configuration"]["include_paths"] == ["src"]
    assert data["configuration"]["exclude_globs"] == ["*.pyc"]
    assert data["summary"]["total_tracked_files"] == 2
    assert data["summary"]["language_statistics"]["counts"] == {
        "markdown": 1,
        "python": 1,
    }
    assert data["tree"][0]["children"][0]["path"] == "src/app.py"
    assert data["files"][0]["content"] == "print('hello')"
    assert data["warnings"][0]["code"] == "example"


def test_repository_export_to_dict_can_omit_file_content():
    export = RepositoryExport(
        mode="ai",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(
                path="config.env",
                language="text",
                content="TOKEN=secret",
                masked_content="TOKEN=***",
            ),
        ),
    )

    data = repository_export_to_dict(export, include_content=False)

    assert "content" not in data["files"][0]
    assert "masked_content" not in data["files"][0]
    assert data["files"][0]["path"] == "config.env"
    assert data["files"][0]["language"] == "text"


def test_to_plain_data_sorts_dictionary_keys_deterministically():
    data = to_plain_data({"z": 1, "a": 2, "m": {"b": 1, "a": 2}})

    assert list(data.keys()) == ["a", "m", "z"]
    assert list(data["m"].keys()) == ["a", "b"]


def test_to_plain_data_converts_tuples_to_lists():
    export = RepositoryExport(
        mode="docs",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(path="README.md", language="markdown"),
            FileEntry(path="docs/guide.md", language="markdown"),
        ),
    )

    data = repository_export_to_dict(export)

    assert isinstance(data["files"], list)
    assert [file["path"] for file in data["files"]] == [
        "README.md",
        "docs/guide.md",
    ]


def test_serialization_does_not_mutate_export_model():
    export = RepositoryExport(
        mode="changed",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(path="a.py", language="python", content="print(1)"),
        ),
    )

    data = repository_export_to_dict(export)
    data["files"][0]["path"] = "changed.py"

    assert export.files[0].path == "a.py"
