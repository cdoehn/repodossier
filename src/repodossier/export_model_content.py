"""Content helpers for RepoDossier's structured export model."""

from __future__ import annotations

from repodossier.export_model import FileEntry, FileStatus, TextStatus


def content_line_count(content: str | None) -> int:
    """Return a deterministic line count for optional text content."""

    if content is None or content == "":
        return 0

    return len(content.splitlines())


def content_size_bytes(content: str | None, *, encoding: str = "utf-8") -> int:
    """Return the encoded byte size for optional text content."""

    if content is None:
        return 0

    return len(content.encode(encoding))


def estimate_tokens_from_content(content: str | None) -> int:
    """Return a conservative deterministic token estimate.

    This helper is intentionally simple and dependency-free. It is meant for
    model construction defaults, not for exact tokenizer accounting.
    """

    if not content:
        return 0

    return max(1, (len(content) + 3) // 4)


def file_entry_content_for_rendering(entry: FileEntry) -> str | None:
    """Return exportable text content for a file entry.

    Binary files never expose content through this helper. Masked content is
    preferred over raw content through FileEntry.rendered_content.
    """

    if entry.text_status == "binary":
        return None

    return entry.rendered_content


def file_entry_has_exportable_content(entry: FileEntry) -> bool:
    """Return whether a file entry has text content suitable for renderers."""

    return file_entry_content_for_rendering(entry) is not None


def make_file_entry_from_content(
    *,
    path: str,
    language: str,
    content: str | None,
    masked_content: str | None = None,
    text_status: TextStatus = "text",
    status: FileStatus = "included",
    size_bytes: int | None = None,
    line_count: int | None = None,
    estimated_tokens: int | None = None,
    reason: str | None = None,
) -> FileEntry:
    """Build a FileEntry with deterministic derived content metadata."""

    stats_content = content if content is not None else masked_content

    return FileEntry(
        path=path,
        language=language,
        size_bytes=(
            content_size_bytes(stats_content)
            if size_bytes is None
            else size_bytes
        ),
        line_count=(
            content_line_count(stats_content)
            if line_count is None
            else line_count
        ),
        estimated_tokens=(
            estimate_tokens_from_content(stats_content)
            if estimated_tokens is None
            else estimated_tokens
        ),
        text_status=text_status,
        status=status,
        content=content,
        masked_content=masked_content,
        reason=reason,
    )
