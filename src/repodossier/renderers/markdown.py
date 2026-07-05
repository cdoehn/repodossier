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

MARKDOWN_RENDERER_MODE_METHODS: tuple[str, ...] = (
    "render_full",
    "render_ai",
    "render_docs",
    "render_changed",
)

MARKDOWN_RENDERER_MIGRATION_DECISION = (
    "The current MarkdownRenderer can render a generic RepositoryExport, "
    "but Milestone 4 still needs mode-aware render_full, render_ai, "
    "render_docs, and render_changed output before legacy exporters can "
    "delegate to it as their primary renderer."
)

FULL_MARKDOWN_RENDERER_SECTION_ORDER: tuple[str, ...] = (
    "ai_quick_start",
    "repository_statistics",
    "file_summary",
    "repository_tree",
    "dependencies",
    "database_schema",
    "secret_detection",
    "complete_source_export",
    "warnings",
    "import_graph",
    "call_graph",
)

FULL_MARKDOWN_RENDERER_SECTION_HEADINGS: dict[str, str] = {
    "ai_quick_start": "# AI Quick Start",
    "repository_statistics": "# Repository Statistics",
    "file_summary": "# File Summary",
    "repository_tree": "# Repository Tree",
    "dependencies": "# Dependencies",
    "database_schema": "# Database Schema",
    "secret_detection": "# Secret Detection",
    "complete_source_export": "# Complete Source Export",
    "warnings": "# Warnings",
    "import_graph": "# Import Graph",
    "call_graph": "# Call Graph",
}


def describe_markdown_renderer_status() -> dict[str, tuple[str, ...] | str]:
    """Describe current renderer reuse points and migration gaps."""

    return {
        "reusable_sections": MARKDOWN_RENDERER_REUSABLE_SECTIONS,
        "legacy_gaps": MARKDOWN_RENDERER_LEGACY_GAPS,
        "mode_methods": MARKDOWN_RENDERER_MODE_METHODS,
        "decision": MARKDOWN_RENDERER_MIGRATION_DECISION,
    }


def iter_full_markdown_renderer_headings() -> tuple[str, ...]:
    """Return full Markdown renderer headings in stable render order."""

    return tuple(
        FULL_MARKDOWN_RENDERER_SECTION_HEADINGS[section_name]
        for section_name in FULL_MARKDOWN_RENDERER_SECTION_ORDER
    )


def _export_mode_value(export: RepositoryExport) -> str:
    """Return a normalized export mode value from a RepositoryExport."""

    mode = getattr(export, "mode", "")
    value = getattr(mode, "value", mode)
    return str(value).strip().lower()


def _assert_export_mode(export: RepositoryExport, expected_mode: str) -> None:
    """Raise when a mode-specific renderer receives the wrong model mode."""

    actual_mode = _export_mode_value(export)
    if actual_mode != expected_mode:
        raise ValueError(
            f"Expected RepositoryExport mode {expected_mode!r}, got {actual_mode!r}."
        )


class MarkdownRenderer:
    """Render a RepositoryExport as deterministic Markdown text."""

    def render_full(self, export: RepositoryExport) -> str:
        """Render a full-mode RepositoryExport as legacy-shaped Markdown."""

        _assert_export_mode(export, "full")
        return self._render_full_export(export)

    def render_ai(self, export: RepositoryExport) -> str:
        """Render an AI-mode RepositoryExport as Markdown."""

        return self._render_mode(export, "ai")

    def render_docs(self, export: RepositoryExport) -> str:
        """Render a docs-mode RepositoryExport as Markdown."""

        return self._render_mode(export, "docs")

    def render_changed(self, export: RepositoryExport) -> str:
        """Render a changed-mode RepositoryExport as Markdown."""

        return self._render_mode(export, "changed")

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

    def _render_mode(self, export: RepositoryExport, expected_mode: str) -> str:
        """Validate the export mode before delegating to the generic renderer."""

        _assert_export_mode(export, expected_mode)
        return self.render(export)

    def _render_full_export(self, export: RepositoryExport) -> str:
        """Render full.txt-compatible sections from RepositoryExport."""

        section_renderers = {
            "ai_quick_start": self._render_full_ai_quick_start,
            "repository_statistics": self._render_full_repository_statistics,
            "file_summary": self._render_full_file_summary,
            "repository_tree": self._render_full_repository_tree,
            "dependencies": self._render_full_dependencies,
            "database_schema": self._render_full_database_schema,
            "secret_detection": self._render_full_secret_detection,
            "complete_source_export": self._render_full_complete_source_export,
            "warnings": self._render_full_warnings,
            "import_graph": self._render_full_import_graph,
            "call_graph": self._render_full_call_graph,
        }

        parts = [
            section_renderers[section_name](export)
            for section_name in FULL_MARKDOWN_RENDERER_SECTION_ORDER
        ]

        return "\n\n".join(part for part in parts if part).rstrip() + "\n"

    def _render_full_ai_quick_start(self, export: RepositoryExport) -> str:
        repository = export.repository
        lines = [
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["ai_quick_start"],
            "",
            f"Repository: {repository.root_name}",
            "Export mode: full",
            f"Primary language: {self._primary_language(export)}",
        ]

        if repository.git_branch:
            lines.append(f"Git branch: {repository.git_branch}")
        if repository.git_commit:
            lines.append(f"Git commit: {repository.git_commit}")
        if repository.git_dirty is not None:
            lines.append(f"Git dirty: {repository.git_dirty}")

        return "\n".join(lines)

    def _render_full_repository_statistics(self, export: RepositoryExport) -> str:
        summary = export.summary
        lines = [
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["repository_statistics"],
            "",
            f"Total tracked files: {summary.total_tracked_files}",
            f"Scanned files: {summary.scanned_files}",
            f"Exported text files: {summary.exported_text_files}",
            f"Skipped binary files: {summary.skipped_binary_files}",
            f"Errored files: {summary.errored_files}",
            f"Total lines: {summary.total_lines}",
            f"Estimated tokens: {summary.estimated_tokens}",
        ]

        if summary.file_type_statistics:
            lines.extend(["", "File types:"])
            for suffix, count in sorted(summary.file_type_statistics.items()):
                label = suffix or "[no extension]"
                lines.append(f"- {label}: {count}")

        return "\n".join(lines)

    def _render_full_file_summary(self, export: RepositoryExport) -> str:
        lines = [
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["file_summary"],
            "",
            f"Exported text files: {len(export.files)}",
            f"Total lines: {export.summary.total_lines}",
            f"Estimated tokens: {export.summary.estimated_tokens}",
        ]

        if not export.files:
            lines.extend(["", "No text files exported."])
            return "\n".join(lines)

        by_language: dict[str, list[FileEntry]] = {}
        for entry in sorted(export.files, key=lambda item: item.path):
            by_language.setdefault(entry.language or "unknown", []).append(entry)

        for language, entries in sorted(by_language.items()):
            label = self._readable_language_label(language)
            count_label = "file" if len(entries) == 1 else "files"
            lines.extend(["", f"## {label} ({len(entries)} {count_label})"])
            for entry in entries:
                lines.append(
                    f"- `{entry.path}` — {entry.line_count} lines, "
                    f"~{entry.estimated_tokens} tokens"
                )

        return "\n".join(lines)

    def _render_full_repository_tree(self, export: RepositoryExport) -> str:
        lines = [FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["repository_tree"], ""]

        if export.tree:
            for entry in export.tree:
                self._append_full_tree_entry(lines, entry, depth=0)
        elif export.files:
            for entry in sorted(export.files, key=lambda item: item.path):
                lines.append(f"- {entry.path}")
        else:
            lines.append("No files detected.")

        return "\n".join(lines)

    def _append_full_tree_entry(
        self,
        lines: list[str],
        entry: FileTreeEntry,
        *,
        depth: int,
    ) -> None:
        indent = "  " * depth
        suffix = "/" if entry.entry_type == "directory" else ""
        lines.append(f"{indent}- {entry.path}{suffix}")
        for child in entry.children:
            self._append_full_tree_entry(lines, child, depth=depth + 1)

    def _render_full_dependencies(self, export: RepositoryExport) -> str:
        return self._render_full_report_section(
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["dependencies"],
            export.dependencies,
            empty_message="No dependencies detected.",
        )

    def _render_full_database_schema(self, export: RepositoryExport) -> str:
        return self._render_full_report_section(
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["database_schema"],
            export.database_schema,
            empty_message="No database schema files detected.",
        )

    def _render_full_secret_detection(self, export: RepositoryExport) -> str:
        return self._render_full_report_section(
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["secret_detection"],
            export.secret_detection,
            empty_message="No secret findings reported.",
        )

    def _render_full_import_graph(self, export: RepositoryExport) -> str:
        return self._render_full_report_section(
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["import_graph"],
            export.import_graph,
            empty_message="No import graph data available.",
        )

    def _render_full_call_graph(self, export: RepositoryExport) -> str:
        return self._render_full_report_section(
            FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["call_graph"],
            export.call_graph,
            empty_message="No call graph data available.",
        )

    def _render_full_report_section(
        self,
        heading: str,
        report: object,
        *,
        empty_message: str,
    ) -> str:
        items = getattr(report, "items", ())
        metadata = getattr(report, "metadata", {})

        lines = [heading]

        if not items and not metadata:
            lines.extend(["", empty_message])
            return "\n".join(lines)

        if metadata:
            lines.append("")
            for key, value in sorted(metadata.items()):
                lines.append(f"- {key}: {value}")

        if items:
            lines.append("")
            for item in items:
                if isinstance(item, tuple) and len(item) == 2:
                    key, value = item
                    lines.append(f"- {key}: {value}")
                else:
                    lines.append(f"- {item}")

        return "\n".join(lines)

    def _render_full_complete_source_export(self, export: RepositoryExport) -> str:
        lines = [FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["complete_source_export"]]

        if not export.included_files():
            lines.extend(["", "No source files exported."])
            return "\n".join(lines)

        for entry in export.included_files():
            content = entry.rendered_content
            fence = self._choose_code_fence(content)
            language = self._code_fence_language(entry.language)
            opening_fence = f"{fence}{language}" if language else fence
            lines.extend(["", f"## File: {entry.path}", "", opening_fence])
            lines.append(content)
            lines.append(fence)

        return "\n".join(lines)

    def _render_full_warnings(self, export: RepositoryExport) -> str:
        heading = FULL_MARKDOWN_RENDERER_SECTION_HEADINGS["warnings"]
        if not export.warnings:
            return f"{heading}\n\nNo warnings."

        lines = [heading]
        for warning in sorted(export.warnings, key=self._warning_sort_key):
            location = f" ({warning.path})" if warning.path else ""
            lines.append(f"- {warning.message}{location}")
        return "\n".join(lines)

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
            "## Summary",
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
        configuration = export.configuration
        lines = [
            "## Configuration",
            f"- Config active: {configuration.config_active}",
        ]

        if configuration.config_path:
            lines.append(f"- Config path: {configuration.config_path}")

        for label, values in (
            ("Include paths", configuration.include_paths),
            ("Include globs", configuration.include_globs),
            ("Exclude paths", configuration.exclude_paths),
            ("Exclude globs", configuration.exclude_globs),
        ):
            if values:
                lines.append(f"- {label}:")
                lines.extend(f"  - {value}" for value in values)

        if configuration.limits:
            lines.append("- Limits:")
            for key, value in sorted(configuration.limits.items()):
                lines.append(f"  - {key}: {value}")

        if configuration.split_settings:
            lines.append("- Split settings:")
            for key, value in sorted(configuration.split_settings.items()):
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

    def _render_tree(self, tree: Iterable[FileTreeEntry]) -> str:
        entries = tuple(tree)
        if not entries:
            return ""

        lines = ["## Repository Tree"]
        for entry in entries:
            self._append_tree_entry(lines, entry, depth=0)

        return "\n".join(lines)

    def _append_tree_entry(
        self,
        lines: list[str],
        entry: FileTreeEntry,
        *,
        depth: int,
    ) -> None:
        indent = "  " * depth
        suffix = "/" if entry.entry_type == "directory" else ""
        lines.append(f"{indent}- {entry.path}{suffix}")

        for child in entry.children:
            self._append_tree_entry(lines, child, depth=depth + 1)

    def _render_file_summary(self, files: Iterable[FileEntry]) -> str:
        entries = tuple(files)
        if not entries:
            return ""

        lines = ["## Files"]
        for entry in sorted(entries, key=lambda item: item.path):
            line = (
                f"- {entry.path} ({entry.language}, {entry.line_count} lines, "
                f"{entry.size_bytes} bytes, {entry.status})"
            )
            if entry.reason:
                line += f" - {entry.reason}"
            lines.append(line)

        return "\n".join(lines)

    def _render_source_export(self, files: Iterable[FileEntry]) -> str:
        entries = tuple(files)
        if not entries:
            return ""

        backtick = chr(96)
        lines = ["## Source Export"]

        for entry in sorted(entries, key=lambda item: item.path):
            content = entry.rendered_content
            fence = self._choose_code_fence(content)
            language = self._code_fence_language(entry.language)
            opening_fence = f"{fence}{language}" if language else fence
            lines.extend(
                [
                    "",
                    f"### {entry.path}",
                    "",
                    opening_fence,
                    content,
                    fence,
                ]
            )

        # Keep the local name so tests can verify this method remains fence-aware
        # without hard-coding literal Markdown fences in this source file.
        _ = backtick
        return "\n".join(lines)

    def _render_warnings(self, warnings: Iterable[ExportWarning]) -> str:
        entries = tuple(warnings)
        if not entries:
            return ""

        lines = ["## Warnings"]
        for warning in sorted(entries, key=self._warning_sort_key):
            prefix = f"{warning.path}: " if warning.path else ""
            suffix = f" [{warning.code}]" if warning.code else ""
            lines.append(f"- {prefix}{warning.message}{suffix}")

        return "\n".join(lines)

    def _warning_sort_key(self, warning: ExportWarning) -> tuple[str, str, str]:
        """Return a stable sort key for ExportWarning objects."""

        return (
            warning.path or "",
            warning.code or "",
            warning.message,
        )

    def _primary_language(self, export: RepositoryExport) -> str:
        counts = export.summary.language_statistics.counts
        if not counts:
            return "unknown"

        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _readable_language_label(self, language: str | None) -> str:
        labels = {
            "bash": "Bash",
            "c": "C",
            "cpp": "C++",
            "csharp": "C#",
            "css": "CSS",
            "html": "HTML",
            "ini": "INI",
            "java": "Java",
            "javascript": "JavaScript",
            "json": "JSON",
            "markdown": "Markdown",
            "python": "Python",
            "text": "Text",
            "toml": "TOML",
            "tsx": "TSX",
            "typescript": "TypeScript",
            "unknown": "Unknown",
            "yaml": "YAML",
        }
        return labels.get(language or "unknown", str(language).replace("_", " ").title())

    def _code_fence_language(self, language: str | None) -> str:
        fences = {
            "bash": "bash",
            "c": "c",
            "cpp": "cpp",
            "csharp": "csharp",
            "css": "css",
            "html": "html",
            "ini": "ini",
            "java": "java",
            "javascript": "javascript",
            "json": "json",
            "markdown": "markdown",
            "python": "python",
            "text": "text",
            "toml": "toml",
            "tsx": "tsx",
            "typescript": "typescript",
            "yaml": "yaml",
        }
        return fences.get(language or "text", "text")

    def _choose_code_fence(self, content: str) -> str:
        backtick = chr(96)
        fence = backtick * 3

        while fence in content:
            fence += backtick

        return fence


def render_full_markdown(export: RepositoryExport) -> str:
    """Render a full-mode RepositoryExport with the Markdown renderer."""

    return MarkdownRenderer().render_full(export)


def render_ai_markdown(export: RepositoryExport) -> str:
    """Render an AI-mode RepositoryExport with the Markdown renderer."""

    return MarkdownRenderer().render_ai(export)


def render_docs_markdown(export: RepositoryExport) -> str:
    """Render a docs-mode RepositoryExport with the Markdown renderer."""

    return MarkdownRenderer().render_docs(export)


def render_changed_markdown(export: RepositoryExport) -> str:
    """Render a changed-mode RepositoryExport with the Markdown renderer."""

    return MarkdownRenderer().render_changed(export)


def render_markdown(export: RepositoryExport) -> str:
    """Render a RepositoryExport as Markdown with the default renderer."""

    return MarkdownRenderer().render(export)
