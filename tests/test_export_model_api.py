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


def test_export_model_api_exposes_collector_helpers():
    partitions = api.partition_file_entries(
        (
            api.FileEntry(path="src/app.py", language="python"),
            api.FileEntry(
                path="src/large.py",
                language="python",
                status="truncated",
            ),
            api.FileEntry(
                path="assets/logo.png",
                language="binary",
                text_status="binary",
                status="skipped",
            ),
        )
    )

    assert isinstance(partitions, api.FileEntryPartitions)
    assert [entry.path for entry in partitions.files] == ["src/app.py"]
    assert [entry.path for entry in partitions.truncated_files] == ["src/large.py"]
    assert [entry.path for entry in partitions.omitted_files] == ["assets/logo.png"]

    export = api.repository_export_from_file_mappings(
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
                "truncated": True,
                "content": "# Partial",
            },
        ),
    )

    assert [entry.path for entry in export.files] == ["src/app.py"]
    assert [entry.path for entry in export.truncated_files] == ["README.md"]
    assert export.summary.total_tracked_files == 2


def test_export_model_api_exposes_compare_helpers():
    before = api.repository_export_from_file_mappings(
        mode="full",
        root_path="/repo",
        root_name="repo",
        mappings=(
            {
                "path": "src/app.py",
                "language": "python",
                "content": "print(1)\n",
            },
        ),
    )
    after = api.repository_export_from_file_mappings(
        mode="full",
        root_path="/repo",
        root_name="repo",
        mappings=(
            {
                "path": "src/app.py",
                "language": "python",
                "content": "print(2)\n",
            },
            {
                "path": "README.md",
                "language": "markdown",
                "content": "# Hello\n",
            },
        ),
    )

    comparison = api.compare_repository_exports(before, after)

    assert api.FILE_COMPARE_FIELDS
    assert isinstance(comparison, api.RepositoryExportComparison)
    assert not comparison.same
    assert comparison.added_paths == ("README.md",)
    assert comparison.removed_paths == ()
    assert comparison.changed_files == (
        api.FileEntryChange(path="src/app.py", changed_fields=("content",)),
    )
    assert comparison.changed_paths() == ("README.md", "src/app.py")

    assert not api.repository_exports_have_same_paths(before, after)
    assert api.repository_export_path_delta(before, after) == (
        ("README.md",),
        (),
    )

    assert api.compare_file_entries(
        before.files[0],
        after.files[1],
        include_content=False,
    ) == ()
    assert api.compare_file_entries(
        before.files[0],
        after.files[1],
    ) == ("content",)


def test_export_model_api_exposes_manifest_helpers():
    export = api.repository_export_from_file_mappings(
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
        ),
    )

    manifest = api.repository_export_manifest(export)
    data = api.repository_export_manifest_to_dict(manifest)
    lines = api.repository_export_manifest_lines(export)

    assert isinstance(manifest, api.RepositoryExportManifest)
    assert manifest.mode == "full"
    assert manifest.title == "Full Repository Export"
    assert manifest.file_count == 2
    assert manifest.omitted_file_count == 0
    assert manifest.truncated_file_count == 0
    assert len(manifest.fingerprint) == 64
    assert data["mode"] == "full"
    assert data["file_count"] == 2
    assert data["languages"] == {
        "markdown": 1,
        "python": 1,
    }
    assert lines[0] == "mode: full"
    assert "files: 2" in lines
    assert "languages: markdown=1, python=1" in lines


def test_export_model_api_exposes_view_helpers():
    export = api.repository_export_from_file_mappings(
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
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
            },
        ),
        warnings=(
            api.make_export_warning(
                "Binary file skipped",
                path="assets/logo.png",
                code="binary",
            ),
        ),
    )

    view = api.repository_export_view(export)

    assert isinstance(view, api.RepositoryExportView)
    assert view.export is export
    assert view.manifest.mode == "full"
    assert view.section_title("repository-metadata") == "Repository Metadata"

    assert [entry.path for entry in view.files_for_section("source_export")] == [
        "src/app.py",
    ]
    assert [entry.path for entry in api.repository_export_files_for_section(
        export,
        "omitted_files",
    )] == ["assets/logo.png"]

    assert api.repository_export_warning_lines(export) == (
        "assets/logo.png [binary] Binary file skipped",
    )
    assert view.warning_lines() == (
        "assets/logo.png [binary] Binary file skipped",
    )

    titles = api.repository_export_section_titles(export)
    assert ("repository_metadata", "Repository Metadata") in titles
    assert ("summary", "Summary") in titles


def test_export_model_api_exposes_file_inventory_helpers():
    export = api.repository_export_from_file_mappings(
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
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
                "size": 123,
                "skip_reason": "binary file",
            },
            {
                "path": "large.log",
                "language": "text",
                "content": "partial",
                "truncated": True,
                "skip_reason": "too large",
            },
        ),
    )

    inventory = api.repository_export_file_inventory(export)
    grouped = api.repository_export_file_inventory_by_group(export)
    data = api.repository_export_file_inventory_to_dicts(export)
    lines = api.repository_export_file_inventory_lines(export)

    assert isinstance(inventory[0], api.FileInventoryEntry)
    assert [entry.path for entry in inventory] == [
        "assets/logo.png",
        "large.log",
        "src/app.py",
    ]
    assert [entry.path for entry in grouped["files"]] == ["src/app.py"]
    assert [entry.path for entry in grouped["omitted_files"]] == [
        "assets/logo.png",
    ]
    assert [entry.path for entry in grouped["truncated_files"]] == [
        "large.log",
    ]

    assert data[0]["path"] == "assets/logo.png"
    assert data[0]["group"] == "omitted_files"
    assert data[0]["reason"] == "binary file"

    assert lines[0].startswith(
        "assets/logo.png | group=omitted_files | language=binary"
    )
    assert "reason=too large" in lines[1]
    assert lines[2].startswith("src/app.py | group=files | language=python")


def test_export_model_api_exposes_deserialization_helpers():
    original = api.repository_export_from_file_mappings(
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
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
                "size": 123,
            },
        ),
        warnings=(
            api.make_export_warning(
                "Binary file skipped",
                path="assets/logo.png",
                code="binary",
            ),
        ),
    )

    data = api.repository_export_to_dict(original)
    json_text = api.repository_export_to_json(original)

    from_dict = api.repository_export_from_dict(data)
    from_json = api.repository_export_from_json(json_text)

    assert from_dict == original
    assert from_json == original
    assert api.repository_export_fingerprint(from_dict) == api.repository_export_fingerprint(original)


def test_export_model_api_exposes_roundtrip_helpers():
    export = api.repository_export_from_file_mappings(
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
                "path": "large.log",
                "language": "text",
                "content": "partial",
                "truncated": True,
            },
        ),
    )

    restored = api.repository_export_round_trip(export)
    canonical = api.repository_export_canonical_dict(export)
    status = api.repository_export_round_trip_status(export)

    assert restored == export
    assert canonical == api.repository_export_to_dict(export)
    assert isinstance(status, api.RepositoryExportRoundTripStatus)
    assert status.valid
    assert status.issues == ()
    assert status.same_fingerprint is True
    assert len(status.before_fingerprint) == 64

    api.assert_repository_export_round_trips(export)

    invalid = api.RepositoryExport(
        mode="full",
        repository=api.RepositoryMetadata(root_path="", root_name="repo"),
    )

    invalid_status = api.repository_export_round_trip_status(invalid)

    assert not invalid_status.valid
    assert invalid_status.issues
    assert invalid_status.issues[0].startswith("deserialization failed:")

    try:
        api.assert_repository_export_round_trips(invalid)
    except api.RepositoryExportRoundTripError as exc:
        assert "RepositoryExport does not round-trip cleanly:" in str(exc)
    else:
        raise AssertionError("expected RepositoryExportRoundTripError")


def test_export_model_api_exposes_audit_helpers():
    export = api.repository_export_from_file_mappings(
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
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
                "size": 123,
            },
        ),
    )

    result = api.audit_repository_export(export)
    lines = api.repository_export_audit_lines(export)

    assert isinstance(result, api.RepositoryExportAuditResult)
    assert result.valid
    assert result.issues == ()
    assert result.summary_matches is True
    assert result.tree_matches is True
    assert result.inventory_matches is True
    assert result.round_trip_matches is True
    assert lines == (
        "valid=True",
        "summary_matches=True",
        "tree_matches=True",
        "inventory_matches=True",
        "round_trip_matches=True",
    )

    api.assert_repository_export_audit(export)

    stale = api.RepositoryExport(
        mode="full",
        repository=api.RepositoryMetadata(root_path="", root_name="repo"),
    )

    stale_result = api.audit_repository_export(stale)

    assert not stale_result.valid
    assert stale_result.issues

    try:
        api.assert_repository_export_audit(stale)
    except api.RepositoryExportAuditError as exc:
        assert "RepositoryExport audit failed:" in str(exc)
    else:
        raise AssertionError("expected RepositoryExportAuditError")
