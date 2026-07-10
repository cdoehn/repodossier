#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_PATTERN_SPECS = (
    ("person_name", "Example" + " Private" + " Name"),
    ("person_email", "example.private" + "@" + "example.invalid"),
    ("home_path", "/home/" + "exampleuser"),
    ("old_project_path", "market_" + "research"),
    ("workstation_name", "Example" + "Machine"),
)
FORBIDDEN_PATTERNS = [value for _name, value in DEFAULT_PATTERN_SPECS]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    pattern: str
    text: str


def _is_probably_binary(raw: bytes) -> bool:
    return b"\0" in raw[:4096]


def _legacy_scan_text(path: str, text: str, patterns: Sequence[str]) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            if pattern in line:
                findings.append(Finding(path=path, line=line_number, pattern=pattern, text=line.strip()))
    return findings


def scan_text(path: str, text: str, patterns: list[str] | None = None) -> list[Finding]:
    active_patterns = tuple(patterns or FORBIDDEN_PATTERNS)
    patchharbor_scan_text = _load_patchharbor_scan_text()
    if patchharbor_scan_text is None:
        return _legacy_scan_text(path, text, active_patterns)

    try:
        result = patchharbor_scan_text(
            path,
            text,
            _patchharbor_pattern_mappings(active_patterns),
            target_type="text",
            metadata_mode="source-wrapper",
        )
    except Exception:
        return _legacy_scan_text(path, text, active_patterns)

    return [
        Finding(
            path=finding.path,
            line=finding.line,
            pattern=finding.pattern.value,
            text=finding.text,
        )
        for finding in result.findings
    ]


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
    patchharbor_result = _run_patchharbor_tracked_scan(repo)
    if patchharbor_result is not None:
        return patchharbor_result
    return _scan_tracked_legacy(repo)


def _scan_tracked_legacy(repo: Path) -> list[Finding]:
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


def _load_patchharbor_scan_text():
    _ensure_patchharbor_import_path()
    try:
        from patchharbor.public_audit_checks import scan_public_audit_text
    except Exception:
        return None
    return scan_public_audit_text


def _ensure_patchharbor_import_path(repo: Path | None = None) -> Path | None:
    source = _patchharbor_src(repo)
    if source is not None and str(source) not in sys.path:
        sys.path.insert(0, str(source))
    return source


def _patchharbor_src(repo: Path | None = None) -> Path | None:
    for candidate in _patchharbor_src_candidates(repo):
        if (candidate / "patchharbor" / "public_audit_checks.py").is_file():
            return candidate
    return None


def _patchharbor_src_candidates(repo: Path | None = None) -> Iterable[Path]:
    env_src = os.environ.get("PATCHHARBOR_SRC")
    if env_src:
        yield Path(env_src).expanduser().resolve()

    env_repo = os.environ.get("PATCHHARBOR_REPO")
    if env_repo:
        yield Path(env_repo).expanduser().resolve() / "src"

    if repo is not None:
        yield repo.resolve().parent / "patch-harbor" / "src"

    script_root = Path(__file__).resolve().parents[2]
    yield script_root.parent / "patch-harbor" / "src"


def _patchharbor_pattern_mappings(patterns: Sequence[str]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "name": _pattern_name(index, pattern),
            "value": pattern,
            "severity": "error",
        }
        for index, pattern in enumerate(patterns)
    )


def _patchharbor_cli_pattern_args(patterns: Sequence[str]) -> list[str]:
    args: list[str] = []
    for index, pattern in enumerate(patterns):
        args.extend(["--pattern", f"{_pattern_name(index, pattern)}={pattern}"])
    return args


def _pattern_name(index: int, pattern: str) -> str:
    for name, value in DEFAULT_PATTERN_SPECS:
        if pattern == value:
            return name
    return f"pattern_{index + 1}"


def _run_patchharbor_tracked_scan(repo: Path) -> list[Finding] | None:
    patchharbor_src = _ensure_patchharbor_import_path(repo)
    if patchharbor_src is None:
        return None

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(patchharbor_src) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")

    command = [
        sys.executable,
        "-m",
        "patchharbor",
        "audit-public",
        "--repo",
        str(repo),
        *_patchharbor_cli_pattern_args(FORBIDDEN_PATTERNS),
    ]
    result = subprocess.run(
        command,
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode in (0, 1):
        return _findings_from_patchharbor_stdout(result.stdout)
    return None


_PATCHHARBOR_FINDING_RE = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+)(?::\d+)?: (?P<severity>error|warning|info)/(?P<name>[^:]+): (?P<text>.*)$"
)


def _findings_from_patchharbor_stdout(stdout: str) -> list[Finding]:
    findings: list[Finding] = []
    pattern_by_name = {name: value for name, value in DEFAULT_PATTERN_SPECS}
    for line in stdout.splitlines():
        match = _PATCHHARBOR_FINDING_RE.match(line)
        if match is None:
            continue
        name = match.group("name")
        findings.append(
            Finding(
                path=match.group("path"),
                line=int(match.group("line")),
                pattern=pattern_by_name.get(name, name),
                text=match.group("text"),
            )
        )
    return findings


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
