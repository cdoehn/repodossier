"""Archive CLI contract helpers for RepoDossier.

This module owns the new top-level archive invocation contract:

    repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER

Commit 1 intentionally parses and validates the contract only. Repository
resolution, snapshots, archive creation, and renderer source references are
implemented by later hotfix commits.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ARCHIVE_USAGE = "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER"
DEFAULT_ARCHIVE_NAME = "repodossier-archive.zip"


class ArchiveCliArgumentError(ValueError):
    """Raised when the archive CLI positional contract is violated."""


@dataclass(frozen=True)
class ArchiveCliArguments:
    """Parsed archive CLI arguments for the new top-level invocation."""

    source_paths: tuple[Path, ...]
    output_dir: Path
    output_name: str | None
    archive_name: str

    @property
    def archive_filename(self) -> str:
        """Return the exact archive filename that should be used later."""

        return self.output_name if self.output_name is not None else self.archive_name


def build_archive_parser(version: str) -> argparse.ArgumentParser:
    """Create the top-level parser for the archive CLI contract."""

    parser = argparse.ArgumentParser(
        prog="repodossier",
        usage=ARCHIVE_USAGE,
        description=(
            "RepoDossier creates one compressed ZIP dossier from one or more "
            "Git repository folders."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Positionsargumente:\n"
            "  QUELLE        Ein Quellordner. Das kann die Wurzel eines Git-Repositories\n"
            "                oder ein Unterordner innerhalb eines Git-Repositories sein.\n"
            "  AUSGABEORDNER Das letzte Positionsargument ist immer der Ausgabeordner.\n"
            "\n"
            "ZIP-Paket:\n"
            "  Pro Aufruf wird genau ein gemeinsames ZIP-Archiv erzeugt. Es enthält\n"
            "  RepoDossier-Reports unter reports/ und Repository-Snapshots unter\n"
            "  repositories/. Der Dateiname ist frei wählbar; der Inhalt bleibt auch\n"
            "  bei anderer Dateiendung technisch ein ZIP-Archiv.\n"
            "\n"
            "Beispiele:\n"
            "  repodossier ./repository ./output\n"
            "  repodossier ./repository-a ./repository-b ./output\n"
            "  repodossier ./repository/backend ./repository/frontend ./output\n"
            "  repodossier ./repository ./output --output-name mein-paket.zip\n"
            "  repodossier ./repository ./output --output-name projektstand.xml\n"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"repodossier {version}",
        help="Show the installed RepoDossier version and exit.",
    )
    parser.add_argument(
        "--output-name",
        metavar="DATEINAME",
        help=(
            "Use this exact archive filename. Any extension is accepted; the "
            "archive content remains ZIP."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="PFAD",
        help=(
            "One or more source folders followed by the output folder. The "
            "last positional argument is always the output folder."
        ),
    )
    return parser


def split_archive_positionals(paths: Sequence[str]) -> tuple[tuple[Path, ...], Path]:
    """Split archive CLI positionals into source folders and output folder."""

    if len(paths) < 2:
        raise ArchiveCliArgumentError(
            "at least two positional arguments are required: "
            "one or more source folders followed by the output folder."
        )

    source_paths = tuple(Path(path) for path in paths[:-1])
    output_dir = Path(paths[-1])
    return source_paths, output_dir


def parse_archive_cli_arguments(
    namespace: argparse.Namespace,
) -> ArchiveCliArguments:
    """Convert a parsed argparse namespace into structured archive arguments."""

    source_paths, output_dir = split_archive_positionals(namespace.paths)
    output_name = getattr(namespace, "output_name", None)
    return ArchiveCliArguments(
        source_paths=source_paths,
        output_dir=output_dir,
        output_name=output_name,
        archive_name=DEFAULT_ARCHIVE_NAME,
    )


def format_archive_contract_summary(arguments: ArchiveCliArguments) -> str:
    """Return a compact human-readable summary for the parsed archive contract."""

    lines = [
        "RepoDossier archive CLI contract accepted.",
        f"Sources: {len(arguments.source_paths)}",
    ]
    for index, source in enumerate(arguments.source_paths, start=1):
        lines.append(f"  {index}. {source}")
    lines.append(f"Output folder: {arguments.output_dir}")
    lines.append(f"Archive filename: {arguments.archive_filename}")
    lines.append("Archive generation will be enabled by subsequent hotfix commits.")
    return "\n".join(lines)
