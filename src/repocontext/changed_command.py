from __future__ import annotations

from argparse import Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Any

from repocontext.changed_exporter import write_changed_export
from repocontext.git import find_repository_root
from repocontext.gitignore import ensure_repocontext_gitignore_entries


def add_changed_subparser(subparsers: Any) -> Any:
    """Register the changed export subcommand on an argparse subparsers object."""

    parser = subparsers.add_parser(
        "changed",
        help="Generate changed.txt for git changes.",
        description=(
            "Generate changed.txt with changed files, unified diffs, "
            "and changed file contents."
        ),
        epilog=(
            "Examples:\n"
            "  repocontext changed\n"
            "  repocontext changed --branch main\n"
            "  repocontext changed --output review-changes.txt\n"
            "  repocontext changed --no-diff"
        ),
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        default="changed.txt",
        help="Output file path. Defaults to changed.txt.",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Compare against a branch using git's three-dot branch...HEAD diff, for example --branch main.",
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
        help="Do not include the unified Git diff section in changed.txt.",
    )

    parser.set_defaults(
        func=run_changed_command,
        handler=run_changed_command,
        command_handler=run_changed_command,
    )
    return parser


def run_changed_command(args: Namespace) -> int:
    """Run the changed export command from parsed CLI arguments."""

    repository_root = find_repository_root(Path.cwd())
    if repository_root is None:
        print("Error: not inside a Git repository")
        return 1

    ensure_repocontext_gitignore_entries(repository_root)

    requested_output = Path(getattr(args, "output", "changed.txt"))
    output_path = (
        requested_output
        if requested_output.is_absolute()
        else repository_root / requested_output
    )

    output = write_changed_export(
        repository_root,
        output_path,
        branch=getattr(args, "branch", None),
        include_diff=getattr(args, "include_diff", True),
    )
    print(f"Wrote {output}")
    return 0
