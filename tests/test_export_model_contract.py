import pytest

from repodossier.export_model import FileEntry, RepositoryExport, RepositoryMetadata
from repodossier.export_model_configuration import make_export_configuration_summary
from repodossier.export_model_contract import (
    REQUIRED_EXPORT_MODEL_API_SYMBOLS,
    REQUIRED_EXPORT_MODEL_SECTIONS,
    ExportModelContractError,
    assert_export_model_contract,
    export_model_contract_status,
    export_model_section_presence,
    missing_export_model_api_symbols,
    missing_export_model_sections,
)
from repodossier.export_model_factory import make_repository_export
from repodossier.export_model_reports import (
    make_call_graph_report,
    make_database_schema_report,
    make_dependency_report,
    make_import_graph_report,
    make_recent_commit_report,
    make_secret_detection_summary,
    make_symbol_index,
    make_test_map_report,
)
from repodossier.export_model_warnings import make_export_warning


def make_contract_export():
    return make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        configuration=make_export_configuration_summary(
            config_active=True,
            include_paths=("src",),
        ),
        files=(
            FileEntry(
                path="src/app.py",
                language="python",
                status="included",
                line_count=1,
                estimated_tokens=4,
                content="print(1)\n",
            ),
        ),
        warnings=(
            make_export_warning(
                "Example warning",
                path="src/app.py",
                code="example",
            ),
        ),
        dependencies=make_dependency_report(
            ({"package": "pytest", "source": "pyproject.toml"},)
        ),
        database_schema=make_database_schema_report(
            ({"table": "apps", "columns": ["id", "name"]},)
        ),
        secret_detection=make_secret_detection_summary(
            findings=({"path": "src/app.py", "kind": "none"},),
            masked_files=(),
        ),
        symbol_index=make_symbol_index(
            ({"path": "src/app.py", "kind": "function", "name": "main"},)
        ),
        import_graph=make_import_graph_report(
            ({"source": "src/app.py", "target": "json", "kind": "external"},)
        ),
        call_graph=make_call_graph_report(
            ({"source": "main", "target": "print", "kind": "external"},)
        ),
        test_map=make_test_map_report(
            ({"source": "src/app.py", "test_file": "tests/test_app.py"},)
        ),
        recent_commits=make_recent_commit_report(
            ({"short_hash": "abc1234", "message": "Example"},)
        ),
    )


def test_required_export_model_sections_are_stable():
    assert REQUIRED_EXPORT_MODEL_SECTIONS == (
        "mode",
        "repository",
        "configuration",
        "summary",
        "tree",
        "files",
        "omitted_files",
        "truncated_files",
        "warnings",
        "dependencies",
        "database_schema",
        "secret_detection",
        "symbol_index",
        "import_graph",
        "call_graph",
        "test_map",
        "recent_commits",
    )


def test_required_export_model_api_symbols_are_currently_available():
    assert REQUIRED_EXPORT_MODEL_API_SYMBOLS == tuple(
        sorted(REQUIRED_EXPORT_MODEL_API_SYMBOLS)
    )
    assert missing_export_model_api_symbols() == ()


def test_export_model_section_presence_reports_complete_model():
    export = make_contract_export()

    presence = export_model_section_presence(export)

    assert all(presence.values())
    assert missing_export_model_sections(export) == ()


def test_export_model_contract_status_accepts_complete_export():
    export = make_contract_export()

    status = export_model_contract_status(export)

    assert status.valid
    assert status.issues == ()
    assert status.missing_sections == ()
    assert status.missing_api_symbols == ()
    assert len(status.fingerprint) == 64

    assert_export_model_contract(export)


def test_export_model_contract_status_reports_validation_issues():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
    )

    status = export_model_contract_status(export)

    assert not status.valid
    assert "repository.root_path must not be empty" in status.issues
    assert status.missing_sections == ()


def test_assert_export_model_contract_raises_useful_error():
    export = RepositoryExport(
        mode="full",
        repository=RepositoryMetadata(root_path="", root_name="repo"),
    )

    with pytest.raises(ExportModelContractError) as exc_info:
        assert_export_model_contract(export)

    assert "Export model contract is not satisfied:" in str(exc_info.value)
    assert "- repository.root_path must not be empty" in str(exc_info.value)


def test_export_model_contract_fingerprint_can_include_or_omit_content():
    export = make_contract_export()

    metadata_only = export_model_contract_status(
        export,
        include_content_in_fingerprint=False,
    )
    with_content = export_model_contract_status(
        export,
        include_content_in_fingerprint=True,
    )

    assert metadata_only.valid
    assert with_content.valid
    assert metadata_only.fingerprint != with_content.fingerprint


def test_contract_helper_api_symbols_are_required_and_exported():
    import repodossier.export_model_api as api
    from repodossier.export_model_contract import (
        CONTRACT_HELPER_API_SYMBOLS,
        REQUIRED_EXPORT_MODEL_API_SYMBOLS,
        missing_export_model_api_symbols,
    )

    assert CONTRACT_HELPER_API_SYMBOLS == tuple(sorted(CONTRACT_HELPER_API_SYMBOLS))
    assert set(CONTRACT_HELPER_API_SYMBOLS) <= set(REQUIRED_EXPORT_MODEL_API_SYMBOLS)

    for symbol in CONTRACT_HELPER_API_SYMBOLS:
        assert symbol in api.__all__
        assert hasattr(api, symbol)

    assert missing_export_model_api_symbols() == ()
