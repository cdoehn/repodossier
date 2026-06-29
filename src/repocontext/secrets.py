"""Secret detection models and masking helpers.

This module contains the core data structures and low-level masking helpers
used by later export integrations. It intentionally keeps scanning behavior
small and testable so exporters can share the same implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from re import Pattern
from typing import TypeAlias


SecretGroup: TypeAlias = str | int | None

_REDACTION_MARKER = "***REDACTED***"


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
    """Build a conservative assignment pattern for secret-like variables."""

    return re.compile(
        rf"""
        (?ix)
        (?P<prefix>
            ^\s*
            (?:export\s+)?
            (?:
                os\.environ\[
                    ['\"](?P<env_name>{variable_pattern})['\"]
                \]
                |
                (?P<name>{variable_pattern})
            )
            \s*(?:=|:)\s*
            (?P<quote>['\"]?)
        )
        (?P<value>[^'"\#\n]+?)
        (?P=quote)
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
            regex=_assignment_pattern(
                r"[A-Z0-9_]*(?:TOKEN|ACCESS_TOKEN|REFRESH_TOKEN|AUTH_TOKEN|BEARER_TOKEN)"
            ),
            secret_type="TOKEN",
            confidence="high",
            value_group="value",
        ),
        SecretPattern(
            name="secret_assignment",
            regex=_assignment_pattern(
                r"[A-Z0-9_]*(?:SECRET|CLIENT_SECRET|JWT_SECRET|SIGNING_SECRET|WEBHOOK_SECRET|APP_SECRET)"
            ),
            secret_type="SECRET",
            confidence="high",
            value_group="value",
        ),
        SecretPattern(
            name="password_assignment",
            regex=_assignment_pattern(
                r"[A-Z0-9_]*(?:PASSWORD|PASSWD|PWD|DB_PASSWORD|DATABASE_PASSWORD)"
            ),
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
