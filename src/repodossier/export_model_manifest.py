"""Compact manifest helpers for RepositoryExport models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from repodossier.export_model import RepositoryExport
from repodossier.export_model_modes import repository_export_title
from repodossier.export_model_sections import (
    repository_export_populated_sections,
    repository_export_sections,
)
from repodossier.export_model_snapshot import repository_export_fingerprint


@dataclass(frozen=True)
class RepositoryExportManifest:
    """Compact, renderer-friendly metadata for a RepositoryExport."""

    mode: str
    title: str
    root_name: str
    root_path: str
    git_branch: str | None
    git_commit: str | None
    git_dirty: bool | None
    fingerprint: str
    sections: tuple[str, ...]
    populated_sections: tuple[str, ...]
    file_count: int
    omitted_file_count: int
    truncated_file_count: int
    warning_count: int
    total_lines: int
    estimated_tokens: int
    languages: tuple[tuple[str, int], ...]


def repository_export_manifest(
    export: RepositoryExport,
    *,
    include_content_in_fingerprint: bool = False,
) -> RepositoryExportManifest:
    """Build a compact manifest from a RepositoryExport."""

    return RepositoryExportManifest(
        mode=export.mode,
        title=repository_export_title(export),
        root_name=export.repository.root_name,
        root_path=export.repository.root_path,
        git_branch=export.repository.git_branch,
        git_commit=export.repository.git_commit,
        git_dirty=export.repository.git_dirty,
        fingerprint=repository_export_fingerprint(
            export,
            include_content=include_content_in_fingerprint,
        ),
        sections=repository_export_sections(export),
        populated_sections=repository_export_populated_sections(export),
        file_count=len(export.files),
        omitted_file_count=len(export.omitted_files),
        truncated_file_count=len(export.truncated_files),
        warning_count=len(export.warnings),
        total_lines=export.summary.total_lines,
        estimated_tokens=export.summary.estimated_tokens,
        languages=tuple(
            sorted(export.summary.language_statistics.counts.items())
        ),
    )


def repository_export_manifest_to_dict(
    manifest: RepositoryExportManifest,
) -> dict[str, Any]:
    """Convert a RepositoryExportManifest to plain JSON-ready data."""

    data = asdict(manifest)
    data["sections"] = list(manifest.sections)
    data["populated_sections"] = list(manifest.populated_sections)
    data["languages"] = {
        language: count
        for language, count in manifest.languages
    }
    return data


def repository_export_manifest_lines(
    export: RepositoryExport,
    *,
    include_content_in_fingerprint: bool = False,
) -> tuple[str, ...]:
    """Return a stable, human-readable manifest summary."""

    manifest = repository_export_manifest(
        export,
        include_content_in_fingerprint=include_content_in_fingerprint,
    )

    lines = [
        f"mode: {manifest.mode}",
        f"title: {manifest.title}",
        f"root_name: {manifest.root_name}",
        f"root_path: {manifest.root_path}",
        f"fingerprint: {manifest.fingerprint}",
        f"files: {manifest.file_count}",
        f"omitted_files: {manifest.omitted_file_count}",
        f"truncated_files: {manifest.truncated_file_count}",
        f"warnings: {manifest.warning_count}",
        f"total_lines: {manifest.total_lines}",
        f"estimated_tokens: {manifest.estimated_tokens}",
    ]

    if manifest.git_branch:
        lines.append(f"git_branch: {manifest.git_branch}")

    if manifest.git_commit:
        lines.append(f"git_commit: {manifest.git_commit}")

    if manifest.git_dirty is not None:
        lines.append(f"git_dirty: {manifest.git_dirty}")

    if manifest.languages:
        language_text = ", ".join(
            f"{language}={count}"
            for language, count in manifest.languages
        )
        lines.append(f"languages: {language_text}")

    if manifest.populated_sections:
        lines.append(
            "populated_sections: "
            + ", ".join(manifest.populated_sections)
        )

    return tuple(lines)
