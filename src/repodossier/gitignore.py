"""Helpers for managing RepoDossier .gitignore entries."""

from __future__ import annotations

from pathlib import Path

REPODOSSIER_EXPORT_FILES: tuple[str, ...] = (
    "full.txt",
    "ai.txt",
    "docs.txt",
    "changed.txt",
)

REPODOSSIER_GITIGNORE_HEADER = "# RepoDossier exports"

__all__ = [
    "GitignoreUpdateError",
    "REPODOSSIER_EXPORT_FILES",
    "REPODOSSIER_GITIGNORE_HEADER",
    "ensure_repodossier_gitignore_entries",
    "render_repodossier_gitignore_entries",
]


class GitignoreUpdateError(RuntimeError):
    """Raised when RepoDossier cannot update .gitignore."""


def ensure_repodossier_gitignore_entries(repository_root: Path | str) -> bool:
    """Ensure RepoDossier export files are ignored by Git.

    Parameters
    ----------
    repository_root:
        Repository root where ``.gitignore`` should be managed.

    Returns
    -------
    bool
        True if ``.gitignore`` was created or changed, False if it already
        contained all required entries.
    """
    gitignore_path = Path(repository_root).resolve() / ".gitignore"

    try:
        current_text = (
            gitignore_path.read_text(encoding="utf-8")
            if gitignore_path.exists()
            else ""
        )
    except OSError as exc:
        raise GitignoreUpdateError(f"Could not read {gitignore_path}: {exc}") from exc

    updated_text = render_repodossier_gitignore_entries(current_text)
    if updated_text == current_text:
        return False

    try:
        gitignore_path.write_text(updated_text, encoding="utf-8")
    except OSError as exc:
        raise GitignoreUpdateError(f"Could not write {gitignore_path}: {exc}") from exc

    return True


def render_repodossier_gitignore_entries(gitignore_text: str) -> str:
    """Return .gitignore text with missing RepoDossier export entries added."""
    missing_entries = _missing_repodossier_entries(gitignore_text)
    if not missing_entries:
        return gitignore_text

    if not gitignore_text.strip():
        return _format_repodossier_block(missing_entries)

    lines = gitignore_text.splitlines()
    header_index = _find_repodossier_header_index(lines)

    if header_index is not None:
        updated_lines = _insert_entries_into_existing_block(
            lines,
            header_index,
            missing_entries,
        )
        return _normalize_lines(updated_lines)

    return _append_repodossier_block(gitignore_text, missing_entries)


def _missing_repodossier_entries(gitignore_text: str) -> tuple[str, ...]:
    """Return required RepoDossier entries not already present anywhere."""
    existing_entries = {
        line.strip()
        for line in gitignore_text.splitlines()
        if line.strip()
    }
    return tuple(
        export_file
        for export_file in REPODOSSIER_EXPORT_FILES
        if export_file not in existing_entries
    )


def _find_repodossier_header_index(lines: list[str]) -> int | None:
    """Return the index of the RepoDossier block header if present."""
    for index, line in enumerate(lines):
        if line.strip() == REPODOSSIER_GITIGNORE_HEADER:
            return index
    return None


def _insert_entries_into_existing_block(
    lines: list[str],
    header_index: int,
    missing_entries: tuple[str, ...],
) -> list[str]:
    """Insert missing entries into an existing RepoDossier block."""
    insert_index = header_index + 1

    while insert_index < len(lines):
        stripped_line = lines[insert_index].strip()
        if stripped_line in REPODOSSIER_EXPORT_FILES:
            insert_index += 1
            continue
        break

    return [
        *lines[:insert_index],
        *missing_entries,
        *lines[insert_index:],
    ]


def _append_repodossier_block(
    gitignore_text: str,
    missing_entries: tuple[str, ...],
) -> str:
    """Append a new RepoDossier block to existing .gitignore text."""
    existing_text = gitignore_text.rstrip("\n")
    block = _format_repodossier_block(missing_entries)

    if not existing_text:
        return block

    return f"{existing_text}\n\n{block}"


def _format_repodossier_block(entries: tuple[str, ...]) -> str:
    """Format a RepoDossier .gitignore block."""
    return "\n".join((REPODOSSIER_GITIGNORE_HEADER, *entries)) + "\n"


def _normalize_lines(lines: list[str]) -> str:
    """Format changed .gitignore lines with one final newline."""
    return "\n".join(lines).rstrip("\n") + "\n"
