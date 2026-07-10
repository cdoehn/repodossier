"""Archive CLI contract, source resolution, and snapshot ZIP helpers."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import zipfile
from html import escape as escape_xml
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

from .scanner import detect_language, is_source_code_language

ARCHIVE_USAGE = "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER"
DEFAULT_ARCHIVE_NAME = "repodossier-archive.zip"

class ArchiveCliArgumentError(ValueError):
    """Raised when the archive CLI positional contract is violated."""

class ArchiveSourceResolutionError(ValueError):
    """Raised when a source folder cannot be resolved to a Git repository."""

class ArchiveCreationError(RuntimeError):
    """Raised when the shared archive cannot be created safely."""

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

@dataclass(frozen=True)
class ArchiveSnapshotFile:
    """One file copied from the visible working tree into the archive."""
    source_path: Path
    repository_relative_path: Path
    archive_path: PurePosixPath
    repository_id: str

@dataclass(frozen=True)
class SourceReference:
    """Structured reference from a report entry to an archived source file."""
    repository_id: str
    repository_path: Path
    archive_path: PurePosixPath
    report_relative_archive_path: PurePosixPath
    language: str

@dataclass(frozen=True)
class ArchiveBuildResult:
    """Result of a successful archive build."""
    archive_path: Path
    snapshot_files: tuple[ArchiveSnapshotFile, ...]
    resolved: ResolvedArchiveInputs
    source_references: tuple[SourceReference, ...]

def build_archive_parser(version: str) -> argparse.ArgumentParser:
    """Create the top-level parser for the archive CLI contract."""
    parser = argparse.ArgumentParser(
        prog="repodossier",
        usage=ARCHIVE_USAGE,
        description="RepoDossier creates one compressed ZIP dossier from one or more Git repository folders.",
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
    parser.add_argument("--version", action="version", version=f"repodossier {version}", help="Show the installed RepoDossier version and exit.")
    parser.add_argument("--output-name", metavar="DATEINAME", help="Use this exact archive filename. Any extension is accepted; the archive content remains ZIP.")
    parser.add_argument("paths", nargs="*", metavar="PFAD", help="One or more source folders followed by the output folder. The last positional argument is always the output folder.")
    return parser

def split_archive_positionals(paths: Sequence[str]) -> tuple[tuple[Path, ...], Path]:
    """Split archive CLI positionals into source folders and output folder."""
    if len(paths) < 2:
        raise ArchiveCliArgumentError("at least two positional arguments are required: one or more source folders followed by the output folder.")
    return tuple(Path(path) for path in paths[:-1]), Path(paths[-1])

def parse_archive_cli_arguments(namespace: argparse.Namespace) -> ArchiveCliArguments:
    """Convert a parsed argparse namespace into structured archive arguments."""
    source_paths, output_dir = split_archive_positionals(namespace.paths)
    output_name = getattr(namespace, "output_name", None)
    return ArchiveCliArguments(source_paths=source_paths, output_dir=output_dir, output_name=output_name, archive_name=DEFAULT_ARCHIVE_NAME)

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
    result = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise ArchiveSourceResolutionError(f"source folder is not inside a Git repository: {path}")
    root_text = result.stdout.strip()
    if not root_text:
        raise ArchiveSourceResolutionError(f"Git did not return a repository root for source folder: {path}")
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
        raise ArchiveSourceResolutionError(f"source folder is not below its detected Git repository root: {normalized}") from exc
    return normalized, repository_root, Path(".") if str(repository_relative) == "." else repository_relative

def _safe_repository_id_base(repository_root: Path) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", repository_root.name or "repository").strip("-._")
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

def resolve_archive_inputs(arguments: ArchiveCliArguments, *, cwd: Path | None = None) -> ResolvedArchiveInputs:
    """Resolve archive CLI arguments into source and repository records."""
    resolved_raw: list[tuple[Path, Path, Path, Path]] = []
    seen_sources: set[Path] = set()
    for original_source in arguments.source_paths:
        normalized, repository_root, repository_relative = resolve_source_folder(original_source, cwd=cwd)
        if normalized in seen_sources:
            continue
        seen_sources.add(normalized)
        resolved_raw.append((original_source, normalized, repository_root, repository_relative))
    repository_roots: list[Path] = []
    for _, _, repository_root, _ in resolved_raw:
        if repository_root not in repository_roots:
            repository_roots.append(repository_root)
    repository_ids = _assign_repository_ids(repository_roots)
    repositories = tuple(ResolvedArchiveRepository(repository_root=root, repository_id=repository_ids[root], archive_path=PurePosixPath("repositories") / repository_ids[root]) for root in repository_roots)
    repository_by_root = {repository.repository_root: repository for repository in repositories}
    sources = tuple(
        ResolvedArchiveSource(
            original_path=original,
            normalized_path=normalized,
            repository_root=repository_root,
            repository_relative_path=repository_relative,
            repository_id=repository_ids[repository_root],
            archive_source_path=_archive_source_path(repository_by_root[repository_root].archive_path, repository_relative),
        )
        for original, normalized, repository_root, repository_relative in resolved_raw
    )
    return ResolvedArchiveInputs(arguments=arguments, output_dir=_normalize_output_dir(arguments.output_dir, cwd=cwd), sources=sources, repositories=repositories)

def _git_ls_files(repository_root: Path) -> list[Path]:
    result = subprocess.run(["git", "-C", str(repository_root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ArchiveCreationError(f"could not enumerate Git working-tree files for {repository_root}: {message}")
    return [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]

def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True

def _should_exclude_snapshot_path(absolute_path: Path, *, repository_root: Path, output_dir: Path, final_archive_path: Path, temporary_archive_path: Path) -> bool:
    if ".git" in absolute_path.relative_to(repository_root).parts:
        return True
    if _is_relative_to(absolute_path, output_dir):
        return True
    if absolute_path == final_archive_path or absolute_path == temporary_archive_path:
        return True
    return False

def enumerate_repository_snapshot_files(repository: ResolvedArchiveRepository, *, output_dir: Path, final_archive_path: Path, temporary_archive_path: Path) -> tuple[ArchiveSnapshotFile, ...]:
    """Enumerate visible Git working-tree files for one repository snapshot."""
    files: list[ArchiveSnapshotFile] = []
    seen_relative_paths: set[Path] = set()
    for relative_path in _git_ls_files(repository.repository_root):
        if relative_path in seen_relative_paths:
            continue
        seen_relative_paths.add(relative_path)
        absolute_path = (repository.repository_root / relative_path).resolve(strict=False)
        if not absolute_path.exists() or not absolute_path.is_file():
            continue
        if _should_exclude_snapshot_path(absolute_path, repository_root=repository.repository_root, output_dir=output_dir, final_archive_path=final_archive_path, temporary_archive_path=temporary_archive_path):
            continue
        files.append(ArchiveSnapshotFile(source_path=absolute_path, repository_relative_path=relative_path, archive_path=repository.archive_path / PurePosixPath(relative_path.as_posix()), repository_id=repository.repository_id))
    return tuple(files)

def enumerate_all_snapshot_files(resolved: ResolvedArchiveInputs, *, final_archive_path: Path, temporary_archive_path: Path) -> tuple[ArchiveSnapshotFile, ...]:
    """Enumerate all snapshot files for all unique repositories."""
    files: list[ArchiveSnapshotFile] = []
    for repository in resolved.repositories:
        files.extend(enumerate_repository_snapshot_files(repository, output_dir=resolved.output_dir, final_archive_path=final_archive_path, temporary_archive_path=temporary_archive_path))
    return tuple(files)

def _read_language_sample(path: Path, limit: int = 8192) -> str | bytes | None:
    """Read a small sample for central language detection."""
    try:
        return path.read_bytes()[:limit]
    except OSError:
        return None


def _snapshot_is_inside_source(
    snapshot_file: ArchiveSnapshotFile,
    source: ResolvedArchiveSource,
) -> bool:
    if snapshot_file.repository_id != source.repository_id:
        return False
    source_relative = source.repository_relative_path
    if source_relative == Path("."):
        return True
    try:
        snapshot_file.repository_relative_path.relative_to(source_relative)
    except ValueError:
        return False
    return True


def _source_for_snapshot(
    snapshot_file: ArchiveSnapshotFile,
    sources: Sequence[ResolvedArchiveSource],
) -> ResolvedArchiveSource | None:
    matching = [source for source in sources if _snapshot_is_inside_source(snapshot_file, source)]
    if not matching:
        return None
    return max(matching, key=lambda source: len(source.repository_relative_path.parts))


def collect_source_references(
    resolved: ResolvedArchiveInputs,
    snapshot_files: Sequence[ArchiveSnapshotFile],
) -> tuple[SourceReference, ...]:
    """Return structured source-code references for analyzed source folders.

    Source code classification uses RepoDossier's central language-detection
    pipeline. This function intentionally does not maintain a second list of
    source-code file extensions.
    """
    references: list[SourceReference] = []
    seen: set[tuple[str, Path]] = set()

    for snapshot_file in snapshot_files:
        source = _source_for_snapshot(snapshot_file, resolved.sources)
        if source is None:
            continue

        sample = _read_language_sample(snapshot_file.source_path)
        language = detect_language(snapshot_file.repository_relative_path, sample)
        if not is_source_code_language(language):
            continue

        key = (snapshot_file.repository_id, snapshot_file.repository_relative_path)
        if key in seen:
            continue
        seen.add(key)

        references.append(
            SourceReference(
                repository_id=snapshot_file.repository_id,
                repository_path=snapshot_file.repository_relative_path,
                archive_path=snapshot_file.archive_path,
                report_relative_archive_path=PurePosixPath("..") / snapshot_file.archive_path,
                language=language or "unknown",
            )
        )

    return tuple(references)


def render_source_references_text(references: Sequence[SourceReference]) -> str:
    """Render source references for plain-text reports."""
    lines = ["RepoDossier source references", ""]
    if not references:
        lines.append("No source-code files were detected in the selected source folders.")
        return "\n".join(lines) + "\n"

    for reference in references:
        lines.append(f"Repository: {reference.repository_id}")
        lines.append(f"Language: {reference.language}")
        lines.append(f"Source file: {reference.repository_path.as_posix()}")
        lines.append(f"Archive path: {reference.report_relative_archive_path.as_posix()}")
        lines.append("")
    return "\n".join(lines)


def render_source_references_markdown(references: Sequence[SourceReference]) -> str:
    """Render source references for Markdown reports."""
    lines = [
        "# RepoDossier source references",
        "",
        "Full source-code contents are stored in the repository snapshots, not embedded in this report.",
        "",
    ]
    if not references:
        lines.append("No source-code files were detected in the selected source folders.")
        return "\n".join(lines) + "\n"

    lines.extend(["| Repository | Language | Source file | Archive path |", "| --- | --- | --- | --- |"])
    for reference in references:
        lines.append(
            "| "
            f"{reference.repository_id} | "
            f"{reference.language} | "
            f"{reference.repository_path.as_posix()} | "
            f"{reference.report_relative_archive_path.as_posix()} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_source_references_xml(references: Sequence[SourceReference]) -> str:
    """Render source references for XML reports."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<source-files>",
    ]
    for reference in references:
        lines.append(
            "  <source-file"
            f' repository-id="{escape_xml(reference.repository_id)}"'
            f' language="{escape_xml(reference.language)}"'
            f' repository-path="{escape_xml(reference.repository_path.as_posix())}"'
            f' archive-path="{escape_xml(reference.report_relative_archive_path.as_posix())}"'
            " />"
        )
    lines.append("</source-files>")
    return "\n".join(lines) + "\n"


def _write_source_reference_reports(
    archive: zipfile.ZipFile,
    references: Sequence[SourceReference],
) -> None:
    archive.writestr("reports/source-references.txt", render_source_references_text(references))
    archive.writestr("reports/source-references.md", render_source_references_markdown(references))
    archive.writestr("reports/source-references.xml", render_source_references_xml(references))


def _archive_final_path(resolved: ResolvedArchiveInputs) -> Path:
    return resolved.output_dir / resolved.arguments.archive_filename

def _temporary_archive_path(final_archive_path: Path) -> Path:
    base = f".{final_archive_path.name}.tmp-{os.getpid()}"
    candidate = final_archive_path.with_name(base)
    index = 0
    while candidate.exists():
        index += 1
        candidate = final_archive_path.with_name(f"{base}-{index}")
    return candidate

def _manifest_text(resolved: ResolvedArchiveInputs, snapshot_files: Sequence[ArchiveSnapshotFile]) -> str:
    lines = ["RepoDossier archive manifest", f"Archive filename: {resolved.arguments.archive_filename}", f"Sources: {len(resolved.sources)}"]
    for source in resolved.sources:
        lines.append(f"Source: {source.normalized_path}")
        lines.append(f"  Repository: {source.repository_id}")
        lines.append(f"  Repository path: {source.repository_relative_path}")
        lines.append(f"  Archive path: {source.archive_source_path}")
    lines.append(f"Repositories: {len(resolved.repositories)}")
    for repository in resolved.repositories:
        lines.append(f"Repository: {repository.repository_id}")
        lines.append(f"  Root: {repository.repository_root}")
        lines.append(f"  Archive path: {repository.archive_path}")
    lines.append(f"Snapshot files: {len(snapshot_files)}")
    for snapshot_file in snapshot_files:
        lines.append(f"Snapshot file: {snapshot_file.repository_id}:{snapshot_file.repository_relative_path}")
        lines.append(f"  Archive path: {snapshot_file.archive_path}")
    return "\n".join(lines) + "\n"

def _write_archive_manifest(archive: zipfile.ZipFile, resolved: ResolvedArchiveInputs, snapshot_files: Sequence[ArchiveSnapshotFile]) -> None:
    archive.writestr("reports/archive-manifest.txt", _manifest_text(resolved, snapshot_files))

def _write_repository_snapshots(archive: zipfile.ZipFile, snapshot_files: Sequence[ArchiveSnapshotFile]) -> None:
    for snapshot_file in snapshot_files:
        archive.write(snapshot_file.source_path, snapshot_file.archive_path.as_posix())

def create_archive_dossier(resolved: ResolvedArchiveInputs) -> ArchiveBuildResult:
    """Create one compressed ZIP archive with reports and repository snapshots."""
    resolved.output_dir.mkdir(parents=True, exist_ok=True)
    final_path = _archive_final_path(resolved)
    if final_path.exists():
        raise ArchiveCreationError(f"output archive already exists: {final_path}")
    temporary_path = _temporary_archive_path(final_path)
    snapshot_files = enumerate_all_snapshot_files(resolved, final_archive_path=final_path.resolve(strict=False), temporary_archive_path=temporary_path.resolve(strict=False))
    source_references = collect_source_references(resolved, snapshot_files)
    try:
        with zipfile.ZipFile(temporary_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            _write_archive_manifest(archive, resolved, snapshot_files)
            _write_source_reference_reports(archive, source_references)
            _write_repository_snapshots(archive, snapshot_files)
        temporary_path.replace(final_path)
    except Exception as exc:
        temporary_path.unlink(missing_ok=True)
        if isinstance(exc, ArchiveCreationError):
            raise
        raise ArchiveCreationError(f"could not create archive {final_path}: {exc}") from exc
    return ArchiveBuildResult(archive_path=final_path, snapshot_files=snapshot_files, resolved=resolved, source_references=source_references)

def format_archive_contract_summary(arguments: ArchiveCliArguments) -> str:
    """Return a compact human-readable summary for the parsed archive contract."""
    lines = ["RepoDossier archive CLI contract accepted.", f"Sources: {len(arguments.source_paths)}"]
    for index, source in enumerate(arguments.source_paths, start=1):
        lines.append(f"  {index}. {source}")
    lines.append(f"Output folder: {arguments.output_dir}")
    lines.append(f"Archive filename: {arguments.archive_filename}")
    return "\n".join(lines)

def format_resolved_archive_summary(resolved: ResolvedArchiveInputs) -> str:
    """Return a human-readable summary for resolved archive inputs."""
    lines = [format_archive_contract_summary(resolved.arguments), f"Resolved sources: {len(resolved.sources)}"]
    for index, source in enumerate(resolved.sources, start=1):
        lines.append(f"  {index}. {source.normalized_path} (repository: {source.repository_id}, repository path: {source.repository_relative_path})")
        lines.append(f"     Archive source path: {source.archive_source_path}")
    lines.append(f"Repositories: {len(resolved.repositories)}")
    for repository in resolved.repositories:
        lines.append(f"  {repository.repository_id}: {repository.repository_root} -> {repository.archive_path}")
    lines.append(f"Normalized output folder: {resolved.output_dir}")
    return "\n".join(lines)

def format_archive_build_summary(result: ArchiveBuildResult) -> str:
    """Return a compact success message for a created archive."""
    return "\n".join([format_resolved_archive_summary(result.resolved), f"Wrote archive: {result.archive_path}", f"Snapshot files: {len(result.snapshot_files)}", f"Source references: {len(result.source_references)}"])
