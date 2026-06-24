"""Command-line interface entrypoint for RepoContext."""

from __future__ import annotations

import argparse
from importlib import metadata
from typing import Iterable, Optional


_FALLBACK_VERSION = "0.1.0.dev0"


def _determine_version() -> str:
    """Return the installed package version or a fallback value."""
    try:
        return metadata.version("repocontext")
    except metadata.PackageNotFoundError:
        return _FALLBACK_VERSION


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Run the RepoContext command-line interface.

    Args:
        argv: Optional iterable of argument strings. Defaults to ``None`` to use
            :data:`sys.argv`.

    Returns:
        An integer process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="repocontext",
        description=(
            "RepoContext prepares AI-friendly exports of Git repositories, "
            "tailored for large language models."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_determine_version()}")

    parser.parse_args(argv)

    print("RepoContext CLI is under construction.")
    return 0
