#!/usr/bin/env python3
"""Reusable local helper library for Example User's repo patch scripts.

This module is versioned with RepoDossier at:
    scripts/dev/repo_patch_helper.py

A legacy copy may also exist on Example User's machines at:
    ~/dev-scripts/repo_patch_helper.py

It can be imported from patch heredocs like this:
    import sys
    from pathlib import Path
    helper_dir = Path("scripts/dev").resolve()
    sys.path.insert(0, str(helper_dir))
    from repo_patch_helper import replace_once, write_text

It can also be used as a small CLI:
    python3 scripts/dev/repo_patch_helper.py smoke
    python3 scripts/dev/repo_patch_helper.py compile --repo . src tests/test_x.py
    python3 scripts/dev/repo_patch_helper.py pytest-existing --repo . tests/test_x.py
    python3 scripts/dev/repo_patch_helper.py commit-if-changed --repo . --message "Commit message" path1 path2
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ENCODING = "utf-8"

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"


class PatchHelperError(RuntimeError):
    """Raised when a patch helper operation cannot be completed safely."""


@dataclass(frozen=True)
class FooterItem:
    """One line in the colored task footer."""

    task_id: str
    title: str
    commit: str = ""
    fix: str = ""


def _colors_enabled() -> bool:
    return not os.environ.get("NO_COLOR")


def colored(text: str, color_code: str) -> str:
    if not _colors_enabled():
        return text
    return f"{color_code}{text}{NC}"


def as_path(path: str | Path) -> Path:
    return path if isinstance(path, Path) else Path(path)


def read_text(path: str | Path, *, encoding: str = ENCODING) -> str:
    return as_path(path).read_text(encoding=encoding)


def write_text(
    path: str | Path,
    text: str,
    *,
    encoding: str = ENCODING,
    final_newline: bool = True,
) -> Path:
    target = as_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if final_newline and text and not text.endswith("\n"):
        text += "\n"
    target.write_text(text, encoding=encoding)
    return target


def append_once(
    path: str | Path,
    block: str,
    *,
    marker: str | None = None,
    encoding: str = ENCODING,
    final_newline: bool = True,
) -> bool:
    target = as_path(path)
    text = read_text(target, encoding=encoding) if target.exists() else ""
    needle = marker or block
    if needle in text:
        return False

    if text and not text.endswith("\n"):
        text += "\n"
    text += block
    if final_newline and text and not text.endswith("\n"):
        text += "\n"

    write_text(target, text, encoding=encoding, final_newline=False)
    return True


def replace_once_text(text: str, old: str, new: str, *, label: str = "") -> str:
    count = text.count(old)
    if count != 1:
        name = f" for {label}" if label else ""
        raise PatchHelperError(
            f"Expected exactly one match{name}, found {count}."
        )
    return text.replace(old, new, 1)


def replace_once(
    path: str | Path,
    old: str,
    new: str,
    *,
    label: str = "",
    encoding: str = ENCODING,
) -> bool:
    target = as_path(path)
    text = read_text(target, encoding=encoding)
    updated = replace_once_text(text, old, new, label=label or str(target))
    if updated == text:
        return False
    write_text(target, updated, encoding=encoding)
    return True


def replace_if_present(
    path: str | Path,
    old: str,
    new: str,
    *,
    encoding: str = ENCODING,
) -> bool:
    target = as_path(path)
    text = read_text(target, encoding=encoding)
    if old not in text:
        return False
    updated = text.replace(old, new, 1)
    write_text(target, updated, encoding=encoding)
    return True


def insert_before_once(
    path: str | Path,
    needle: str,
    block: str,
    *,
    marker: str | None = None,
    label: str = "",
    encoding: str = ENCODING,
) -> bool:
    target = as_path(path)
    text = read_text(target, encoding=encoding)

    if marker and marker in text:
        return False
    if not marker and block in text:
        return False

    count = text.count(needle)
    if count != 1:
        name = f" for {label}" if label else f" in {target}"
        raise PatchHelperError(
            f"Expected exactly one insertion needle{name}, found {count}."
        )

    updated = text.replace(needle, block + needle, 1)
    write_text(target, updated, encoding=encoding)
    return True


def insert_after_once(
    path: str | Path,
    needle: str,
    block: str,
    *,
    marker: str | None = None,
    label: str = "",
    encoding: str = ENCODING,
) -> bool:
    target = as_path(path)
    text = read_text(target, encoding=encoding)

    if marker and marker in text:
        return False
    if not marker and block in text:
        return False

    count = text.count(needle)
    if count != 1:
        name = f" for {label}" if label else f" in {target}"
        raise PatchHelperError(
            f"Expected exactly one insertion needle{name}, found {count}."
        )

    updated = text.replace(needle, needle + block, 1)
    write_text(target, updated, encoding=encoding)
    return True


def ensure_line(
    path: str | Path,
    line: str,
    *,
    encoding: str = ENCODING,
) -> bool:
    target = as_path(path)
    text = read_text(target, encoding=encoding) if target.exists() else ""
    lines = text.splitlines()

    if line in lines:
        return False

    lines.append(line)
    write_text(target, "\n".join(lines), encoding=encoding)
    return True


def normalize_literal_newlines(
    path: str | Path,
    *,
    encoding: str = ENCODING,
) -> bool:
    """Repair accidental literal backslash-n sequences in generated source files.

    Use deliberately and only for files that should contain real line breaks.
    This is helpful after a bad text replacement accidentally wrote characters
    backslash+n into Python source.
    """

    target = as_path(path)
    text = read_text(target, encoding=encoding)
    if "\\n" not in text:
        return False

    updated = text.replace("\\n", "\n")
    write_text(target, updated, encoding=encoding)
    return True


def write_module(path: str | Path, content: str) -> Path:
    return write_text(path, content, final_newline=True)


def write_test(path: str | Path, content: str) -> Path:
    return write_text(path, content, final_newline=True)


def _clean_import_name(line: str) -> str:
    cleaned = line.strip()
    if "#" in cleaned:
        cleaned = cleaned.split("#", 1)[0].strip()
    cleaned = cleaned.rstrip(",").strip()
    cleaned = cleaned.strip("()").strip()
    return cleaned


def ensure_from_import_names(
    path: str | Path,
    module: str,
    names: Iterable[str],
    *,
    encoding: str = ENCODING,
) -> bool:
    """Ensure names are imported from a module using a stable multiline block."""

    target = as_path(path)
    text = read_text(target, encoding=encoding)
    lines = text.splitlines()
    required = {name.strip() for name in names if name.strip()}
    if not required:
        return False

    prefix = f"from {module} import "
    changed = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue

        start = index
        rest = stripped[len(prefix):].strip()
        existing: set[str] = set()

        if rest == "(" or rest.endswith("("):
            end = index
            while end < len(lines) and lines[end].strip() != ")":
                end += 1
            if end >= len(lines):
                raise PatchHelperError(
                    f"Could not find end of import block for {module} in {target}."
                )
            for raw in lines[start + 1 : end]:
                name = _clean_import_name(raw)
                if name:
                    existing.add(name)
        else:
            end = index
            raw_names = rest.strip("()")
            for raw in raw_names.split(","):
                name = _clean_import_name(raw)
                if name:
                    existing.add(name)

        merged = sorted(existing | required)
        replacement = [f"from {module} import ("]
        replacement.extend(f"    {name}," for name in merged)
        replacement.append(")")

        old_block = lines[start : end + 1]
        if old_block != replacement:
            lines = lines[:start] + replacement + lines[end + 1 :]
            changed = True

        break
    else:
        insert_at = 0
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("from __future__ import "):
                insert_at = index + 1

        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_at = index + 1

        block = [f"from {module} import ("]
        block.extend(f"    {name}," for name in sorted(required))
        block.append(")")
        lines = lines[:insert_at] + block + lines[insert_at:]
        changed = True

    if changed:
        write_text(target, "\n".join(lines), encoding=encoding)

    return changed


def run_stream(
    command: Sequence[str] | str,
    *,
    cwd: str | Path | None = None,
    log_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    """Run a command, stream output to terminal, and optionally tee to a log."""

    if isinstance(command, str):
        cmd = ["bash", "-lc", command]
    else:
        cmd = [str(part) for part in command]

    merged_env = os.environ.copy()
    if env:
        merged_env.update({str(key): str(value) for key, value in env.items()})

    log_handle = None
    if log_path is not None:
        log_target = as_path(log_path)
        log_target.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_target.open("w", encoding=ENCODING)

    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd is not None else None,
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            if log_handle is not None:
                log_handle.write(line)

        return process.wait()
    finally:
        if log_handle is not None:
            log_handle.close()


def copy_file_to_clipboard(log_path: str | Path) -> bool:
    """Copy a file to the X clipboard when xclip is available."""

    path = as_path(log_path)
    if not path.exists():
        print(colored(f"Fehlerlog nicht gefunden: {path}", RED))
        return False

    xclip = shutil.which("xclip")
    if not xclip:
        print("Hinweis: xclip ist nicht installiert. Fehlerlog wurde nicht kopiert.")
        return False

    with path.open("rb") as handle:
        subprocess.run(
            [xclip, "-selection", "clipboard"],
            stdin=handle,
            check=False,
        )

    print("Fehlerlog wurde in die Zwischenablage kopiert.")
    return True


def repo_path(path: str | Path | None = None) -> Path:
    return as_path(path or ".").resolve()


def collect_existing(paths: Iterable[str | Path], *, cwd: str | Path | None = None) -> list[str]:
    base = as_path(cwd) if cwd is not None else Path(".")
    existing: list[str] = []
    for raw in paths:
        path_text = str(raw)
        candidate = as_path(path_text)
        absolute = candidate if candidate.is_absolute() else base / candidate
        if absolute.exists():
            existing.append(path_text)
        else:
            print(f"skip missing optional path: {path_text}")
    return existing


def run_compileall(
    paths: Iterable[str | Path],
    *,
    cwd: str | Path | None = None,
    log_path: str | Path | None = None,
) -> int:
    existing = collect_existing(paths, cwd=cwd)
    if not existing:
        print("Keine vorhandenen Pfade für compileall gefunden.")
        return 0

    return run_stream(
        [sys.executable, "-m", "compileall", *existing],
        cwd=cwd,
        log_path=log_path,
    )


def run_pytest_existing(
    tests: Iterable[str | Path],
    *,
    cwd: str | Path | None = None,
    log_path: str | Path | None = None,
    extra_args: Iterable[str] = (),
) -> int:
    existing = collect_existing(tests, cwd=cwd)
    if not existing:
        print("Keine vorhandenen Testdateien gefunden.")
        return 0

    return run_stream(
        [sys.executable, "-m", "pytest", "--color=yes", *extra_args, *existing],
        cwd=cwd,
        log_path=log_path,
    )


def git_no_pager(
    args: Sequence[str],
    *,
    cwd: str | Path | None = None,
    log_path: str | Path | None = None,
) -> int:
    return run_stream(["git", "--no-pager", *args], cwd=cwd, log_path=log_path)


def git_diff(
    paths: Iterable[str | Path] = (),
    *,
    cwd: str | Path | None = None,
    staged: bool = False,
    log_path: str | Path | None = None,
) -> int:
    args = ["diff"]
    if staged:
        args.append("--cached")
    if paths:
        args.append("--")
        args.extend(str(path) for path in paths)
    return git_no_pager(args, cwd=cwd, log_path=log_path)


def git_status(*, cwd: str | Path | None = None, log_path: str | Path | None = None) -> int:
    return git_no_pager(["status", "--short"], cwd=cwd, log_path=log_path)


def git_commit_if_changed(
    message: str,
    paths: Iterable[str | Path],
    *,
    cwd: str | Path | None = None,
    log_path: str | Path | None = None,
) -> int:
    add_paths = [str(path) for path in paths]
    if not add_paths:
        raise PatchHelperError("No paths supplied for git_commit_if_changed.")

    add_status = run_stream(["git", "add", *add_paths], cwd=cwd, log_path=log_path)
    if add_status != 0:
        return add_status

    quiet = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(cwd) if cwd is not None else None,
        check=False,
    )
    if quiet.returncode == 0:
        print("Keine Änderungen zum Committen.")
        return 0

    return run_stream(["git", "commit", "-m", message], cwd=cwd, log_path=log_path)


def parse_footer_item(raw: str) -> FooterItem:
    parts = raw.split("|")
    parts.extend(["", "", "", ""])
    return FooterItem(
        task_id=parts[0].strip(),
        title=parts[1].strip(),
        commit=parts[2].strip(),
        fix=parts[3].strip(),
    )


def print_task_footer(
    *,
    current: FooterItem,
    done: Iterable[FooterItem] = (),
    upcoming: Iterable[FooterItem] = (),
    problems: Iterable[str] = (),
) -> None:
    print()
    print("============================================================")

    done_items = list(done)
    if done_items:
        print(colored("Erledigt:", GREEN))
        for item in done_items:
            print(colored(f"  {item.task_id} – {item.title}", GREEN))
            if item.commit:
                print(f"    Commit: {item.commit}")
            if item.fix:
                print(f"    Fix: {item.fix}")
        print()

    print(colored("Aktuell:", YELLOW))
    print(colored(f"  {current.task_id} – {current.title}", YELLOW))
    if current.commit:
        print(f"    Commit: {current.commit}")
    if current.fix:
        print(f"    Fix: {current.fix}")
    print()

    upcoming_items = list(upcoming)
    if upcoming_items:
        print(colored("Danach:", CYAN))
        for item in upcoming_items:
            print(colored(f"  {item.task_id} – {item.title}", CYAN))
        print()

    problem_items = list(problems)
    if problem_items:
        print(colored("Problem:", RED))
        for problem in problem_items:
            print(colored(f"  {problem}", RED))
        print()

    print("============================================================")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo_patch_helper.py",
        description="Local helper for Example User's repo patch scripts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("smoke", help="Verify that the helper can be imported and executed.")

    compile_parser = subparsers.add_parser("compile", help="Run python3 -m compileall on existing paths.")
    compile_parser.add_argument("--repo", default=".")
    compile_parser.add_argument("--log")
    compile_parser.add_argument("paths", nargs="+")

    pytest_parser = subparsers.add_parser("pytest-existing", help="Run pytest on existing test files only.")
    pytest_parser.add_argument("--repo", default=".")
    pytest_parser.add_argument("--log")
    pytest_parser.add_argument("--extra", action="append", default=[])
    pytest_parser.add_argument("tests", nargs="+")

    copy_parser = subparsers.add_parser("copy-log", help="Copy a log file to clipboard with xclip.")
    copy_parser.add_argument("log_path")

    diff_parser = subparsers.add_parser("diff", help="Show git diff without pager.")
    diff_parser.add_argument("--repo", default=".")
    diff_parser.add_argument("--staged", action="store_true")
    diff_parser.add_argument("paths", nargs="*")

    status_parser = subparsers.add_parser("status", help="Show git status --short.")
    status_parser.add_argument("--repo", default=".")

    commit_parser = subparsers.add_parser("commit-if-changed", help="Git add paths and commit if staged changes exist.")
    commit_parser.add_argument("--repo", default=".")
    commit_parser.add_argument("--message", required=True)
    commit_parser.add_argument("--log")
    commit_parser.add_argument("paths", nargs="+")

    footer_parser = subparsers.add_parser("footer", help="Print colored task footer.")
    footer_parser.add_argument("--task", required=True)
    footer_parser.add_argument("--title", required=True)
    footer_parser.add_argument("--commit", default="")
    footer_parser.add_argument("--fix", default="")
    footer_parser.add_argument("--done", action="append", default=[], help="Format: id|title|commit|fix")
    footer_parser.add_argument("--next", action="append", default=[], help="Format: id|title")
    footer_parser.add_argument("--problem", action="append", default=[])

    newline_parser = subparsers.add_parser("normalize-literal-newlines", help="Replace literal backslash-n with real newlines in files.")
    newline_parser.add_argument("paths", nargs="+")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "smoke":
        print("repo_patch_helper.py smoke OK")
        print(f"Python: {sys.version.split()[0]}")
        print(f"File: {Path(__file__).resolve()}")
        return 0

    if args.command == "compile":
        return run_compileall(args.paths, cwd=args.repo, log_path=args.log)

    if args.command == "pytest-existing":
        extra_args: list[str] = []
        for item in args.extra:
            extra_args.extend(part for part in item.split(" ") if part)
        return run_pytest_existing(
            args.tests,
            cwd=args.repo,
            log_path=args.log,
            extra_args=extra_args,
        )

    if args.command == "copy-log":
        return 0 if copy_file_to_clipboard(args.log_path) else 1

    if args.command == "diff":
        return git_diff(args.paths, cwd=args.repo, staged=args.staged)

    if args.command == "status":
        return git_status(cwd=args.repo)

    if args.command == "commit-if-changed":
        return git_commit_if_changed(
            args.message,
            args.paths,
            cwd=args.repo,
            log_path=args.log,
        )

    if args.command == "footer":
        print_task_footer(
            current=FooterItem(args.task, args.title, args.commit, args.fix),
            done=[parse_footer_item(item) for item in args.done],
            upcoming=[parse_footer_item(item) for item in args.next],
            problems=args.problem,
        )
        return 0

    if args.command == "normalize-literal-newlines":
        changed = False
        for raw_path in args.paths:
            if normalize_literal_newlines(raw_path):
                print(f"normalized literal newline escapes in {raw_path}")
                changed = True
            else:
                print(f"no literal newline escapes found in {raw_path}")
        return 0 if changed else 0

    parser.error(f"Unhandled command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
