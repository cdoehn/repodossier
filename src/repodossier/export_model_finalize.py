"""Finalization helpers for RepoDossier's structured export model."""

from __future__ import annotations

from dataclasses import replace

from repodossier.export_model import FileEntry, RepositoryExport, RepositoryMetadata
from repodossier.export_model_summary import build_export_summary_from_export
from repodossier.export_model_tree import build_file_tree_from_export
from repodossier.export_model import assert_valid_repository_export


def finalize_repository_export(
    export: RepositoryExport,
    *,
    rebuild_summary: bool = True,
    rebuild_tree: bool = True,
    validate: bool = True,
) -> RepositoryExport:
    """Return an export with derived model sections filled consistently.

    This helper composes the pure model helpers introduced for Milestone 3.
    It does not scan files, call Git, render output or mutate the input model.

    Validation intentionally runs before tree building. That way invalid model
    paths produce ExportModelValidationError instead of lower-level path errors.
    """

    finalized = export

    if validate:
        assert_valid_repository_export(finalized)

    if rebuild_summary:
        finalized = replace(
            finalized,
            summary=build_export_summary_from_export(finalized),
        )

    if rebuild_tree:
        finalized = replace(
            finalized,
            tree=build_file_tree_from_export(finalized),
        )

    if validate:
        assert_valid_repository_export(finalized)

    return finalized

def repository_export_with_files(
    *,
    mode: str,
    repository: RepositoryMetadata,
    files: tuple[FileEntry, ...] = (),
    omitted_files: tuple[FileEntry, ...] = (),
    truncated_files: tuple[FileEntry, ...] = (),
    validate: bool = True,
) -> RepositoryExport:
    """Build a finalized RepositoryExport from already prepared file entries."""

    export = RepositoryExport(
        mode=mode,
        repository=repository,
        files=files,
        omitted_files=omitted_files,
        truncated_files=truncated_files,
    )

    return finalize_repository_export(export, validate=validate)


def replace_repository_export_files(
    export: RepositoryExport,
    *,
    files: tuple[FileEntry, ...] | None = None,
    omitted_files: tuple[FileEntry, ...] | None = None,
    truncated_files: tuple[FileEntry, ...] | None = None,
    validate: bool = True,
) -> RepositoryExport:
    """Return a finalized copy of export with replaced file groups."""

    updated = replace(
        export,
        files=export.files if files is None else files,
        omitted_files=(
            export.omitted_files
            if omitted_files is None
            else omitted_files
        ),
        truncated_files=(
            export.truncated_files
            if truncated_files is None
            else truncated_files
        ),
    )

    return finalize_repository_export(updated, validate=validate)


def refresh_repository_export_derived_sections(
    export: RepositoryExport,
    *,
    validate: bool = True,
) -> RepositoryExport:
    """Refresh summary and tree sections from the current file groups."""

    return finalize_repository_export(
        export,
        rebuild_summary=True,
        rebuild_tree=True,
        validate=validate,
    )
