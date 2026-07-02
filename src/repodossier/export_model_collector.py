"""Collection helpers for assembling RepositoryExport file groups."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

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
from repodossier.export_model_adapters import (
    file_entries_from_mappings,
    file_entries_from_objects,
)
from repodossier.export_model_factory import make_repository_export


@dataclass(frozen=True)
class FileEntryPartitions:
    """Separated file groups used by RepositoryExport."""

    files: tuple[FileEntry, ...] = ()
    omitted_files: tuple[FileEntry, ...] = ()
    truncated_files: tuple[FileEntry, ...] = ()

    def all_entries(self) -> tuple[FileEntry, ...]:
        """Return all known entries in deterministic path order."""

        return tuple(
            sorted(
                self.files + self.omitted_files + self.truncated_files,
                key=lambda entry: entry.path,
            )
        )


def partition_file_entries(
    entries: Iterable[FileEntry],
) -> FileEntryPartitions:
    """Partition FileEntry objects into export model file groups."""

    files: list[FileEntry] = []
    omitted_files: list[FileEntry] = []
    truncated_files: list[FileEntry] = []

    for entry in entries:
        if entry.status == "truncated":
            truncated_files.append(entry)
        elif entry.status in {"skipped", "error"} or entry.text_status == "binary":
            omitted_files.append(entry)
        else:
            files.append(entry)

    return FileEntryPartitions(
        files=tuple(sorted(files, key=lambda entry: entry.path)),
        omitted_files=tuple(
            sorted(omitted_files, key=lambda entry: entry.path)
        ),
        truncated_files=tuple(
            sorted(truncated_files, key=lambda entry: entry.path)
        ),
    )


def repository_export_from_file_entries(
    *,
    mode: str,
    root_path: str,
    entries: Iterable[FileEntry],
    root_name: str | None = None,
    git_branch: str | None = None,
    git_commit: str | None = None,
    git_dirty: bool | None = None,
    configuration: ExportConfigurationSummary | None = None,
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
    """Build a finalized RepositoryExport from mixed FileEntry objects."""

    partitions = partition_file_entries(entries)

    return make_repository_export(
        mode=mode,
        root_path=root_path,
        root_name=root_name,
        git_branch=git_branch,
        git_commit=git_commit,
        git_dirty=git_dirty,
        configuration=configuration,
        files=partitions.files,
        omitted_files=partitions.omitted_files,
        truncated_files=partitions.truncated_files,
        warnings=warnings,
        dependencies=dependencies,
        database_schema=database_schema,
        secret_detection=secret_detection,
        symbol_index=symbol_index,
        import_graph=import_graph,
        call_graph=call_graph,
        test_map=test_map,
        recent_commits=recent_commits,
        validate=validate,
    )


def repository_export_from_file_mappings(
    *,
    mode: str,
    root_path: str,
    mappings: Iterable[Mapping[str, Any]],
    root_name: str | None = None,
    configuration: ExportConfigurationSummary | None = None,
    warnings: tuple[ExportWarning, ...] = (),
    validate: bool = True,
) -> RepositoryExport:
    """Build a finalized RepositoryExport from dict-like file payloads."""

    return repository_export_from_file_entries(
        mode=mode,
        root_path=root_path,
        root_name=root_name,
        entries=file_entries_from_mappings(mappings),
        configuration=configuration,
        warnings=warnings,
        validate=validate,
    )


def repository_export_from_file_objects(
    *,
    mode: str,
    root_path: str,
    objects: Iterable[object],
    root_name: str | None = None,
    configuration: ExportConfigurationSummary | None = None,
    warnings: tuple[ExportWarning, ...] = (),
    validate: bool = True,
) -> RepositoryExport:
    """Build a finalized RepositoryExport from scanner-like objects."""

    return repository_export_from_file_entries(
        mode=mode,
        root_path=root_path,
        root_name=root_name,
        entries=file_entries_from_objects(objects),
        configuration=configuration,
        warnings=warnings,
        validate=validate,
    )
