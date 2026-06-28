from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from repocontext.changed_exporter import write_changed_export


def add_changed_subparser(subparsers: Any) -> Any:
    """Register the changed export subcommand on an argparse subparsers object."""

    parser = subparsers.add_parser(
        "changed",
        help="Generate changed.txt for git changes.",
        description="Generate changed.txt with changed files, diffs, and contents.",
    )
    parser.add_argument(
        "--output",
        default="changed.txt",
        help="Output file path. Defaults to changed.txt.",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Compare against a branch using git's three-dot branch...HEAD diff.",
    )

    diff_group = parser.add_mutually_exclusive_group()
    diff_group.add_argument(
        "--include-diff",
        dest="include_diff",
        action="store_true",
        default=True,
        help="Include unified git diff output. This is the default.",
    )
    diff_group.add_argument(
        "--no-diff",
        dest="include_diff",
        action="store_false",
        help="Do not include unified git diff output.",
    )

    parser.set_defaults(
        func=run_changed_command,
        handler=run_changed_command,
        command_handler=run_changed_command,
    )
    return parser


def run_changed_command(args: Namespace) -> int:
    """Run the changed export command from parsed CLI arguments."""

    output = write_changed_export(
        Path.cwd(),
        getattr(args, "output", "changed.txt"),
        branch=getattr(args, "branch", None),
        include_diff=getattr(args, "include_diff", True),
    )
    print(f"Wrote {output}")
    return 0
