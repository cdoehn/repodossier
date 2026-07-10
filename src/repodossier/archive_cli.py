"""Archive CLI contract and source resolution helpers for RepoDossier.

The top-level archive invocation contract is:

    repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER

Commit 2 validates source folders and resolves the Git repository roots that
will later be snapshotted in full. Snapshot file enumeration, ZIP creation, and
renderer source references are implemented by later hotfix commits.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


ARCHIVE_USAGE = "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER"
DEFAULT_ARCHIVE_NAME = "repodossier-archive.zip"


class ArchiveCliArgumentError(ValueError):
    """Raised when the archive CLI positional contract is violated."""


class ArchiveSourceResolutionError(ValueError):
    """Raised when a source folder cannot be resolved to a Git repository."""


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


@dataclass(frozen=True)
class ResolvedArchiveRepository:
    """A unique Git repository participating in an archive invocation."""

    repository_root: Path
    repository_id: str
    archive_path: PurePosixPath


@dataclass(frozen=True)
class ResolvedArchiveSource:
    """A normalized analysis source folder inside a resolved Git repository."""

    original_path: Path
    normalized_path: Path
    repository_root: Path
    repository_relative_path: Path
    repository_id: str
    archive_source_path: PurePosixPath


@dataclass(frozen=True)
class ResolvedArchiveInputs:
    """Resolved archive invocation model used by later hotfix commits."""

    arguments: ArchiveCliArguments
    output_dir: Path
    sources: tuple[ResolvedArchiveSource, ...]
    repositories: tuple[ResolvedArchiveRepository, ...]


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


def _normalize_path(path: Path, *, cwd: Path | None = None) -> Path:
    base = cwd if cwd is not None else Path.cwd()
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = base / expanded
    return expanded.resolve()


def _normalize_output_dir(path: Path, *, cwd: Path | None = None) -> Path:
    base = cwd if cwd is not None else Path.cwd()
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = base / expanded
    return expanded.resolve(strict=False)


def _git_repository_root(path: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ArchiveSourceResolutionError(
            f"source folder is not inside a Git repository: {path}"
        )

    root_text = result.stdout.strip()
    if not root_text:
        raise ArchiveSourceResolutionError(
            f"Git did not return a repository root for source folder: {path}"
        )
    return Path(root_text).resolve()


def resolve_source_folder(source: Path, *, cwd: Path | None = None) -> tuple[Path, Path, Path]:
    """Resolve one source folder to normalized path, repository root, and relative path."""

    normalized = _normalize_path(source, cwd=cwd)
    if not normalized.exists():
        raise ArchiveSourceResolutionError(f"source folder does not exist: {source}")
    if not normalized.is_dir():
        raise ArchiveSourceResolutionError(f"source path is not a directory: {source}")

    repository_root = _git_repository_root(normalized)
    try:
        repository_relative = normalized.relative_to(repository_root)
    except ValueError as exc:
        raise ArchiveSourceResolutionError(
            f"source folder is not below its detected Git repository root: {normalized}"
        ) from exc

    if str(repository_relative) == ".":
        repository_relative = Path(".")
    return normalized, repository_root, repository_relative


def _safe_repository_id_base(repository_root: Path) -> str:
    name = repository_root.name or "repository"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
    return safe or "repository"


def _assign_repository_ids(repository_roots: Iterable[Path]) -> dict[Path, str]:
    result: dict[Path, str] = {}
    used: set[str] = set()
    base_counts: dict[str, int] = {}

    for root in repository_roots:
        if root in result:
            continue

        base = _safe_repository_id_base(root)
        base_counts[base] = base_counts.get(base, 0) + 1
        suffix = base_counts[base]
        candidate = base if suffix == 1 else f"{base}-{suffix}"
        while candidate in used:
            suffix += 1
            candidate = f"{base}-{suffix}"
        used.add(candidate)
        result[root] = candidate

    return result


def _archive_source_path(repository_archive_path: PurePosixPath, relative_path: Path) -> PurePosixPath:
    if relative_path == Path("."):
        return repository_archive_path
    return repository_archive_path / PurePosixPath(relative_path.as_posix())


def resolve_archive_inputs(
    arguments: ArchiveCliArguments,
    *,
    cwd: Path | None = None,
) -> ResolvedArchiveInputs:
    """Resolve archive CLI arguments into source and repository records."""

    resolved_raw: list[tuple[Path, Path, Path, Path]] = []
    seen_sources: set[Path] = set()

    for original_source in arguments.source_paths:
        normalized, repository_root, repository_relative = resolve_source_folder(
            original_source,
            cwd=cwd,
        )
        if normalized in seen_sources:
            continue
        seen_sources.add(normalized)
        resolved_raw.append((original_source, normalized, repository_root, repository_relative))

    repository_roots: list[Path] = []
    for _, _, repository_root, _ in resolved_raw:
        if repository_root not in repository_roots:
            repository_roots.append(repository_root)

    repository_ids = _assign_repository_ids(repository_roots)
    repositories = tuple(
        ResolvedArchiveRepository(
            repository_root=root,
            repository_id=repository_ids[root],
            archive_path=PurePosixPath("repositories") / repository_ids[root],
        )
        for root in repository_roots
    )
    repository_by_root = {repository.repository_root: repository for repository in repositories}

    sources = tuple(
        ResolvedArchiveSource(
            original_path=original,
            normalized_path=normalized,
            repository_root=repository_root,
            repository_relative_path=repository_relative,
            repository_id=repository_ids[repository_root],
            archive_source_path=_archive_source_path(
                repository_by_root[repository_root].archive_path,
                repository_relative,
            ),
        )
        for original, normalized, repository_root, repository_relative in resolved_raw
    )

    return ResolvedArchiveInputs(
        arguments=arguments,
        output_dir=_normalize_output_dir(arguments.output_dir, cwd=cwd),
        sources=sources,
        repositories=repositories,
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


def format_resolved_archive_summary(resolved: ResolvedArchiveInputs) -> str:
    """Return a human-readable summary for resolved archive inputs."""

    lines = [
        format_archive_contract_summary(resolved.arguments),
        f"Resolved sources: {len(resolved.sources)}",
    ]
    for index, source in enumerate(resolved.sources, start=1):
        lines.append(
            f"  {index}. {source.normalized_path} "
            f"(repository: {source.repository_id}, repository path: {source.repository_relative_path})"
        )
        lines.append(f"     Archive source path: {source.archive_source_path}")

    lines.append(f"Repositories: {len(resolved.repositories)}")
    for repository in resolved.repositories:
        lines.append(
            f"  {repository.repository_id}: {repository.repository_root} -> {repository.archive_path}"
        )
    lines.append(f"Normalized output folder: {resolved.output_dir}")
    return "\n".join(lines)
