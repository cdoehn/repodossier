#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_patch_metadata import parse_metadata_lines, validate_records


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
    args = parser.parse_args(argv)

    script_path = args.script.expanduser().resolve()
    repo_root = args.repo.expanduser().resolve()

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
