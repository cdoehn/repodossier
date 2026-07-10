#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

META_PREFIX = "# repodossier-meta:"
ALLOWED_META_TYPES = {"patch", "progress", "display"}
ALLOWED_PATCH_FIELDS = {"type", "id", "title", "commit", "fix_for", "requires_direct_bash"}
ALLOWED_PROGRESS_FIELDS = {"type", "panel", "status", "file", "start", "end", "anchor", "label"}
ALLOWED_DISPLAY_FIELDS = {"type", "context", "layout", "frame", "progress_context"}
ALLOWED_PANELS = {"roadmap", "milestone"}
ALLOWED_STATUSES = {"done", "active", "partial", "todo"}
ALLOWED_LAYOUTS = {"side-by-side", "stacked"}

@dataclass(frozen=True)
class MetaRecord:
    line_number: int
    data: dict[str, Any]

def _meta_error(line_number: int | None, message: str) -> str:
    return message if line_number is None else f"line {line_number}: {message}"

def parse_metadata_lines(script_path: Path) -> tuple[list[MetaRecord], list[str]]:
    records: list[MetaRecord] = []
    errors: list[str] = []
    try:
        lines = script_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        return [], [f"cannot read script as UTF-8: {exc}"]

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith(META_PREFIX):
            continue
        payload = stripped[len(META_PREFIX):].strip()
        if not payload:
            errors.append(_meta_error(line_number, "empty repodossier-meta payload"))
            continue
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            errors.append(_meta_error(line_number, f"invalid JSON: {exc.msg}"))
            continue
        if not isinstance(decoded, dict):
            errors.append(_meta_error(line_number, "metadata payload must be a JSON object"))
            continue
        records.append(MetaRecord(line_number=line_number, data=decoded))
    return records, errors

def _require_string(record: MetaRecord, errors: list[str], key: str) -> None:
    value = record.data.get(key)
    if not isinstance(value, str):
        errors.append(_meta_error(record.line_number, f'missing or invalid string field "{key}"'))
    elif not value.strip():
        errors.append(_meta_error(record.line_number, f'field "{key}" must not be empty'))

def _require_bool(record: MetaRecord, errors: list[str], key: str) -> None:
    if key in record.data and not isinstance(record.data[key], bool):
        errors.append(_meta_error(record.line_number, f'field "{key}" must be a boolean'))

def _require_int(record: MetaRecord, errors: list[str], key: str, *, minimum: int = 1) -> None:
    value = record.data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(_meta_error(record.line_number, f'missing or invalid integer field "{key}"'))
    elif value < minimum:
        errors.append(_meta_error(record.line_number, f'field "{key}" must be >= {minimum}'))

def validate_records(
    records: list[MetaRecord],
    *,
    script_path: Path,
    repo_root: Path,
    require_metadata: bool = True,
) -> list[str]:
    del script_path
    errors: list[str] = []
    if not records:
        if require_metadata:
            errors.append("missing required repodossier-meta block")
        return errors

    patch_records = [record for record in records if record.data.get("type") == "patch"]
    progress_records = [record for record in records if record.data.get("type") == "progress"]
    display_records = [record for record in records if record.data.get("type") == "display"]

    if len(patch_records) != 1:
        errors.append(f"expected exactly one patch metadata record, found {len(patch_records)}")
    if len(display_records) > 1:
        errors.append(f"expected at most one display metadata record, found {len(display_records)}")

    requires_direct_bash = any(record.data.get("requires_direct_bash") is True for record in patch_records)
    display_progress_context_disabled = any(record.data.get("progress_context") is False for record in display_records)
    if display_progress_context_disabled and progress_records:
        errors.append("display progress_context=false must not be combined with progress metadata records")
    if patch_records and not requires_direct_bash and not display_progress_context_disabled:
        panels = {record.data.get("panel") for record in progress_records if isinstance(record.data.get("panel"), str)}
        if "roadmap" not in panels:
            errors.append("missing required roadmap progress metadata record")
        if "milestone" not in panels:
            errors.append("missing required milestone progress metadata record")

    for record in records:
        meta_type = record.data.get("type")
        if not isinstance(meta_type, str):
            errors.append(_meta_error(record.line_number, 'missing or invalid string field "type"'))
            continue
        if meta_type not in ALLOWED_META_TYPES:
            errors.append(_meta_error(record.line_number, f"type must be one of {sorted(ALLOWED_META_TYPES)}, got {meta_type!r}"))
            continue
        if meta_type == "patch":
            for key in sorted(set(record.data) - ALLOWED_PATCH_FIELDS):
                errors.append(_meta_error(record.line_number, f'unknown field "{key}"'))
            for key in ("id", "title", "commit"):
                _require_string(record, errors, key)
            if "fix_for" in record.data:
                _require_string(record, errors, "fix_for")
            _require_bool(record, errors, "requires_direct_bash")
        elif meta_type == "progress":
            for key in sorted(set(record.data) - ALLOWED_PROGRESS_FIELDS):
                errors.append(_meta_error(record.line_number, f'unknown field "{key}"'))
            for key in ("panel", "status", "file"):
                _require_string(record, errors, key)
            has_start = "start" in record.data
            has_end = "end" in record.data
            has_anchor = "anchor" in record.data
            if has_start != has_end:
                errors.append(_meta_error(record.line_number, '"start" and "end" must be provided together'))
            if not has_anchor and not (has_start and has_end):
                errors.append(_meta_error(record.line_number, 'progress metadata must provide either "start"/"end" or "anchor"'))
            if has_start:
                _require_int(record, errors, "start")
            if has_end:
                _require_int(record, errors, "end")
            if has_anchor:
                _require_string(record, errors, "anchor")
            panel = record.data.get("panel")
            status = record.data.get("status")
            rel_file = record.data.get("file")
            if isinstance(panel, str) and panel not in ALLOWED_PANELS:
                errors.append(_meta_error(record.line_number, f"panel must be one of {sorted(ALLOWED_PANELS)}"))
            if isinstance(status, str) and status not in ALLOWED_STATUSES:
                errors.append(_meta_error(record.line_number, f"status must be one of {sorted(ALLOWED_STATUSES)}"))
            if isinstance(rel_file, str):
                rel_path = Path(rel_file)
                if rel_path.is_absolute() or "." in rel_path.parts:
                    errors.append(_meta_error(record.line_number, "file must be a safe repo-relative path"))
                elif not (repo_root / rel_file).exists():
                    errors.append(_meta_error(record.line_number, f"file does not exist: {rel_file}"))
        elif meta_type == "display":
            for key in sorted(set(record.data) - ALLOWED_DISPLAY_FIELDS):
                errors.append(_meta_error(record.line_number, f'unknown field "{key}"'))
            if "context" in record.data:
                _require_int(record, errors, "context", minimum=0)
                context = record.data.get("context")
                if isinstance(context, int) and context > 50:
                    errors.append(_meta_error(record.line_number, 'field "context" must be <= 50'))
            if "layout" in record.data:
                _require_string(record, errors, "layout")
                layout = record.data.get("layout")
                if isinstance(layout, str) and layout not in ALLOWED_LAYOUTS:
                    errors.append(_meta_error(record.line_number, f"layout must be one of {sorted(ALLOWED_LAYOUTS)}"))
            if "frame" in record.data and not isinstance(record.data["frame"], bool):
                errors.append(_meta_error(record.line_number, 'field "frame" must be a boolean'))
            if "progress_context" in record.data and not isinstance(record.data["progress_context"], bool):
                errors.append(_meta_error(record.line_number, 'field "progress_context" must be a boolean'))
    return errors

@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    line_number: int | None = None

    def render(self) -> str:
        location = f"line {self.line_number}: " if self.line_number is not None else ""
        return f"{self.code}: {location}{self.message}"

FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "no-bundle-project",
        re.compile(r"(^|[^\w.-])bundle_project\.sh([^\w.-]|$)"),
        "do not use bundle_project.sh; use RepoDossier exports instead",
    ),
    (
        "no-global-tee-log",
        re.compile(r"exec\s+>\s*>\s*\(\s*tee\b"),
        "patchscripts must not install their own global tee logging; c owns logging",
    ),
    (
        "no-clipboard",
        re.compile(r"\b(xclip|xsel|wl-copy)\b"),
        "patchscripts must not manage clipboard output; c/logfiles own diagnostics",
    ),
    (
        "no-aider",
        re.compile(r"\baider\b", re.IGNORECASE),
        "do not use aider in direct patch scripts unless explicitly requested",
    ),
]

HEREDOC_START = re.compile(
    r"<<-?\s*(?P<quote>['\"]?)(?P<tag>[A-Za-z_][A-Za-z0-9_]*)['\"]?"
)

def _line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1

def _shell_lines_outside_heredocs(lines: list[str]) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    heredoc_tag: str | None = None

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        if heredoc_tag is not None:
            if stripped == heredoc_tag:
                heredoc_tag = None
            continue

        result.append((line_number, line))

        match = HEREDOC_START.search(line)
        if match:
            heredoc_tag = match.group("tag")

    return result

def _strip_shell_quoted_text(line: str) -> str:
    # Remove simple quoted shell text before command-oriented checks.
    #
    # The linter should flag real patch commands, not diagnostic strings such as
    # echo "git diff --cached --quiet". This intentionally stays conservative:
    # commands embedded in quoted strings are treated as text.
    return re.sub(r"'[^']*'|\"(?:\\.|[^\"])*\"", "", line)

def _iter_pattern_findings(shell_lines: list[tuple[int, str]]) -> list[Finding]:
    findings: list[Finding] = []

    for code, pattern, message in FORBIDDEN_PATTERNS:
        for line_number, line in shell_lines:
            command_line = _strip_shell_quoted_text(line)
            if pattern.search(command_line):
                findings.append(
                    Finding(
                        code=code,
                        message=message,
                        line_number=line_number,
                    )
                )

    return findings

def _git_pager_findings(shell_lines: list[tuple[int, str]]) -> list[Finding]:
    findings: list[Finding] = []

    unsafe = re.compile(r"(?<![-\w])git\s+(diff|log|show)\b")
    safe = re.compile(
        r"git\s+--no-pager\s+(diff|log|show)\b|"
        r"GIT_PAGER=cat\s+git\s+(diff|log|show)\b"
    )

    for line_number, line in shell_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        command_line = _strip_shell_quoted_text(line)

        # `git diff --quiet` is an exit-code check and produces no diff output,
        # so it cannot open a pager. This is commonly used for commit guards:
        # `git diff --cached --quiet`.
        if re.search(r"(?<![-\w])git\s+diff\b", command_line) and "--quiet" in command_line:
            continue

        if unsafe.search(command_line) and not safe.search(command_line):
            findings.append(
                Finding(
                    code="git-no-pager",
                    message="use git --no-pager or GIT_PAGER=cat for diff/log/show commands",
                    line_number=line_number,
                )
            )

    return findings

def _missing_footer_findings(text: str) -> list[Finding]:
    if "print_footer" in text:
        return []
    return [
        Finding(
            code="missing-footer",
            message="patchscript should include a print_footer function for success and failure summaries",
        )
    ]

def _missing_tests_findings(text: str) -> list[Finding]:
    test_markers = [
        "pytest",
        "py_compile",
        "compileall",
        "bash -n",
    ]
    if any(marker in text for marker in test_markers):
        return []
    return [
        Finding(
            code="missing-checks",
            message="patchscript should run focused tests or at least syntax/smoke checks",
        )
    ]

def _triple_backtick_findings(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(r"`{3}", text):
        findings.append(
            Finding(
                code="literal-triple-backtick",
                message="avoid literal triple-backticks in generated patch heredocs; use chr(96) * 3 or tilde fences",
                line_number=_line_number_for_offset(text, match.start()),
            )
        )
    return findings

def lint_patch_script(script_path: Path, repo_root: Path) -> list[Finding]:
    try:
        text = script_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [Finding(code="utf8", message=f"script must be UTF-8 readable: {exc}")]

    records, parse_errors = parse_metadata_lines(script_path)
    validation_errors = validate_records(
        records,
        script_path=script_path,
        repo_root=repo_root,
        require_metadata=True,
    )

    findings = [
        Finding(code="metadata", message=error)
        for error in parse_errors + validation_errors
    ]

    lines = text.splitlines()
    shell_lines = _shell_lines_outside_heredocs(lines)

    findings.extend(_iter_pattern_findings(shell_lines))
    findings.extend(_git_pager_findings(shell_lines))
    findings.extend(_missing_footer_findings(text))
    findings.extend(_missing_tests_findings(text))
    findings.extend(_triple_backtick_findings(text))

    return findings

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preflight-lint RepoDossier download patch scripts.")
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--repo", default=Path.cwd(), type=Path)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args(argv)

    script_path = args.script.expanduser().resolve()
    repo_root = args.repo.expanduser().resolve()

    if args.metadata_only:
        records, parse_errors = parse_metadata_lines(script_path)
        validation_errors = validate_records(
            records,
            script_path=script_path,
            repo_root=repo_root,
            require_metadata=True,
        )
        errors = parse_errors + validation_errors
        if errors:
            if not args.quiet:
                print("Metadata invalid:")
                for item in errors:
                    print(f"  - {item}")
            return 10
        if not args.quiet:
            print("Metadata OK")
        return 0

    findings = lint_patch_script(script_path, repo_root)

    if findings:
        if not args.quiet:
            print("Patch preflight failed:")
            for finding in findings:
                print(f"  - {finding.render()}")
        return 20

    if not args.quiet:
        print("Patch preflight OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
