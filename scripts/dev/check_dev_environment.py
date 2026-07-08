#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    hint: str = ""


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _repo_root(start: Path) -> Path:
    result = _run(["git", "rev-parse", "--show-toplevel"], cwd=start)
    if result.returncode != 0:
        raise RuntimeError("not inside a git repository")
    return Path(result.stdout.strip())


def _check_git_identity(repo_root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    for key, hint_value in [
        ("user.name", "git config --global user.name \"Christian Döhn\""),
        ("user.email", "git config --global user.email \"christian.doehn@gmail.com\""),
    ]:
        result = _run(["git", "config", "--get", key], cwd=repo_root)
        value = result.stdout.strip()
        results.append(
            CheckResult(
                name=f"git {key}",
                ok=bool(value),
                detail=value or "not configured",
                hint="" if value else hint_value,
            )
        )
    return results


def _check_command(name: str, command: list[str], *, repo_root: Path, hint: str = "") -> CheckResult:
    binary = command[0]
    if shutil.which(binary) is None:
        return CheckResult(name=name, ok=False, detail=f"{binary} not found in PATH", hint=hint)

    result = _run(command, cwd=repo_root)
    output = (result.stdout or result.stderr).strip().splitlines()
    detail = output[0] if output else f"exit {result.returncode}"
    return CheckResult(name=name, ok=result.returncode == 0, detail=detail, hint=hint if result.returncode != 0 else "")


def _check_file(name: str, path: Path, *, executable: bool = False, hint: str = "") -> CheckResult:
    if not path.exists():
        return CheckResult(name=name, ok=False, detail=f"missing: {path}", hint=hint)
    if executable and not os.access(path, os.X_OK):
        return CheckResult(name=name, ok=False, detail=f"not executable: {path}", hint=f"chmod +x {path}")
    return CheckResult(name=name, ok=True, detail=str(path))


def collect_checks(repo_root: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []

    checks.append(CheckResult("repo root", repo_root.name == "repo_dossier", str(repo_root)))
    checks.extend(_check_git_identity(repo_root))

    checks.append(
        _check_command(
            "python",
            [sys.executable, "--version"],
            repo_root=repo_root,
            hint="sudo apt install python3 python3-venv python3-pip",
        )
    )
    checks.append(
        _check_command(
            "pytest",
            [sys.executable, "-m", "pytest", "--version"],
            repo_root=repo_root,
            hint="python -m pip install -e .[dev]",
        )
    )
    checks.append(
        _check_command(
            "repodossier cli",
            ["repodossier", "--help"],
            repo_root=repo_root,
            hint="pipx install -e .",
        )
    )
    checks.append(_check_command("pipx", ["pipx", "--version"], repo_root=repo_root, hint="python3 -m pip install --user pipx"))

    checks.append(_check_file("c runner", repo_root / "scripts/dev/run_latest_download_patch.sh", executable=True))
    checks.append(_check_file("r runner", repo_root / "scripts/dev/r.sh", executable=True, hint="Run DEV.12.4 or chmod +x scripts/dev/r.sh"))
    checks.append(_check_file("workflow rules", repo_root / "scripts/dev/patch-workflow-rules.json"))
    checks.append(_check_file("workflow rules validator", repo_root / "scripts/dev/validate_patch_workflow_rules.py", executable=True))

    return checks


def render_results(results: list[CheckResult]) -> str:
    lines = ["RepoDossier dev environment doctor", ""]
    for result in results:
        marker = "OK" if result.ok else "FAIL"
        lines.append(f"[{marker}] {result.name}: {result.detail}")
        if not result.ok and result.hint:
            lines.append(f"       hint: {result.hint}")

    failures = [result for result in results if not result.ok]
    lines.append("")
    if failures:
        lines.append(f"FAILED: {len(failures)} check(s) need attention.")
    else:
        lines.append("OK: development environment looks ready.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a RepoDossier development environment.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository path or child directory.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when optional tools such as pipx/CLI are missing.")
    args = parser.parse_args(argv)

    try:
        repo_root = _repo_root(args.repo)
    except RuntimeError as exc:
        print(f"RepoDossier dev environment doctor\n\n[FAIL] repo root: {exc}")
        return 2

    results = collect_checks(repo_root)
    print(render_results(results))

    failures = [result for result in results if not result.ok]
    if not failures:
        return 0

    if args.strict:
        return 1

    required_failures = [
        result
        for result in failures
        if result.name not in {"repodossier cli", "pipx"}
    ]
    return 1 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
