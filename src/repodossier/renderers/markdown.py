"""Markdown renderer for the structured export model.

This module deliberately only consumes RepositoryExport instances. It must not
read files, inspect Git state, run scanners, or execute analyzer logic. Existing
exporters can be migrated to this renderer incrementally.
"""

from __future__ import annotations

from collections.abc import Iterable

from repodossier.export_model import (
    ExportWarning,
    FileEntry,
    FileTreeEntry,
    RepositoryExport,
)


MARKDOWN_RENDERER_REUSABLE_SECTIONS: tuple[str, ...] = (
    "repository",
    "summary",
    "configuration",
    "language_statistics",
    "repository_tree",
    "file_summary",
    "source_export",
    "warnings",
)

MARKDOWN_RENDERER_LEGACY_GAPS: tuple[str, ...] = (
    "full_legacy_heading_order",
    "ai_legacy_heading_order",
    "docs_legacy_heading_order",
    "changed_legacy_heading_order",
    "dependencies_report_rendering",
    "database_schema_report_rendering",
    "secret_detection_report_rendering",
    "symbol_index_report_rendering",
    "import_graph_report_rendering",
    "call_graph_report_rendering",
    "important_files_rendering",
    "documentation_only_rendering",
    "changed_diff_rendering",
)

MARKDOWN_RENDERER_MIGRATION_DECISION = (
    "The current MarkdownRenderer can render a generic RepositoryExport, "
    "but Milestone 4 still needs mode-aware render_full, render_ai, "
    "render_docs, and render_changed output before legacy exporters can "
    "delegate to it as their primary renderer."
)


def describe_markdown_renderer_status() -> dict[str, tuple[str, ...] | str]:
    """Describe current renderer reuse points and migration gaps.

    This is an explicit Milestone 4 inventory helper. It documents the current
    boundary without performing IO, scanning, Git access, or analyzer work.
    """

    return {
        "reusable_sections": MARKDOWN_RENDERER_REUSABLE_SECTIONS,
        "legacy_gaps": MARKDOWN_RENDERER_LEGACY_GAPS,
        "decision": MARKDOWN_RENDERER_MIGRATION_DECISION,
    }



class MarkdownRenderer:
    """Render a RepositoryExport as deterministic Markdown text."""

    def render(self, export: RepositoryExport) -> str:
        parts: list[str] = [
            self._render_header(export),
            self._render_repository(export),
            self._render_summary(export),
            self._render_configuration(export),
            self._render_language_statistics(export),
            self._render_tree(export.tree),
            self._render_file_summary(export.files),
            self._render_source_export(export.included_files()),
            self._render_warnings(export.warnings),
        ]

        return "\n\n".join(part for part in parts if part).rstrip() + "\n"

    def _render_header(self, export: RepositoryExport) -> str:
        return f"# RepoDossier Export ({export.mode})"

    def _render_repository(self, export: RepositoryExport) -> str:
        repository = export.repository
        lines = [
            "## Repository",
            f"- Root name: {repository.root_name}",
            f"- Root path: {repository.root_path}",
        ]

        if repository.git_branch:
            lines.append(f"- Git branch: {repository.git_branch}")
        if repository.git_commit:
            lines.append(f"- Git commit: {repository.git_commit}")
        if repository.git_dirty is not None:
            lines.append(f"- Git dirty: {repository.git_dirty}")

        return "\n".join(lines)

    def _render_summary(self, export: RepositoryExport) -> str:
        summary = export.summary
        lines = [
            "## Export Summary",
            f"- Total tracked files: {summary.total_tracked_files}",
            f"- Scanned files: {summary.scanned_files}",
            f"- Exported text files: {summary.exported_text_files}",
            f"- Skipped binary files: {summary.skipped_binary_files}",
            f"- Errored files: {summary.errored_files}",
            f"- Total lines: {summary.total_lines}",
            f"- Estimated tokens: {summary.estimated_tokens}",
        ]

        if summary.file_type_statistics:
            lines.append("- File types:")
            for suffix, count in sorted(summary.file_type_statistics.items()):
                label = suffix or "[no extension]"
                lines.append(f"  - {label}: {count}")

        return "\n".join(lines)

    def _render_configuration(self, export: RepositoryExport) -> str:
        config = export.configuration
        lines = [
            "## Configuration",
            f"- Config active: {config.config_active}",
        ]

        if config.config_path:
            lines.append(f"- Config path: {config.config_path}")

        self._append_string_tuple(lines, "Include paths", config.include_paths)
        self._append_string_tuple(lines, "Include globs", config.include_globs)
        self._append_string_tuple(lines, "Exclude paths", config.exclude_paths)
        self._append_string_tuple(lines, "Exclude globs", config.exclude_globs)

        if config.limits:
            lines.append("- Limits:")
            for key, value in sorted(config.limits.items()):
                lines.append(f"  - {key}: {value}")

        if config.split_settings:
            lines.append("- Split settings:")
            for key, value in sorted(config.split_settings.items()):
                lines.append(f"  - {key}: {value}")

        return "\n".join(lines)

    def _render_language_statistics(self, export: RepositoryExport) -> str:
        counts = export.summary.language_statistics.counts
        if not counts:
            return ""

        lines = ["## Language Statistics"]
        for language, count in sorted(counts.items()):
            lines.append(f"- {language}: {count}")
        return "\n".join(lines)

    def _render_tree(self, tree: tuple[FileTreeEntry, ...]) -> str:
        if not tree:
            return ""

        lines = ["## Repository Tree"]
        for entry in tree:
            self._append_tree_entry(lines, entry, depth=0)
        return "\n".join(lines)

    def _append_tree_entry(
        self,
        lines: list[str],
        entry: FileTreeEntry,
        *,
        depth: int,
    ) -> None:
        prefix = "  " * depth
        marker = "/" if entry.entry_type == "directory" else ""
        lines.append(f"{prefix}- {entry.path}{marker}")
        for child in entry.children:
            self._append_tree_entry(lines, child, depth=depth + 1)

    def _render_file_summary(self, files: tuple[FileEntry, ...]) -> str:
        if not files:
            return ""

        lines = ["## File Summary"]
        for file in sorted(files, key=lambda item: item.path):
            detail = (
                f"{file.path} "
                f"({file.language}, {file.line_count} lines, "
                f"{file.size_bytes} bytes, {file.status})"
            )
            if file.reason:
                detail += f" - {file.reason}"
            lines.append(f"- {detail}")

        return "\n".join(lines)

    def _render_source_export(self, files: tuple[FileEntry, ...]) -> str:
        included = [file for file in files if file.rendered_content is not None]
        if not included:
            return ""

        fence = "`" * 3
        lines = ["## Source Export"]

        for file in sorted(included, key=lambda item: item.path):
            language = file.language if file.language not in {"text", "unknown"} else ""
            lines.append(f"### {file.path}")
            lines.append(f"{fence}{language}")
            lines.append(file.rendered_content or "")
            lines.append(fence)

        return "\n".join(lines)

    def _render_warnings(self, warnings: tuple[ExportWarning, ...]) -> str:
        if not warnings:
            return ""

        lines = ["## Warnings"]
        for warning in warnings:
            prefix = f"{warning.path}: " if warning.path else ""
            suffix = f" [{warning.code}]" if warning.code else ""
            lines.append(f"- {prefix}{warning.message}{suffix}")
        return "\n".join(lines)

    def _append_string_tuple(
        self,
        lines: list[str],
        label: str,
        values: Iterable[str],
    ) -> None:
        values = tuple(values)
        if not values:
            return

        lines.append(f"- {label}:")
        for value in values:
            lines.append(f"  - {value}")


def render_markdown(export: RepositoryExport) -> str:
    """Convenience wrapper for rendering Markdown exports."""

    return MarkdownRenderer().render(export)
