"""High-level factory helpers for RepoDossier's structured export model."""

from __future__ import annotations

from repodossier.export_model import (
    CallGraphReport,
    DatabaseSchemaReport,
    DependencyReport,
    ExportConfigurationSummary,
    ExportWarning,
    FileEntry,
    ImportGraphReport,
    RecentCommitReport,
    RepositoryExport,
    SecretDetectionSummary,
    SymbolIndex,
    TestMapReport,
)
from repodossier.export_model_finalize import finalize_repository_export
from repodossier.export_model_modes import normalize_export_mode
from repodossier.export_model_repository import make_repository_metadata
from repodossier.export_model_warnings import normalize_export_warnings


def make_repository_export(
    *,
    mode: str,
    root_path: str,
    root_name: str | None = None,
    git_branch: str | None = None,
    git_commit: str | None = None,
    git_dirty: bool | None = None,
    configuration: ExportConfigurationSummary | None = None,
    files: tuple[FileEntry, ...] = (),
    omitted_files: tuple[FileEntry, ...] = (),
    truncated_files: tuple[FileEntry, ...] = (),
    warnings: tuple[ExportWarning, ...] = (),
    dependencies: DependencyReport | None = None,
    database_schema: DatabaseSchemaReport | None = None,
    secret_detection: SecretDetectionSummary | None = None,
    symbol_index: SymbolIndex | None = None,
    import_graph: ImportGraphReport | None = None,
    call_graph: CallGraphReport | None = None,
    test_map: TestMapReport | None = None,
    recent_commits: RecentCommitReport | None = None,
    validate: bool = True,
) -> RepositoryExport:
    """Build a finalized RepositoryExport from already prepared model parts.

    This function is intentionally a composition layer. It does not scan the
    filesystem, call Git, run analyzers or render output.
    """

    export = RepositoryExport(
        mode=normalize_export_mode(mode),
        repository=make_repository_metadata(
            root_path=root_path,
            root_name=root_name,
            git_branch=git_branch,
            git_commit=git_commit,
            git_dirty=git_dirty,
        ),
        configuration=configuration or ExportConfigurationSummary(),
        files=files,
        omitted_files=omitted_files,
        truncated_files=truncated_files,
        warnings=normalize_export_warnings(warnings),
        dependencies=dependencies or DependencyReport(),
        database_schema=database_schema or DatabaseSchemaReport(),
        secret_detection=secret_detection or SecretDetectionSummary(),
        symbol_index=symbol_index or SymbolIndex(),
        import_graph=import_graph or ImportGraphReport(),
        call_graph=call_graph or CallGraphReport(),
        test_map=test_map or TestMapReport(),
        recent_commits=recent_commits or RecentCommitReport(),
    )

    return finalize_repository_export(
        export,
        rebuild_tree=validate,
        validate=validate,
    )


def make_minimal_repository_export(
    *,
    mode: str,
    root_path: str,
    root_name: str | None = None,
    validate: bool = True,
) -> RepositoryExport:
    """Build a finalized empty RepositoryExport for tests and migration."""

    return make_repository_export(
        mode=mode,
        root_path=root_path,
        root_name=root_name,
        validate=validate,
    )
