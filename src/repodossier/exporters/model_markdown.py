"""Model-only Markdown exporter helpers.

These helpers are the central bridge between RepositoryExport and the
mode-aware Markdown renderer. They intentionally do not scan repositories,
inspect Git state, collect changed files, or run analyzers.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from repodossier.export_model import RepositoryExport
from repodossier.renderers import render_mode_markdown


def render_markdown_export_from_model(export: RepositoryExport) -> str:
    """Render Markdown for a RepositoryExport using its export mode."""

    return render_mode_markdown(export)


def write_markdown_export_from_model(
    export: RepositoryExport,
    output_path: str | Path,
) -> None:
    """Write mode-specific Markdown for a RepositoryExport to a file path."""

    Path(output_path).write_text(
        render_markdown_export_from_model(export),
        encoding="utf-8",
    )


def write_markdown_export_model_to_stream(
    export: RepositoryExport,
    stream: TextIO,
) -> None:
    """Write mode-specific Markdown for a RepositoryExport to a text stream."""

    stream.write(render_markdown_export_from_model(export))
