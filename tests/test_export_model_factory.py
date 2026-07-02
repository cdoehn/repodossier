import pytest

from repodossier.export_model import (
    DependencyReport,
    ExportConfigurationSummary,
    ExportModelValidationError,
    ExportWarning,
    FileEntry,
)
from repodossier.export_model_factory import (
    make_minimal_repository_export,
    make_repository_export,
)


def test_make_repository_export_builds_finalized_export_from_parts():
    export = make_repository_export(
        mode=" FULL ",
        root_path="/repo",
        root_name=" repo ",
        git_branch=" main ",
        git_commit=" abc123 ",
        git_dirty=False,
        configuration=ExportConfigurationSummary(
            config_active=True,
            include_paths=("src",),
        ),
        files=(
            FileEntry(
                path="src/app.py",
                language="python",
                status="included",
                line_count=3,
                estimated_tokens=12,
            ),
        ),
        warnings=(
            ExportWarning(message="B warning", path="b.py", code="b"),
            ExportWarning(message="A warning", path="a.py", code="a"),
        ),
        dependencies=DependencyReport(
            items=(
                {"package": "pytest", "source": "pyproject.toml"},
            ),
        ),
    )

    assert export.mode == "full"
    assert export.repository.root_path == "/repo"
    assert export.repository.root_name == "repo"
    assert export.repository.git_branch == "main"
    assert export.repository.git_commit == "abc123"
    assert export.repository.git_dirty is False

    assert export.configuration.config_active is True
    assert export.configuration.include_paths == ("src",)

    assert export.summary.total_tracked_files == 1
    assert export.summary.exported_text_files == 1
    assert export.summary.total_lines == 3
    assert export.summary.estimated_tokens == 12
    assert export.summary.language_statistics.counts == {"python": 1}

    assert [entry.path for entry in export.tree] == ["src"]
    assert export.warnings == (
        ExportWarning(message="A warning", path="a.py", code="a"),
        ExportWarning(message="B warning", path="b.py", code="b"),
    )
    assert export.dependencies.items == (
        {"package": "pytest", "source": "pyproject.toml"},
    )


def test_make_repository_export_uses_default_empty_report_sections():
    export = make_repository_export(
        mode="ai",
        root_path="/repo",
        root_name="repo",
    )

    assert export.dependencies.items == ()
    assert export.database_schema.items == ()
    assert export.secret_detection.findings == ()
    assert export.secret_detection.masked_files == ()
    assert export.symbol_index.symbols == ()
    assert export.import_graph.edges == ()
    assert export.call_graph.edges == ()
    assert export.test_map.mappings == ()
    assert export.recent_commits.commits == ()


def test_make_repository_export_rejects_invalid_mode():
    with pytest.raises(ValueError, match="unknown export mode"):
        make_repository_export(
            mode="xml",
            root_path="/repo",
            root_name="repo",
        )


def test_make_repository_export_validates_final_model_by_default():
    with pytest.raises(ExportModelValidationError):
        make_repository_export(
            mode="full",
            root_path="/repo",
            root_name="repo",
            files=(
                FileEntry(path="", language="python"),
            ),
        )


def test_make_repository_export_can_skip_validation_for_incremental_migration():
    export = make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        files=(
            FileEntry(path="", language="python"),
        ),
        validate=False,
    )

    assert export.files[0].path == ""


def test_make_minimal_repository_export_builds_empty_finalized_model():
    export = make_minimal_repository_export(
        mode="docs",
        root_path="/home/christian/repo_dossier",
    )

    assert export.mode == "docs"
    assert export.repository.root_name == "repo_dossier"
    assert export.files == ()
    assert export.summary.total_tracked_files == 0
    assert export.tree == ()
