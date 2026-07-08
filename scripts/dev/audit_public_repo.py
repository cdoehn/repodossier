#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_PATTERNS = [
    "Christian " + "Döhn",
    "christian" + ".doehn",
    "/home/" + "christian",
    "market_" + "research",
    "Blade-" + "15",
]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    pattern: str
    text: str


def _is_probably_binary(raw: bytes) -> bool:
    return b"\0" in raw[:4096]


def scan_text(path: str, text: str, patterns: list[str] | None = None) -> list[Finding]:
    active_patterns = patterns or FORBIDDEN_PATTERNS
    findings: list[Finding] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in active_patterns:
            if pattern in line:
                findings.append(Finding(path=path, line=line_number, pattern=pattern, text=line.strip()))

    return findings


def tracked_files(repo: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return [repo / line for line in result.stdout.splitlines() if line.strip()]


def scan_tracked(repo: Path) -> list[Finding]:
    findings: list[Finding] = []

    for path in tracked_files(repo):
        if not path.exists() or not path.is_file():
            continue
        raw = path.read_bytes()
        if _is_probably_binary(raw):
            continue
        text = raw.decode("utf-8", errors="replace")
        rel = path.relative_to(repo).as_posix()
        findings.extend(scan_text(rel, text))

    return findings


def scan_history(repo: Path) -> list[str]:
    lines: list[str] = []
    revs = subprocess.run(
        ["git", "rev-list", "--all"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if revs.returncode != 0 or not revs.stdout.strip():
        return lines

    revisions = revs.stdout.splitlines()
    for pattern in FORBIDDEN_PATTERNS:
        result = subprocess.run(
            ["git", "--no-pager", "grep", "-n", "-I", pattern, *revisions],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines.extend(result.stdout.splitlines())

    return lines


def print_tracked_findings(findings: list[Finding]) -> None:
    for finding in findings:
        print(f"{finding.path}:{finding.line}: forbidden {finding.pattern!r}: {finding.text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit tracked RepoDossier content for private/local machine references.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--tracked", action="store_true", help="Scan tracked files. Default when no mode is selected.")
    parser.add_argument("--history", action="store_true", help="Also scan git history for forbidden strings.")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    modes_selected = args.tracked or args.history

    status = 0

    if args.tracked or not modes_selected:
        findings = scan_tracked(repo)
        if findings:
            print("Public repo tracked-file audit failed:")
            print_tracked_findings(findings)
            status = 1
        else:
            print("Public repo tracked-file audit OK")

    if args.history:
        history_findings = scan_history(repo)
        if history_findings:
            print("Public repo history audit found matches:")
            for line in history_findings:
                print(line)
            status = 1
        else:
            print("Public repo history audit OK")

    return status


if __name__ == "__main__":
    raise SystemExit(main())
