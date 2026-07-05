from __future__ import annotations
from repodossier.languages import code_fence_language as _shared_code_fence_language

from repodossier.secrets import SecretFinding, mask_secrets_in_text

from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from repodossier.changed import ChangedFileScan, collect_changed_file_scans
from repodossier.git import get_diff, get_diff_against_branch
from repodossier.config import apply_config_to_file_infos, filter_changed_export_sections, format_limit_notice, get_active_config, is_file_size_allowed, truncate_text_by_line_limit





CHANGED_EXPORT_DOCUMENT_HEADING = "# Changed Export"

CHANGED_EXPORT_SECTION_ORDER: tuple[str, ...] = (
    "changed_files_summary",
    "changed_files",
    "git_diff",
    "changed_file_contents",
    "deleted_files",
    "binary_or_skipped_files",
)

CHANGED_EXPORT_SECTION_HEADINGS: dict[str, str] = {
    "changed_files_summary": "# Changed Files Summary",
    "changed_files": "# Changed Files",
    "git_diff": "# Git Diff",
    "changed_file_contents": "# Changed File Contents",
    "deleted_files": "# Deleted Files",
    "binary_or_skipped_files": "# Binary / Skipped Files",
}


def iter_changed_export_headings() -> tuple[str, ...]:
    """Return changed export headings in stable render order."""

    return (
        CHANGED_EXPORT_DOCUMENT_HEADING,
        *(
            CHANGED_EXPORT_SECTION_HEADINGS[section_name]
            for section_name in CHANGED_EXPORT_SECTION_ORDER
        ),
    )


def _repodossier_export_safety_root() -> object:
    """Return the nearest Git repository root or current directory."""

    from pathlib import Path

    current = Path.cwd()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate

    return current


def _repodossier_mask_known_export_files() -> None:
    """Apply final secret masking to known generated export files."""

    from pathlib import Path

    from repodossier.secrets import mask_export_file

    root = Path(_repodossier_export_safety_root())

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
            CHANGED_EXPORT_SECTION_HEADINGS["changed_files_summary"],
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
    lines.extend([CHANGED_EXPORT_SECTION_HEADINGS["changed_files"], ""])

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
    lines.extend([CHANGED_EXPORT_SECTION_HEADINGS["git_diff"], ""])

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


def _changed_code_fence_language(scan: ChangedFileScan) -> str:
    """Return a Markdown code fence language for changed file contents."""

    return _shared_code_fence_language(_language_for(scan))


def _append_changed_file_contents(
    lines: list[str],
    repo_path: Path,
    scans: Sequence[ChangedFileScan],
) -> None:
    lines.extend([CHANGED_EXPORT_SECTION_HEADINGS["changed_file_contents"], ""])

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
                "`" * 3 + _changed_code_fence_language(scan),
                _read_changed_file_content(repo_path, scan).rstrip(),
                "`" * 3,
                "",
            ]
        )


def _append_deleted_files(lines: list[str], scans: Sequence[ChangedFileScan]) -> None:
    deleted_scans = [scan for scan in scans if scan.is_deleted]

    lines.extend([CHANGED_EXPORT_SECTION_HEADINGS["deleted_files"], ""])

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

    lines.extend([CHANGED_EXPORT_SECTION_HEADINGS["binary_or_skipped_files"], ""])

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
        CHANGED_EXPORT_DOCUMENT_HEADING,
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
    return _append_bash_call_graph_section_to_export(
        _append_changed_secret_detection_section(masked_text, secret_section),
        locals(),
    )
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
        _repodossier_mask_known_export_files()


_REPODOSSIER_CHANGED_EXPORT_LIMITS_WRAPPER = True


def _apply_changed_scan_selection_limits(
    scans: Sequence[ChangedFileScan],
) -> tuple[ChangedFileScan, ...]:
    """Apply configured changed-file selection limits before rendering."""

    config = get_active_config()
    selection = apply_config_to_file_infos(tuple(scans), config)
    return tuple(selection.files)


_REPODOSSIER_ORIGINAL_COLLECT_CHANGED_FILE_SCANS_FOR_LIMITS = collect_changed_file_scans


def collect_changed_file_scans(*args: object, **kwargs: object) -> list[ChangedFileScan]:
    """Collect changed scans and apply configured file-selection limits."""

    scans = _REPODOSSIER_ORIGINAL_COLLECT_CHANGED_FILE_SCANS_FOR_LIMITS(
        *args,
        **kwargs,
    )
    return list(_apply_changed_scan_selection_limits(tuple(scans)))


def _changed_limit_notice(reason: str, *, omitted_count: int | None = None) -> str:
    return format_limit_notice(reason, omitted_count=omitted_count) + "\n"


def _changed_scan_file_info(scan: object | None) -> object | None:
    if scan is None:
        return None
    return getattr(scan, "file_info", None)


def _changed_file_size_bytes(scan: object | None, content: str) -> int:
    file_info = _changed_scan_file_info(scan)
    size_bytes = getattr(file_info, "size_bytes", None)
    if size_bytes is not None:
        return int(size_bytes)
    return len(content.encode("utf-8"))


def _apply_changed_content_limits(content: str, scan: object | None) -> str:
    """Apply configured per-file content limits to changed file contents."""

    config = get_active_config()

    if not is_file_size_allowed(_changed_file_size_bytes(scan, content), config):
        return _changed_limit_notice("limits.max_file_bytes was reached")

    limited_content, truncated, omitted_lines = truncate_text_by_line_limit(
        content,
        config,
    )
    if not truncated:
        return limited_content

    if limited_content and not limited_content.endswith("\n"):
        limited_content += "\n"

    return limited_content + _changed_limit_notice(
        "limits.max_line_count was reached",
        omitted_count=omitted_lines,
    )


_REPODOSSIER_ORIGINAL_READ_CHANGED_FILE_CONTENT_FOR_LIMITS = _read_changed_file_content


def _read_changed_file_content(*args: object, **kwargs: object) -> str:
    """Read changed file content and apply configured per-file limits."""

    content = _REPODOSSIER_ORIGINAL_READ_CHANGED_FILE_CONTENT_FOR_LIMITS(
        *args,
        **kwargs,
    )

    scan = kwargs.get("scan")
    if scan is None and len(args) >= 2:
        scan = args[1]

    return _apply_changed_content_limits(content, scan)


def _apply_changed_max_export_bytes_limit(rendered: str) -> str:
    """Apply the global max_export_bytes limit to a rendered changed export."""

    limit = get_active_config().limits.max_export_bytes
    if limit is None:
        return rendered

    rendered_bytes = rendered.encode("utf-8")
    if len(rendered_bytes) <= limit:
        return rendered

    notice = "\n\n" + format_limit_notice("limits.max_export_bytes was reached") + "\n"
    notice_bytes = notice.encode("utf-8")

    if len(notice_bytes) >= limit:
        return notice_bytes[:limit].decode("utf-8", errors="ignore")

    available_bytes = limit - len(notice_bytes)
    truncated = rendered_bytes[:available_bytes].decode("utf-8", errors="ignore").rstrip()
    return truncated + notice


_REPODOSSIER_ORIGINAL_RENDER_CHANGED_EXPORT_FOR_LIMITS = render_changed_export


def render_changed_export(*args: object, **kwargs: object) -> str:
    """Render changed.txt while applying active changed export limits."""

    if kwargs.get("scans") is not None:
        kwargs = dict(kwargs)
        kwargs["scans"] = _apply_changed_scan_selection_limits(kwargs["scans"])

    rendered = _REPODOSSIER_ORIGINAL_RENDER_CHANGED_EXPORT_FOR_LIMITS(
        *args,
        **kwargs,
    )
    return _apply_changed_max_export_bytes_limit(rendered)


def _append_bash_call_graph_section_to_export(export_text: object, context: dict[str, object]) -> object:
    """Append Bash call graph information to text exports when shell files are present."""

    if not isinstance(export_text, str):
        return export_text

    if "Bash Call Graph" in export_text:
        return export_text

    bash_files = _collect_bash_call_graph_files_from_export_context(context)
    if not bash_files:
        return export_text

    from .bash_call_graph import discover_bash_call_graph_for_files

    edges = discover_bash_call_graph_for_files(bash_files)
    if not edges:
        return export_text

    lines = ["## Bash Call Graph", ""]

    for edge in edges:
        caller = _format_bash_call_endpoint(edge.caller_path, edge.caller)
        callee = _format_bash_call_endpoint(edge.callee_path, edge.callee)
        lines.append(f"- {caller} -> {callee}")

    return export_text.rstrip() + "\n\n" + "\n".join(lines) + "\n"


def _format_bash_call_endpoint(path: object, name: str) -> str:
    if path:
        return f"{path}:{name}"

    return name


def _collect_bash_call_graph_files_from_export_context(context: dict[str, object]) -> dict[str, str]:
    collected: dict[str, str] = {}
    seen: set[int] = set()

    for value in context.values():
        _collect_bash_call_graph_files_from_value(value, collected, seen, depth=0)

    return collected


def _collect_bash_call_graph_files_from_value(
    value: object,
    collected: dict[str, str],
    seen: set[int],
    depth: int,
) -> None:
    if depth > 5:
        return

    if value is None:
        return

    if isinstance(value, (str, bytes, int, float, bool)):
        return

    value_id = id(value)
    if value_id in seen:
        return
    seen.add(value_id)

    path_text, content = _bash_call_graph_path_and_content_from_object(value)
    if path_text is not None and content is not None and _is_bash_call_graph_source(path_text, content):
        collected.setdefault(path_text, content)
        return

    if isinstance(value, dict):
        path_text, content = _bash_call_graph_path_and_content_from_mapping(value)
        if path_text is not None and content is not None and _is_bash_call_graph_source(path_text, content):
            collected.setdefault(path_text, content)

        for key, item in value.items():
            if isinstance(key, (str, bytes)) and isinstance(item, (str, bytes)):
                key_text = key.decode("utf-8", errors="ignore") if isinstance(key, bytes) else key
                item_text = item.decode("utf-8", errors="ignore") if isinstance(item, bytes) else item
                if _is_bash_call_graph_source(key_text, item_text):
                    collected.setdefault(key_text, item_text)
                    continue

            _collect_bash_call_graph_files_from_value(item, collected, seen, depth + 1)

        return

    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            _collect_bash_call_graph_files_from_value(item, collected, seen, depth + 1)

        return

    if hasattr(value, "__dict__"):
        for item in vars(value).values():
            _collect_bash_call_graph_files_from_value(item, collected, seen, depth + 1)


def _bash_call_graph_path_and_content_from_mapping(mapping: dict[object, object]) -> tuple[str | None, str | None]:
    path_value = None
    content_value = None

    for key, value in mapping.items():
        key_text = str(key).lower()

        if path_value is None and key_text in {
            "path",
            "file",
            "filepath",
            "file_path",
            "relative_path",
            "source_path",
        }:
            path_value = value

        if content_value is None and key_text in {
            "content",
            "text",
            "source",
            "source_text",
            "raw_text",
            "body",
        }:
            content_value = value

    return _normalize_bash_call_graph_path_and_content(path_value, content_value)


def _bash_call_graph_path_and_content_from_object(value: object) -> tuple[str | None, str | None]:
    path_value = None
    content_value = None

    for attr in ("path", "file", "filepath", "file_path", "relative_path", "source_path"):
        if hasattr(value, attr):
            path_value = getattr(value, attr)
            break

    for attr in ("content", "text", "source", "source_text", "raw_text", "body"):
        if hasattr(value, attr):
            content_value = getattr(value, attr)
            break

    if content_value is None and isinstance(path_value, (str, bytes)):
        path_text = path_value.decode("utf-8", errors="ignore") if isinstance(path_value, bytes) else path_value
        path_obj = Path(path_text)
        if path_obj.is_file() and _is_bash_call_graph_source(str(path_obj), ""):
            try:
                content_value = path_obj.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                content_value = None

    if content_value is None and isinstance(value, Path) and value.is_file():
        path_value = value
        if _is_bash_call_graph_source(str(value), ""):
            try:
                content_value = value.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                content_value = None

    return _normalize_bash_call_graph_path_and_content(path_value, content_value)


def _normalize_bash_call_graph_path_and_content(
    path_value: object,
    content_value: object,
) -> tuple[str | None, str | None]:
    if path_value is None or content_value is None:
        return None, None

    if isinstance(path_value, bytes):
        path_text = path_value.decode("utf-8", errors="ignore")
    else:
        path_text = str(path_value)

    if isinstance(content_value, bytes):
        content = content_value.decode("utf-8", errors="ignore")
    else:
        content = str(content_value)

    return path_text, content


def _is_bash_call_graph_source(path: str, content: str | bytes | None = None) -> bool:
    lowered = path.lower()
    if lowered.endswith((".sh", ".bash")):
        return True

    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    if not content:
        return False

    lines = content.splitlines()
    if not lines:
        return False

    first_line = lines[0].strip()
    if not first_line.startswith("#!"):
        return False

    parts = first_line[2:].strip().lower().replace("\t", " ").split()
    if not parts:
        return False

    executable = parts[0].rsplit("/", 1)[-1]
    if executable in {"bash", "sh"}:
        return True

    if executable == "env":
        for part in parts[1:]:
            if part.startswith("-"):
                continue
            if part.rsplit("/", 1)[-1] in {"bash", "sh"}:
                return True

    return False


def render_changed_export_from_model(export: "RepositoryExport") -> str:
    """Render changed Markdown from a RepositoryExport model.

    This bridge is intentionally model-only. It does not scan files, inspect Git,
    or run analyzers. Legacy changed-export functions stay unchanged while
    callers can opt into the model-rendered Markdown path explicitly.
    """

    from repodossier.renderers import render_changed_markdown

    return render_changed_markdown(export)

