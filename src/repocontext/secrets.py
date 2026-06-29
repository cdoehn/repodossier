"""Secret detection models, scanning helpers, and masking utilities.

This module contains the shared secret-detection core used by the export
pipeline. It intentionally focuses on conservative assignment-based detection
for common variable names and avoids exposing secret values in summaries.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from re import Match, Pattern
from typing import TypeAlias


SecretGroup: TypeAlias = str | int | None

_REDACTION_MARKER = "***REDACTED***"

_PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change-me",
    "example",
    "example-token",
    "your-api-key",
    "your_api_key",
    "insert-key-here",
    "todo",
    "none",
    "null",
    "dummy",
    "test",
    "password",
    "secret",
}

_NON_SECRET_LITERALS = {
    "true",
    "false",
    "yes",
    "no",
    "on",
    "off",
    "none",
    "null",
}

_NUMERIC_RE = re.compile(r"^[+-]?(?:\d+|\d+\.\d+)$")


@dataclass(frozen=True)
class SecretFinding:
    """A potential secret found in a repository file."""

    file_path: str
    line_number: int
    secret_type: str
    matched_text: str
    masked_text: str
    variable_name: str | None
    confidence: str

    @property
    def has_secret(self) -> bool:
        """Return whether this finding represents a non-empty matched value."""

        return bool(self.matched_text)

    @property
    def summary_line(self) -> str:
        """Return a safe one-line summary without exposing the secret value."""

        variable = f" {self.variable_name}" if self.variable_name else ""
        return (
            f"{self.file_path}:{self.line_number}: "
            f"{self.secret_type}{variable} ({self.confidence})"
        )


@dataclass(frozen=True)
class SecretPattern:
    """Compiled pattern metadata for a class of potential secrets."""

    name: str
    regex: Pattern[str]
    secret_type: str
    confidence: str
    value_group: SecretGroup = "value"


def _assignment_pattern(variable_pattern: str) -> Pattern[str]:
    """Build a conservative assignment pattern for secret-like variables.

    Exports may add line numbers, markdown text, or diff markers before the
    original source line. Therefore the pattern allows non-secret context before
    the assignment while still requiring a clear variable assignment.
    """

    return re.compile(
        rf"""
        ^
        (?P<context_prefix>.*?)
        (?P<diff_prefix>[+-])?
        (?P<prefix>
            \s*
            (?:export\s+)?
            (?:
                os\.environ\[\s*['"](?P<env_name>{variable_pattern})['"]\s*\]
                |
                (?P<name>{variable_pattern})
            )
            \s*(?:=|:)\s*
        )
        (?:
            (?P<quote>['"])(?P<quoted_value>.*?)(?P=quote)
            |
            (?P<unquoted_value>[^\#\n]+?)
        )
        (?P<suffix>\s*(?:\#.*)?$)
        """,
        re.VERBOSE | re.IGNORECASE,
    )

def default_secret_patterns() -> list[SecretPattern]:
    """Return the built-in secret pattern registry."""

    return [
        SecretPattern(
            name="api_key_assignment",
            regex=_assignment_pattern(r"[A-Z0-9_]*API[_-]?KEY|apiKey"),
            secret_type="API_KEY",
            confidence="high",
            value_group="value",
        ),
        SecretPattern(
            name="token_assignment",
            regex=_assignment_pattern(r"[A-Z0-9_]*TOKEN"),
            secret_type="TOKEN",
            confidence="high",
            value_group="value",
        ),
        SecretPattern(
            name="secret_assignment",
            regex=_assignment_pattern(r"[A-Z0-9_]*SECRET"),
            secret_type="SECRET",
            confidence="high",
            value_group="value",
        ),
        SecretPattern(
            name="password_assignment",
            regex=_assignment_pattern(r"[A-Z0-9_]*(?:PASSWORD|PASSWD|PWD)"),
            secret_type="PASSWORD",
            confidence="high",
            value_group="value",
        ),
    ]


def mask_secret_value(value: str) -> str:
    """Mask a secret value while preserving a small amount of context."""

    if value == "":
        return ""

    if len(value) <= 8:
        return _REDACTION_MARKER

    prefix = value[:4]
    suffix = value[-4:]
    return f"{prefix}{_REDACTION_MARKER}{suffix}"


def mask_secret_in_line(line: str, secret_value: str) -> str:
    """Return line with the first occurrence of secret_value masked."""

    if not secret_value:
        return line

    masked_value = mask_secret_value(secret_value)
    return line.replace(secret_value, masked_value, 1)


def is_placeholder_secret(value: str) -> bool:
    """Return whether value is an obvious placeholder or example secret."""

    normalized = value.strip().strip("'\"").lower()
    return normalized in _PLACEHOLDER_VALUES


def is_probably_secret_value(value: str) -> bool:
    """Return whether value looks sensitive enough to report as a secret."""

    normalized = value.strip().strip("'\"")
    lowered = normalized.lower()

    if _REDACTION_MARKER in normalized:
        return False

    if is_placeholder_secret(normalized):
        return False

    if lowered in _NON_SECRET_LITERALS:
        return False

    if _NUMERIC_RE.fullmatch(normalized):
        return False

    if len(normalized) < 6:
        return False

    return True


def _is_full_line_comment(line: str) -> bool:
    """Return whether line is a full-line hash comment."""

    return line.lstrip().startswith("#")


def _extract_value(match: Match[str]) -> str:
    """Extract the secret value from a regex match."""

    quoted_value = match.groupdict().get("quoted_value")
    if quoted_value is not None:
        return quoted_value

    unquoted_value = match.groupdict().get("unquoted_value") or ""
    return unquoted_value.strip()


def _extract_variable_name(match: Match[str]) -> str | None:
    """Extract the matched variable name from a regex match."""

    groups = match.groupdict()
    return groups.get("env_name") or groups.get("name")


def detect_secrets_in_text(
    text: str,
    file_path: str,
    patterns: list[SecretPattern] | None = None,
) -> list[SecretFinding]:
    """Detect assignment-based potential secrets in text."""

    active_patterns = patterns or default_secret_patterns()
    findings: list[SecretFinding] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if _is_full_line_comment(line):
            continue

        for pattern in active_patterns:
            match = pattern.regex.search(line)
            if not match:
                continue

            value = _extract_value(match)
            if not is_probably_secret_value(value):
                continue

            findings.append(
                SecretFinding(
                    file_path=file_path,
                    line_number=line_number,
                    secret_type=pattern.secret_type,
                    matched_text=value,
                    masked_text=mask_secret_in_line(line, value),
                    variable_name=_extract_variable_name(match),
                    confidence=pattern.confidence,
                )
            )
            break

    return findings


@dataclass(frozen=True)
class SecretScanResult:
    """Result of scanning and masking one text payload."""

    masked_text: str
    findings: list[SecretFinding]

    @property
    def total_findings(self) -> int:
        """Return the number of findings."""

        return len(self.findings)

    @property
    def findings_by_type(self) -> dict[str, int]:
        """Return finding counts grouped by secret type."""

        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.secret_type] = counts.get(finding.secret_type, 0) + 1
        return counts


def _split_line_ending(line: str) -> tuple[str, str]:
    """Split line content from its original line ending."""

    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def mask_secrets_in_text(text: str, file_path: str) -> tuple[str, list[SecretFinding]]:
    """Mask potential secrets in text and return the masked text and findings."""

    masked_lines: list[str] = []
    findings: list[SecretFinding] = []

    for line_number, raw_line in enumerate(text.splitlines(keepends=True), start=1):
        line_body, line_ending = _split_line_ending(raw_line)
        line_findings = detect_secrets_in_text(line_body, file_path)

        if not line_findings:
            masked_lines.append(raw_line)
            continue

        finding = line_findings[0]
        adjusted_finding = SecretFinding(
            file_path=finding.file_path,
            line_number=line_number,
            secret_type=finding.secret_type,
            matched_text=finding.matched_text,
            masked_text=finding.masked_text,
            variable_name=finding.variable_name,
            confidence=finding.confidence,
        )
        findings.append(adjusted_finding)
        masked_lines.append(finding.masked_text + line_ending)

    return "".join(masked_lines), findings


def scan_and_mask_text(text: str, file_path: str) -> SecretScanResult:
    """Scan and mask text, returning a structured scan result."""

    masked_text, findings = mask_secrets_in_text(text, file_path)
    return SecretScanResult(masked_text=masked_text, findings=findings)


def _format_export_secret_detection_section(
    findings: list[SecretFinding],
    summary_line: str,
) -> str:
    """Format a generic export secret detection section without leaking values."""

    if not findings:
        return ""

    counts_by_type: dict[str, int] = {}
    for finding in findings:
        counts_by_type[finding.secret_type] = counts_by_type.get(finding.secret_type, 0) + 1

    lines = [
        "# Secret Detection",
        "",
        summary_line,
        f"Potential secrets masked: {len(findings)}",
        "",
        "Findings by type:",
    ]

    for secret_type in sorted(counts_by_type):
        lines.append(f"- {secret_type}: {counts_by_type[secret_type]}")

    return "\n".join(lines)


def mask_export_file(
    output_path: object,
    export_label: str | None = None,
    summary_line: str = "Potential secrets were masked before export.",
) -> int:
    """Mask potential secrets in an already generated export file.

    This is a final safety net for CLI paths that write files directly instead
    of returning rendered export text through a shared renderer.
    """

    from pathlib import Path

    path = Path(output_path)
    if not path.exists() or not path.is_file():
        return 0

    original = path.read_text(encoding="utf-8")
    masked_text, findings = mask_secrets_in_text(original, export_label or path.name)

    has_existing_redaction = _REDACTION_MARKER in masked_text

    if "# Secret Detection" not in masked_text and (findings or has_existing_redaction):
        section = _format_export_secret_detection_section(findings, summary_line)

        if not section and has_existing_redaction:
            section = "\n".join(
                [
                    "# Secret Detection",
                    "",
                    summary_line,
                    "Potential secrets masked: already masked before final export check",
                ]
            )

        masked_text = f"{masked_text.rstrip()}\n\n{section}\n"

    if masked_text != original:
        path.write_text(masked_text, encoding="utf-8")

    return len(findings)

