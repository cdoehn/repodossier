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


def test_export_model_api_exposes_adapter_helpers():
    entry = api.file_entry_from_mapping(
        {
            "relative_path": "./src\\app.py",
            "lang": "python",
            "text": "print(1)",
        }
    )

    entries = api.file_entries_from_mappings(
        (
            {"path": "b.py", "language": "python"},
            {"path": "a.py", "language": "python"},
        )
    )

    assert entry.path == "src/app.py"
    assert entry.language == "python"
    assert entry.content == "print(1)"
    assert [item.path for item in entries] == ["a.py", "b.py"]


def test_export_model_api_exposes_snapshot_helpers():
    export = api.make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        files=(
            api.make_file_entry_from_content(
                path="src/app.py",
                language="python",
                content="print(1)\n",
            ),
        ),
    )

    json_text = api.repository_export_to_json(export)
    fingerprint = api.repository_export_fingerprint(export)
    header = api.repository_export_snapshot_header(export)
    lines = api.repository_export_snapshot_lines(export)

    assert '"mode": "full"' in json_text
    assert len(fingerprint) == 64
    assert header["fingerprint"] == fingerprint
    assert header["file_count"] == 1
    assert lines[0] == "{"
    assert lines[-1] == "}"


def test_export_model_api_exposes_contract_helpers():
    export = api.make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        files=(
            api.make_file_entry_from_content(
                path="src/app.py",
                language="python",
                content="print(1)\n",
            ),
        ),
    )

    status = api.export_model_contract_status(export)
    presence = api.export_model_section_presence(export)

    assert api.REQUIRED_EXPORT_MODEL_SECTIONS
    assert api.REQUIRED_EXPORT_MODEL_API_SYMBOLS
    assert isinstance(status, api.ExportModelContractStatus)
    assert status.valid
    assert status.issues == ()
    assert presence["mode"] is True
    assert presence["repository"] is True
    assert api.missing_export_model_sections(export) == ()
    assert api.missing_export_model_api_symbols() == ()

    api.assert_export_model_contract(export)


def test_export_model_api_exposes_section_helpers():
    export = api.make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        files=(
            api.make_file_entry_from_content(
                path="src/app.py",
                language="python",
                content="print(1)\n",
            ),
        ),
    )

    assert api.normalize_export_section("repository-tree") == "repository_tree"
    assert api.export_section_title("source-export") == "Source Export"
    assert "summary" in api.known_export_sections()
    assert api.SECTION_TITLES["repository_tree"] == "Repository Tree"

    assert api.repository_export_sections(export) == api.export_mode_sections("full")

    presence = api.repository_export_section_presence(export)
    populated = api.repository_export_populated_sections(export)

    assert presence["repository_metadata"] is True
    assert presence["summary"] is True
    assert "repository_metadata" in populated
    assert "summary" in populated
    assert api.repository_export_has_section(export, "repository-metadata")
