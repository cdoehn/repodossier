from __future__ import annotations
from repocontext.secrets import SecretFinding, mask_secrets_in_text

from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from repocontext.changed import ChangedFileScan, collect_changed_file_scans
from repocontext.git import get_diff, get_diff_against_branch
from repocontext.config import filter_changed_export_sections, get_active_config





def _repocontext_export_safety_root() -> object:
    """Return the nearest Git repository root or current directory."""

    from pathlib import Path

    current = Path.cwd()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate

    return current


def _repocontext_mask_known_export_files() -> None:
    """Apply final secret masking to known generated export files."""

    from pathlib import Path

    from repocontext.secrets import mask_export_file

    root = Path(_repocontext_export_safety_root())

    targets = [
        (
            "full.txt",
            "Potential secrets were masked before full export was written.",
        ),
        (
            "ai.txt",
            "Potential secrets were masked before AI export was written.",
        ),
        (
            "docs.txt",
            "Potential secrets were masked before documentation export was written.",
        ),
        (
            "changed.txt",
            "Potential secrets masked in changed export.",
        ),
    ]

    for filename, summary in targets:
        mask_export_file(root / filename, filename, summary)
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


def _append_git_diff(
    lines: list[str],
    repo_path: Path,
    scans: Sequence[ChangedFileScan],
    *,
    branch: str | None = None,
) -> None:
    lines.extend(["# Git Diff", ""])

    diffable_scans = [
        scan
        for scan in scans
        if not scan.is_deleted and not scan.is_binary
    ]

    if not diffable_scans:
        lines.extend(["No git diff available.", ""])
        return

    for scan in diffable_scans:
        if branch:
            diff_text = get_diff_against_branch(repo_path, branch, scan.path)
        else:
            diff_text = get_diff(repo_path, scan.path)

        lines.extend(
            [
                f"## {scan.path}",
                "",
                f"- Status: {scan.status}",
                "",
            ]
        )

        if diff_text.strip():
            lines.extend(["```diff", diff_text.rstrip(), "```", ""])
        else:
            lines.extend(["No git diff available for this file.", ""])


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


def _render_changed_export_unmasked(
    repo_path: str | Path = ".",
    *,
    scans: Sequence[ChangedFileScan] | None = None,
    compare_mode: str | None = None,
    include_diff: bool = True,
    branch: str | None = None,
) -> str:
    """Render the changed export as text."""

    repo = Path(repo_path)
    if compare_mode is None:
        compare_mode = f"Against branch: {branch}" if branch else "Working tree"
    changed_scans = (
        list(scans)
        if scans is not None
        else collect_changed_file_scans(repo, branch=branch)
    )

    lines: list[str] = [
        "# Changed Export",
        "",
        f"Repository: {repo.resolve()}",
        f"Compare Mode: {compare_mode}",
        "",
    ]

    _append_summary(lines, changed_scans)
    _append_file_overview(lines, changed_scans)

    if include_diff:
        _append_git_diff(lines, repo, changed_scans, branch=branch)

    _append_changed_file_contents(lines, repo, changed_scans)
    _append_deleted_files(lines, changed_scans)
    _append_binary_or_skipped_files(lines, changed_scans)

    return "\n".join(lines).rstrip() + "\n"





def _format_changed_secret_detection_section(findings: list[SecretFinding]) -> str:
    """Format a compact changed export secret detection summary."""

    if not findings:
        return ""

    counts_by_type: dict[str, int] = {}
    for finding in findings:
        counts_by_type[finding.secret_type] = counts_by_type.get(finding.secret_type, 0) + 1

    lines = [
        "# Secret Detection",
        "",
        f"Potential secrets masked in changed export: {len(findings)}",
        "",
        "Findings by type:",
    ]

    for secret_type in sorted(counts_by_type):
        lines.append(f"- {secret_type}: {counts_by_type[secret_type]}")

    return "\n".join(lines)


def _append_changed_secret_detection_section(text: str, section: str) -> str:
    """Append the changed export secret detection section when needed."""

    if not section:
        return text

    return f"{text.rstrip()}\n\n{section}\n"


def render_changed_export(*args: object, **kwargs: object) -> str:
    """Render changed export content with potential secrets masked."""

    rendered = _render_changed_export_unmasked(*args, **kwargs)
    masked_text, findings = mask_secrets_in_text(rendered, "changed.txt")
    secret_section = _format_changed_secret_detection_section(findings)
    return _append_changed_secret_detection_section(masked_text, secret_section)
def _write_changed_export_without_export_secret_safety_net(
    repo_path: str | Path = ".",
    output_path: str | Path = "changed.txt",
    *,
    scans: Sequence[ChangedFileScan] | None = None,
    compare_mode: str | None = None,
    include_diff: bool = True,
    branch: str | None = None,
) -> Path:
    """Write changed.txt and return the output path."""

    output = Path(output_path)
    rendered_export = render_changed_export(
        repo_path,
        scans=scans,
        compare_mode=compare_mode,
        include_diff=include_diff,
        branch=branch,
    )
    rendered_export = filter_changed_export_sections(
        rendered_export,
        get_active_config(),
    )
    output.write_text(rendered_export, encoding="utf-8")
    return output


def write_changed_export(*args: object, **kwargs: object) -> object:
    """Run write_changed_export and apply final export secret masking."""

    try:
        return _write_changed_export_without_export_secret_safety_net(*args, **kwargs)
    finally:
        _repocontext_mask_known_export_files()

