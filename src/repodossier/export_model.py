"""Structured internal export model for RepoDossier.

The export model is the renderer-independent representation of a
repository export. Scanners, Git helpers and analyzers should build this
model. Renderers should only consume it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ExportMode = Literal["full", "ai", "docs", "changed"]
FileStatus = Literal["included", "skipped", "truncated", "error"]
TextStatus = Literal["text", "binary"]


@dataclass(frozen=True)
class RepositoryMetadata:
    """Repository-level metadata captured for an export."""

    root_path: str
    root_name: str
    git_branch: str | None = None
    git_commit: str | None = None
    git_dirty: bool | None = None


@dataclass(frozen=True)
class ExportConfigurationSummary:
    """User-visible summary of the effective export configuration."""

    config_active: bool = False
    config_path: str | None = None
    include_paths: tuple[str, ...] = ()
    include_globs: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    exclude_globs: tuple[str, ...] = ()
    limits: dict[str, Any] = field(default_factory=dict)
    split_settings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LanguageStatistics:
    """Aggregated file counts by language label."""

    counts: dict[str, int] = field(default_factory=dict)

    def increment(self, language: str) -> "LanguageStatistics":
        next_counts = dict(self.counts)
        next_counts[language] = next_counts.get(language, 0) + 1
        return LanguageStatistics(counts=next_counts)


@dataclass(frozen=True)
class ExportSummary:
    """Aggregated export statistics."""

    total_tracked_files: int = 0
    scanned_files: int = 0
    exported_text_files: int = 0
    skipped_binary_files: int = 0
    errored_files: int = 0
    total_lines: int = 0
    estimated_tokens: int = 0
    file_type_statistics: dict[str, int] = field(default_factory=dict)
    language_statistics: LanguageStatistics = field(default_factory=LanguageStatistics)


@dataclass(frozen=True)
class FileTreeEntry:
    """A deterministic tree entry used by renderers."""

    path: str
    entry_type: Literal["file", "directory"]
    children: tuple["FileTreeEntry", ...] = ()


@dataclass(frozen=True)
class FileEntry:
    """A single file represented in an export."""

    path: str
    language: str
    size_bytes: int = 0
    line_count: int = 0
    estimated_tokens: int = 0
    text_status: TextStatus = "text"
    status: FileStatus = "included"
    content: str | None = None
    masked_content: str | None = None
    reason: str | None = None

    @property
    def rendered_content(self) -> str | None:
        """Return masked content when present, otherwise raw content."""

        return self.masked_content if self.masked_content is not None else self.content


@dataclass(frozen=True)
class ExportWarning:
    """Warning produced while building an export model."""

    message: str
    path: str | None = None
    code: str | None = None


@dataclass(frozen=True)
class DependencyReport:
    """Renderer-independent dependency report placeholder."""

    items: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class DatabaseSchemaReport:
    """Renderer-independent database schema report placeholder."""

    items: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class SecretDetectionSummary:
    """Renderer-independent secret detection summary."""

    findings: tuple[dict[str, Any], ...] = ()
    masked_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class SymbolIndex:
    """Renderer-independent symbol index."""

    symbols: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ImportGraphReport:
    """Renderer-independent import graph."""

    edges: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class CallGraphReport:
    """Renderer-independent call graph."""

    edges: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class TestMapReport:
    """Renderer-independent test map placeholder for later milestones."""

    mappings: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class RecentCommitReport:
    """Renderer-independent recent commit placeholder for later milestones."""

    commits: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class RepositoryExport:
    """Complete structured export consumed by Markdown/XML renderers."""

    mode: ExportMode
    repository: RepositoryMetadata
    configuration: ExportConfigurationSummary = field(
        default_factory=ExportConfigurationSummary
    )
    summary: ExportSummary = field(default_factory=ExportSummary)
    tree: tuple[FileTreeEntry, ...] = ()
    files: tuple[FileEntry, ...] = ()
    omitted_files: tuple[FileEntry, ...] = ()
    truncated_files: tuple[FileEntry, ...] = ()
    warnings: tuple[ExportWarning, ...] = ()
    dependencies: DependencyReport = field(default_factory=DependencyReport)
    database_schema: DatabaseSchemaReport = field(default_factory=DatabaseSchemaReport)
    secret_detection: SecretDetectionSummary = field(
        default_factory=SecretDetectionSummary
    )
    symbol_index: SymbolIndex = field(default_factory=SymbolIndex)
    import_graph: ImportGraphReport = field(default_factory=ImportGraphReport)
    call_graph: CallGraphReport = field(default_factory=CallGraphReport)
    test_map: TestMapReport = field(default_factory=TestMapReport)
    recent_commits: RecentCommitReport = field(default_factory=RecentCommitReport)

    def included_files(self) -> tuple[FileEntry, ...]:
        """Return files whose contents are included in the export."""

        return tuple(file for file in self.files if file.status == "included")

    def all_paths(self) -> tuple[str, ...]:
        """Return all known file paths in deterministic order."""

        paths = {
            file.path
            for group in (self.files, self.omitted_files, self.truncated_files)
            for file in group
        }
        return tuple(sorted(paths))


def empty_repository_export(
    *,
    mode: ExportMode,
    root_path: str,
    root_name: str,
) -> RepositoryExport:
    """Create a minimal structured export for tests and incremental migration."""

    return RepositoryExport(
        mode=mode,
        repository=RepositoryMetadata(root_path=root_path, root_name=root_name),
    )
