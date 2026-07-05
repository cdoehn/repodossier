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

MARKDOWN_RENDERER_MODE_DISPATCH: dict[str, str] = {
    "full": "render_full",
    "ai": "render_ai",
    "docs": "render_docs",
    "changed": "render_changed",
}

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


AI_MARKDOWN_RENDERER_SECTION_ORDER: tuple[str, ...] = (
    "document_header",
    "project",
    "architecture_summary",
    "important_files",
    "dependencies",
    "database_schema",
    "symbol_index",
    "import_graph",
    "call_graph",
    "notes",
)

AI_MARKDOWN_RENDERER_SECTION_HEADINGS: dict[str, str] = {
    "document_header": "# AI CONTEXT",
    "project": "## Project",
    "architecture_summary": "## Architecture Summary",
    "important_files": "## Important Files",
    "dependencies": "## Dependencies",
    "database_schema": "## Database Schema",
    "symbol_index": "## Symbol Index",
    "import_graph": "## Import Graph",
    "call_graph": "## Call Graph",
    "notes": "## Notes",
}


def iter_ai_markdown_renderer_headings() -> tuple[str, ...]:
    """Return AI Markdown renderer headings in stable render order."""

    return tuple(
        AI_MARKDOWN_RENDERER_SECTION_HEADINGS[section_name]
        for section_name in AI_MARKDOWN_RENDERER_SECTION_ORDER
    )


DOCS_MARKDOWN_RENDERER_SECTION_ORDER: tuple[str, ...] = (
    "document_header",
    "documentation_quick_start",
    "documentation_summary",
    "documentation_files",
    "extracted_documents",
    "warnings",
)

DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS: dict[str, str] = {
    "document_header": "# Documentation Context",
    "documentation_quick_start": "## Documentation Quick Start",
    "documentation_summary": "## Documentation Summary",
    "documentation_files": "## Documentation Files",
    "extracted_documents": "## Extracted Documents",
    "warnings": "## Warnings",
}


def iter_docs_markdown_renderer_headings() -> tuple[str, ...]:
    """Return docs Markdown renderer headings in stable render order."""

    return tuple(
        DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS[section_name]
        for section_name in DOCS_MARKDOWN_RENDERER_SECTION_ORDER
    )


CHANGED_MARKDOWN_RENDERER_SECTION_ORDER: tuple[str, ...] = (
    "document_header",
    "changed_files_summary",
    "changed_files",
    "git_diff",
    "changed_file_contents",
    "deleted_files",
    "binary_or_skipped_files",
)

CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS: dict[str, str] = {
    "document_header": "# Changed Export",
    "changed_files_summary": "# Changed Files Summary",
    "changed_files": "# Changed Files",
    "git_diff": "# Git Diff",
    "changed_file_contents": "# Changed File Contents",
    "deleted_files": "# Deleted Files",
    "binary_or_skipped_files": "# Binary / Skipped Files",
}


def iter_changed_markdown_renderer_headings() -> tuple[str, ...]:
    """Return changed Markdown renderer headings in stable render order."""

    return tuple(
        CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS[section_name]
        for section_name in CHANGED_MARKDOWN_RENDERER_SECTION_ORDER
    )


def describe_markdown_renderer_status() -> dict[str, tuple[str, ...] | str]:
    """Describe current renderer reuse points and migration gaps."""

    return {
        "reusable_sections": MARKDOWN_RENDERER_REUSABLE_SECTIONS,
        "legacy_gaps": MARKDOWN_RENDERER_LEGACY_GAPS,
        "mode_methods": MARKDOWN_RENDERER_MODE_METHODS,
        "mode_dispatch": MARKDOWN_RENDERER_MODE_DISPATCH,
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

    def render_mode(self, export: RepositoryExport) -> str:
        """Render a RepositoryExport through its mode-specific entrypoint."""

        mode = _export_mode_value(export)
        method_name = MARKDOWN_RENDERER_MODE_DISPATCH.get(mode)
        if method_name is None:
            supported_modes = ", ".join(sorted(MARKDOWN_RENDERER_MODE_DISPATCH))
            raise ValueError(
                f"Unsupported RepositoryExport mode {mode!r}. "
                f"Supported modes: {supported_modes}."
            )

        return getattr(self, method_name)(export)

    def render_full(self, export: RepositoryExport) -> str:
        """Render a full-mode RepositoryExport as legacy-shaped Markdown."""

        _assert_export_mode(export, "full")
        return self._render_full_export(export)

    def render_ai(self, export: RepositoryExport) -> str:
        """Render an AI-mode RepositoryExport as compact Markdown."""

        _assert_export_mode(export, "ai")
        return self._render_ai_export(export)

    def _render_ai_export(self, export: RepositoryExport) -> str:
        """Render ai.txt-compatible compact sections from RepositoryExport."""

        section_renderers = {
            "document_header": self._render_ai_document_header,
            "project": self._render_ai_project,
            "architecture_summary": self._render_ai_architecture_summary,
            "important_files": self._render_ai_important_files,
            "dependencies": self._render_ai_dependencies,
            "database_schema": self._render_ai_database_schema,
            "symbol_index": self._render_ai_symbol_index,
            "import_graph": self._render_ai_import_graph,
            "call_graph": self._render_ai_call_graph,
            "notes": self._render_ai_notes,
        }

        parts = [
            section_renderers[section_name](export)
            for section_name in AI_MARKDOWN_RENDERER_SECTION_ORDER
        ]

        return "\n\n".join(part for part in parts if part).rstrip() + "\n"

    def _render_ai_document_header(self, export: RepositoryExport) -> str:
        return AI_MARKDOWN_RENDERER_SECTION_HEADINGS["document_header"]

    def _render_ai_project(self, export: RepositoryExport) -> str:
        summary = export.summary
        repository = export.repository
        lines = [
            AI_MARKDOWN_RENDERER_SECTION_HEADINGS["project"],
            "",
            f"Repository: {repository.root_name}",
            f"Mode: {export.mode}",
            f"Tracked files: {summary.total_tracked_files}",
            f"Exported text files: {summary.exported_text_files}",
            f"Estimated tokens: {summary.estimated_tokens}",
            f"Primary language: {self._primary_language(export)}",
        ]

        if repository.git_branch:
            lines.append(f"Git branch: {repository.git_branch}")
        if repository.git_commit:
            lines.append(f"Git commit: {repository.git_commit}")

        return "\n".join(lines)

    def _render_ai_architecture_summary(self, export: RepositoryExport) -> str:
        lines = [AI_MARKDOWN_RENDERER_SECTION_HEADINGS["architecture_summary"]]

        top_level_dirs = sorted(
            {
                entry.path.split("/", 1)[0]
                for entry in export.files + export.omitted_files + export.truncated_files
                if "/" in entry.path
            }
        )
        root_files = sorted(
            {
                entry.path
                for entry in export.files + export.omitted_files + export.truncated_files
                if "/" not in entry.path
            }
        )
        languages = export.summary.language_statistics.counts

        lines.append("")
        lines.append(f"Top-level directories: {', '.join(top_level_dirs) if top_level_dirs else 'none detected'}")
        lines.append(f"Root files: {', '.join(root_files[:8]) if root_files else 'none detected'}")

        if languages:
            language_summary = ", ".join(
                f"{language}: {count}" for language, count in sorted(languages.items())
            )
            lines.append(f"Languages: {language_summary}")
        else:
            lines.append("Languages: none detected")

        return "\n".join(lines)

    def _render_ai_important_files(self, export: RepositoryExport) -> str:
        lines = [AI_MARKDOWN_RENDERER_SECTION_HEADINGS["important_files"]]

        candidates = sorted(
            export.files,
            key=lambda entry: (
                0 if entry.path in {"README.md", "pyproject.toml"} else 1,
                0 if entry.path.endswith("cli.py") or entry.path.endswith("__main__.py") else 1,
                entry.path.count("/"),
                entry.path,
            ),
        )

        if not candidates:
            lines.extend(["", "No important files available in the model."])
            return "\n".join(lines)

        for entry in candidates[:12]:
            reason = "model file entry"
            if entry.path == "README.md":
                reason = "primary documentation"
            elif entry.path == "pyproject.toml":
                reason = "project configuration"
            elif entry.path.endswith("cli.py") or entry.path.endswith("__main__.py"):
                reason = "likely entry point"
            lines.append(f"- {entry.path}")
            lines.append(f"  Reason: {reason}")

        return "\n".join(lines)

    def _render_ai_dependencies(self, export: RepositoryExport) -> str:
        return self._render_ai_report_section(
            AI_MARKDOWN_RENDERER_SECTION_HEADINGS["dependencies"],
            export.dependencies,
            empty_message="No dependencies detected.",
        )

    def _render_ai_database_schema(self, export: RepositoryExport) -> str:
        return self._render_ai_report_section(
            AI_MARKDOWN_RENDERER_SECTION_HEADINGS["database_schema"],
            export.database_schema,
            empty_message="No database schema files detected.",
        )

    def _render_ai_symbol_index(self, export: RepositoryExport) -> str:
        return self._render_ai_report_section(
            AI_MARKDOWN_RENDERER_SECTION_HEADINGS["symbol_index"],
            export.symbol_index,
            empty_message="No symbol index data available.",
        )

    def _render_ai_import_graph(self, export: RepositoryExport) -> str:
        return self._render_ai_report_section(
            AI_MARKDOWN_RENDERER_SECTION_HEADINGS["import_graph"],
            export.import_graph,
            empty_message="No import graph data available.",
        )

    def _render_ai_call_graph(self, export: RepositoryExport) -> str:
        return self._render_ai_report_section(
            AI_MARKDOWN_RENDERER_SECTION_HEADINGS["call_graph"],
            export.call_graph,
            empty_message="No call graph data available.",
        )

    def _render_ai_notes(self, export: RepositoryExport) -> str:
        lines = [AI_MARKDOWN_RENDERER_SECTION_HEADINGS["notes"]]

        if not export.warnings and not export.omitted_files and not export.truncated_files:
            lines.extend(["", "No notes."])
            return "\n".join(lines)

        if export.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in sorted(export.warnings, key=self._warning_sort_key):
                prefix = f"{warning.path}: " if warning.path else ""
                suffix = f" [{warning.code}]" if warning.code else ""
                lines.append(f"- {prefix}{warning.message}{suffix}")

        if export.omitted_files:
            lines.append("")
            lines.append("Omitted files:")
            for entry in sorted(export.omitted_files, key=lambda item: item.path)[:20]:
                reason = f" - {entry.reason}" if entry.reason else ""
                lines.append(f"- {entry.path} ({entry.status}){reason}")

        if export.truncated_files:
            lines.append("")
            lines.append("Truncated files:")
            for entry in sorted(export.truncated_files, key=lambda item: item.path)[:20]:
                reason = f" - {entry.reason}" if entry.reason else ""
                lines.append(f"- {entry.path} ({entry.status}){reason}")

        return "\n".join(lines)

    def _render_ai_report_section(
        self,
        heading: str,
        report: object,
        *,
        empty_message: str,
    ) -> str:
        items = self._report_items(report)

        if not items:
            return f"{heading}\n\n{empty_message}"

        lines = [heading]
        for item in items[:40]:
            lines.append(f"- {self._format_report_item(item)}")

        return "\n".join(lines)

    def _report_items(self, report: object) -> tuple[object, ...]:
        for attribute in ("items", "symbols", "edges", "findings", "mappings", "commits"):
            value = getattr(report, attribute, ())
            if value:
                return tuple(value)

        masked_files = getattr(report, "masked_files", ())
        if masked_files:
            return tuple({"masked_file": path} for path in masked_files)

        return ()

    def _format_report_item(self, item: object) -> str:
        if isinstance(item, dict):
            return ", ".join(
                f"{key}: {value}" for key, value in sorted(item.items())
            )
        if isinstance(item, tuple) and len(item) == 2:
            return f"{item[0]}: {item[1]}"
        return str(item)

    def render_docs(self, export: RepositoryExport) -> str:
        """Render a docs-mode RepositoryExport as documentation Markdown."""

        _assert_export_mode(export, "docs")
        return self._render_docs_export(export)

    def _render_docs_export(self, export: RepositoryExport) -> str:
        """Render docs.txt-compatible sections from RepositoryExport."""

        section_renderers = {
            "document_header": self._render_docs_document_header,
            "documentation_quick_start": self._render_docs_quick_start,
            "documentation_summary": self._render_docs_summary,
            "documentation_files": self._render_docs_files,
            "extracted_documents": self._render_docs_extracted_documents,
            "warnings": self._render_docs_warnings,
        }

        parts = [
            section_renderers[section_name](export)
            for section_name in DOCS_MARKDOWN_RENDERER_SECTION_ORDER
        ]

        return "\n\n".join(part for part in parts if part).rstrip() + "\n"

    def _render_docs_document_header(self, export: RepositoryExport) -> str:
        return DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS["document_header"]

    def _render_docs_quick_start(self, export: RepositoryExport) -> str:
        repository = export.repository
        docs_files = self._documentation_files(export)
        lines = [
            DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS["documentation_quick_start"],
            "",
            f"Repository: {repository.root_name}",
            f"Documentation files: {len(docs_files)}",
            f"Estimated tokens: {export.summary.estimated_tokens}",
        ]

        if docs_files:
            lines.append(f"Start with: {docs_files[0].path}")

        return "\n".join(lines)

    def _render_docs_summary(self, export: RepositoryExport) -> str:
        docs_files = self._documentation_files(export)
        omitted_docs = self._documentation_files_from_entries(export.omitted_files)
        truncated_docs = self._documentation_files_from_entries(export.truncated_files)

        lines = [
            DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS["documentation_summary"],
            "",
            f"Tracked files: {export.summary.total_tracked_files}",
            f"Scanned files: {export.summary.scanned_files}",
            f"Documentation files included: {len(docs_files)}",
            f"Documentation files omitted: {len(omitted_docs)}",
            f"Documentation files truncated: {len(truncated_docs)}",
        ]

        if docs_files:
            total_lines = sum(entry.line_count for entry in docs_files)
            total_tokens = sum(entry.estimated_tokens for entry in docs_files)
            lines.append(f"Documentation lines: {total_lines}")
            lines.append(f"Documentation estimated tokens: {total_tokens}")

        return "\n".join(lines)

    def _render_docs_files(self, export: RepositoryExport) -> str:
        docs_files = self._documentation_files(export)
        omitted_docs = self._documentation_files_from_entries(export.omitted_files)
        truncated_docs = self._documentation_files_from_entries(export.truncated_files)

        lines = [DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS["documentation_files"]]

        if not docs_files and not omitted_docs and not truncated_docs:
            lines.extend(["", "No documentation files detected."])
            return "\n".join(lines)

        if docs_files:
            lines.append("")
            lines.append("Included:")
            for entry in docs_files:
                lines.append(
                    f"- {entry.path} ({entry.language}, {entry.line_count} lines, "
                    f"{entry.size_bytes} bytes, {entry.status})"
                )

        if omitted_docs:
            lines.append("")
            lines.append("Omitted:")
            for entry in omitted_docs:
                reason = f" - {entry.reason}" if entry.reason else ""
                lines.append(f"- {entry.path} ({entry.status}){reason}")

        if truncated_docs:
            lines.append("")
            lines.append("Truncated:")
            for entry in truncated_docs:
                reason = f" - {entry.reason}" if entry.reason else ""
                lines.append(f"- {entry.path} ({entry.status}){reason}")

        return "\n".join(lines)

    def _render_docs_extracted_documents(self, export: RepositoryExport) -> str:
        docs_files = self._documentation_files(export)
        lines = [DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS["extracted_documents"]]

        if not docs_files:
            lines.extend(["", "No documentation content exported."])
            return "\n".join(lines)

        for entry in docs_files:
            content = entry.rendered_content
            fence = self._choose_code_fence(content)
            language = self._code_fence_language(entry.language)
            opening_fence = f"{fence}{language}" if language else fence
            lines.extend(["", f"### {entry.path}", "", opening_fence])
            lines.append(content)
            lines.append(fence)

        return "\n".join(lines)

    def _render_docs_warnings(self, export: RepositoryExport) -> str:
        heading = DOCS_MARKDOWN_RENDERER_SECTION_HEADINGS["warnings"]
        relevant_warnings = tuple(
            warning
            for warning in export.warnings
            if not warning.path or self._is_documentation_path(warning.path)
        )

        if not relevant_warnings:
            return f"{heading}\n\nNo documentation warnings."

        lines = [heading]
        for warning in sorted(relevant_warnings, key=self._warning_sort_key):
            prefix = f"{warning.path}: " if warning.path else ""
            suffix = f" [{warning.code}]" if warning.code else ""
            lines.append(f"- {prefix}{warning.message}{suffix}")

        return "\n".join(lines)

    def _documentation_files(self, export: RepositoryExport) -> tuple[FileEntry, ...]:
        return self._documentation_files_from_entries(export.files)

    def _documentation_files_from_entries(
        self,
        entries: Iterable[FileEntry],
    ) -> tuple[FileEntry, ...]:
        return tuple(
            sorted(
                (
                    entry
                    for entry in entries
                    if self._is_documentation_entry(entry)
                ),
                key=lambda item: item.path,
            )
        )

    def _is_documentation_entry(self, entry: FileEntry) -> bool:
        return self._is_documentation_path(entry.path) or (
            entry.language in {"markdown", "rst", "text"} and "/" not in entry.path
        )

    def _is_documentation_path(self, path: str) -> bool:
        normalized = path.lower()
        documentation_names = {
            "readme",
            "license",
            "changelog",
            "contributing",
            "code_of_conduct",
            "security",
            "authors",
            "notice",
        }
        documentation_suffixes = (
            ".md",
            ".markdown",
            ".rst",
            ".txt",
            ".adoc",
        )
        basename = normalized.rsplit("/", 1)[-1]
        stem = basename.rsplit(".", 1)[0]

        return (
            normalized.startswith("docs/")
            or normalized.startswith("doc/")
            or "/docs/" in normalized
            or "/doc/" in normalized
            or stem in documentation_names
            or basename.endswith(documentation_suffixes)
        )

    def render_changed(self, export: RepositoryExport) -> str:
        """Render a changed-mode RepositoryExport as changed Markdown."""

        _assert_export_mode(export, "changed")
        return self._render_changed_export(export)

    def _render_changed_export(self, export: RepositoryExport) -> str:
        """Render changed.txt-compatible sections from RepositoryExport."""

        section_renderers = {
            "document_header": self._render_changed_document_header,
            "changed_files_summary": self._render_changed_files_summary,
            "changed_files": self._render_changed_files,
            "git_diff": self._render_changed_git_diff,
            "changed_file_contents": self._render_changed_file_contents,
            "deleted_files": self._render_changed_deleted_files,
            "binary_or_skipped_files": self._render_changed_binary_or_skipped_files,
        }

        parts = [
            section_renderers[section_name](export)
            for section_name in CHANGED_MARKDOWN_RENDERER_SECTION_ORDER
        ]

        return "\n\n".join(part for part in parts if part).rstrip() + "\n"

    def _render_changed_document_header(self, export: RepositoryExport) -> str:
        repository = export.repository
        lines = [
            CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS["document_header"],
            "",
            f"Repository path: {repository.root_path}",
            "Compare mode: model",
        ]

        if repository.git_branch:
            lines.append(f"Git branch: {repository.git_branch}")
        if repository.git_commit:
            lines.append(f"Git commit: {repository.git_commit}")
        if repository.git_dirty is not None:
            lines.append(f"Git dirty: {repository.git_dirty}")

        return "\n".join(lines)

    def _render_changed_files_summary(self, export: RepositoryExport) -> str:
        included = tuple(sorted(export.files, key=lambda item: item.path))
        deleted = self._changed_deleted_files(export)
        skipped = self._changed_binary_or_skipped_files(export)

        lines = [
            CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS["changed_files_summary"],
            "",
            f"Changed text files: {len(included)}",
            f"Deleted files: {len(deleted)}",
            f"Binary / skipped files: {len(skipped)}",
            f"Warnings: {len(export.warnings)}",
            f"Estimated tokens: {export.summary.estimated_tokens}",
        ]

        return "\n".join(lines)

    def _render_changed_files(self, export: RepositoryExport) -> str:
        lines = [CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS["changed_files"]]
        entries = tuple(sorted(export.files, key=lambda item: item.path))

        if not entries:
            lines.extend(["", "No changed text files."])
            return "\n".join(lines)

        for entry in entries:
            lines.append(
                f"- {entry.path} ({entry.language}, {entry.line_count} lines, "
                f"{entry.size_bytes} bytes, {entry.status})"
            )

        return "\n".join(lines)

    def _render_changed_git_diff(self, export: RepositoryExport) -> str:
        lines = [CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS["git_diff"]]
        diff_text = self._metadata_value(export, "git_diff")

        if not diff_text:
            lines.extend(["", "No git diff available in export model."])
            return "\n".join(lines)

        fence = self._choose_code_fence(str(diff_text))
        lines.extend(["", f"{fence}diff", str(diff_text), fence])
        return "\n".join(lines)

    def _render_changed_file_contents(self, export: RepositoryExport) -> str:
        lines = [CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS["changed_file_contents"]]
        entries = tuple(sorted(export.included_files(), key=lambda item: item.path))

        if not entries:
            lines.extend(["", "No changed file contents exported."])
            return "\n".join(lines)

        for entry in entries:
            content = entry.rendered_content
            fence = self._choose_code_fence(content)
            language = self._code_fence_language(entry.language)
            opening_fence = f"{fence}{language}" if language else fence
            lines.extend(["", f"## File: {entry.path}", "", opening_fence])
            lines.append(content)
            lines.append(fence)

        return "\n".join(lines)

    def _render_changed_deleted_files(self, export: RepositoryExport) -> str:
        lines = [CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS["deleted_files"]]
        entries = self._changed_deleted_files(export)

        if not entries:
            lines.extend(["", "No deleted files."])
            return "\n".join(lines)

        for entry in entries:
            reason = f" - {entry.reason}" if entry.reason else ""
            lines.append(f"- {entry.path} ({entry.status}){reason}")

        return "\n".join(lines)

    def _render_changed_binary_or_skipped_files(self, export: RepositoryExport) -> str:
        lines = [CHANGED_MARKDOWN_RENDERER_SECTION_HEADINGS["binary_or_skipped_files"]]
        entries = self._changed_binary_or_skipped_files(export)

        if not entries:
            lines.extend(["", "No binary or skipped files."])
            return "\n".join(lines)

        for entry in entries:
            reason = f" - {entry.reason}" if entry.reason else ""
            text_status = f", {entry.text_status}" if entry.text_status else ""
            lines.append(f"- {entry.path} ({entry.status}{text_status}){reason}")

        return "\n".join(lines)

    def _changed_deleted_files(self, export: RepositoryExport) -> tuple[FileEntry, ...]:
        return tuple(
            sorted(
                (
                    entry
                    for entry in export.omitted_files + export.truncated_files
                    if entry.status == "deleted"
                    or (entry.reason is not None and "deleted" in entry.reason.lower())
                ),
                key=lambda item: item.path,
            )
        )

    def _changed_binary_or_skipped_files(self, export: RepositoryExport) -> tuple[FileEntry, ...]:
        return tuple(
            sorted(
                (
                    entry
                    for entry in export.omitted_files + export.truncated_files
                    if entry.status != "deleted"
                    and not (entry.reason is not None and "deleted" in entry.reason.lower())
                ),
                key=lambda item: item.path,
            )
        )

    def _metadata_value(self, export: RepositoryExport, key: str) -> object | None:
        for report in (
            export.dependencies,
            export.database_schema,
            export.secret_detection,
            export.symbol_index,
            export.import_graph,
            export.call_graph,
            export.test_map,
            export.recent_commits,
        ):
            metadata = getattr(report, "metadata", None)
            if isinstance(metadata, dict) and key in metadata:
                return metadata[key]

        return None

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


def render_mode_markdown(export: RepositoryExport) -> str:
    """Render a RepositoryExport using its mode-specific Markdown renderer."""

    return MarkdownRenderer().render_mode(export)


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
