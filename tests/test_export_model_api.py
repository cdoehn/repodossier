import repodossier.export_model_api as api


def test_export_model_api_exposes_core_model_types():
    assert api.RepositoryExport.__name__ == "RepositoryExport"
    assert api.RepositoryMetadata.__name__ == "RepositoryMetadata"
    assert api.FileEntry.__name__ == "FileEntry"
    assert api.FileTreeEntry.__name__ == "FileTreeEntry"
    assert api.ExportWarning.__name__ == "ExportWarning"


def test_export_model_api_exposes_factory_and_serialization_helpers():
    export = api.make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        files=(
            api.make_file_entry_from_content(
                path="src/app.py",
                language="python",
                content="print('hello')\n",
            ),
        ),
    )

    data = api.repository_export_to_dict(export)

    assert export.mode == "full"
    assert export.summary.total_tracked_files == 1
    assert export.summary.language_statistics.counts == {"python": 1}
    assert api.tree_paths(export.tree) == ("src", "src/app.py")
    assert data["files"][0]["path"] == "src/app.py"


def test_export_model_api_exposes_configuration_warning_and_report_helpers():
    configuration = api.make_export_configuration_summary(
        config_active=True,
        include_paths=["src"],
        exclude_globs=["*.pyc"],
    )
    warning = api.make_export_warning(
        "File was truncated",
        path="src/app.py",
        code="limit",
    )
    dependencies = api.make_dependency_report(
        ({"package": "pytest", "source": "pyproject.toml"},)
    )

    export = api.make_repository_export(
        mode="ai",
        root_path="/repo",
        root_name="repo",
        configuration=configuration,
        warnings=(warning,),
        dependencies=dependencies,
    )

    assert export.configuration.config_active is True
    assert export.configuration.include_paths == ("src",)
    assert export.configuration.exclude_globs == ("*.pyc",)
    assert api.warning_counts_by_code(export.warnings) == {"limit": 1}
    assert export.dependencies.items == (
        {"package": "pytest", "source": "pyproject.toml"},
    )


def test_export_model_api_exposes_mode_and_path_helpers():
    assert api.normalize_export_mode(" FULL ") == "full"
    assert api.export_mode_title("ai") == "AI Repository Export"
    assert api.export_mode_includes_source_content("changed")
    assert api.normalize_export_path("./src\\app.py") == "src/app.py"
    assert api.sort_export_paths(["src/app.py", "README.md"]) == (
        "README.md",
        "src/app.py",
    )


def test_export_model_api_all_is_sorted_and_matches_public_names():
    public_names = api.__all__

    assert public_names == tuple(sorted(public_names))
    assert len(public_names) == len(set(public_names))

    for name in public_names:
        assert hasattr(api, name), name
