from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from repocontext.changed import ChangedFileScan, collect_changed_file_scans


def _metadata_value(file_info: Any | None, names: Sequence[str], default: Any = None) -> Any:
    if file_info is None:
        return default

    for name in names:
        if hasattr(file_info, name):
            return getattr(file_info, name)

    return default


def _language_for(scan: ChangedFileScan) -> str:
    language = _metadata_value(scan.file_info, ["language", "detected_language"], None)
    if language:
        return str(language)

    suffix = Path(scan.path).suffix.lstrip(".")
    return suffix or "unknown"


def _line_count_for(scan: ChangedFileScan) -> int | str:
    return _metadata_value(scan.file_info, ["line_count", "lines", "num_lines"], "unknown")


def _token_estimate_for(scan: ChangedFileScan) -> int | str:
    return _metadata_value(
        scan.file_info,
        ["token_estimate", "estimated_tokens", "tokens"],
        "unknown",
    )


def _read_changed_file_content(repo_path: Path, scan: ChangedFileScan) -> str:
    file_path = repo_path / scan.path
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"[Could not read file: {exc}]"


def _append_summary(lines: list[str], scans: Sequence[ChangedFileScan]) -> None:
    status_counts = Counter(scan.status for scan in scans)
    deleted_count = sum(1 for scan in scans if scan.is_deleted)
    binary_count = sum(1 for scan in scans if scan.is_binary)
    text_count = sum(
        1
        for scan in scans
        if not scan.is_deleted and not scan.is_binary and scan.file_info is not None
    )

    lines.extend(
        [
            "# Changed Files Summary",
            "",
            f"- Total: {len(scans)}",
            f"- Modified: {status_counts.get('modified', 0)}",
            f"- Added: {status_counts.get('added', 0)}",
            f"- Deleted: {deleted_count}",
            f"- Renamed: {status_counts.get('renamed', 0)}",
            f"- Untracked: {status_counts.get('untracked', 0)}",
            f"- Text files: {text_count}",
            f"- Binary/skipped files: {binary_count}",
            "",
        ]
    )


def _append_file_overview(lines: list[str], scans: Sequence[ChangedFileScan]) -> None:
    lines.extend(["# Changed Files", ""])

    if not scans:
        lines.extend(["No changed files detected.", ""])
        return

    for scan in scans:
        markers: list[str] = [scan.status]
        if scan.is_deleted:
            markers.append("deleted")
        if scan.is_untracked:
            markers.append("untracked")
        if scan.is_binary:
            markers.append("binary/skipped")
        lines.append(f"- `{scan.path}` ({', '.join(markers)})")

    lines.append("")


def _append_changed_file_contents(
    lines: list[str],
    repo_path: Path,
    scans: Sequence[ChangedFileScan],
) -> None:
    lines.extend(["# Changed File Contents", ""])

    text_scans = [
        scan
        for scan in scans
        if not scan.is_deleted and not scan.is_binary and scan.file_info is not None
    ]

    if not text_scans:
        lines.extend(["No changed text file contents to include.", ""])
        return

    for scan in text_scans:
        lines.extend(
            [
                f"## {scan.path}",
                "",
                f"- Status: {scan.status}",
                f"- Language: {_language_for(scan)}",
                f"- Lines: {_line_count_for(scan)}",
                f"- Estimated tokens: {_token_estimate_for(scan)}",
                "",
                "```text",
                _read_changed_file_content(repo_path, scan).rstrip(),
                "```",
                "",
            ]
        )


def _append_deleted_files(lines: list[str], scans: Sequence[ChangedFileScan]) -> None:
    deleted_scans = [scan for scan in scans if scan.is_deleted]

    lines.extend(["# Deleted Files", ""])

    if not deleted_scans:
        lines.extend(["No deleted files.", ""])
        return

    for scan in deleted_scans:
        lines.append(f"- `{scan.path}`")

    lines.append("")


def _append_binary_or_skipped_files(lines: list[str], scans: Sequence[ChangedFileScan]) -> None:
    skipped_scans = [
        scan
        for scan in scans
        if scan.is_binary or (not scan.is_deleted and scan.file_info is None)
    ]

    lines.extend(["# Binary / Skipped Files", ""])

    if not skipped_scans:
        lines.extend(["No binary or skipped files.", ""])
        return

    for scan in skipped_scans:
        if scan.is_binary:
            reason = "binary"
        else:
            reason = "not available for scanning"
        lines.append(f"- `{scan.path}` ({reason})")

    lines.append("")


def render_changed_export(
    repo_path: str | Path = ".",
    *,
    scans: Sequence[ChangedFileScan] | None = None,
    compare_mode: str = "Working tree",
) -> str:
    """Render the changed export as text."""

    repo = Path(repo_path)
    changed_scans = list(scans) if scans is not None else collect_changed_file_scans(repo)

    lines: list[str] = [
        "# Changed Export",
        "",
        f"Repository: {repo.resolve()}",
        f"Compare Mode: {compare_mode}",
        "",
    ]

    _append_summary(lines, changed_scans)
    _append_file_overview(lines, changed_scans)
    _append_changed_file_contents(lines, repo, changed_scans)
    _append_deleted_files(lines, changed_scans)
    _append_binary_or_skipped_files(lines, changed_scans)

    return "\n".join(lines).rstrip() + "\n"


def write_changed_export(
    repo_path: str | Path = ".",
    output_path: str | Path = "changed.txt",
    *,
    scans: Sequence[ChangedFileScan] | None = None,
    compare_mode: str = "Working tree",
) -> Path:
    """Write changed.txt and return the output path."""

    output = Path(output_path)
    output.write_text(
        render_changed_export(repo_path, scans=scans, compare_mode=compare_mode),
        encoding="utf-8",
    )
    return output
