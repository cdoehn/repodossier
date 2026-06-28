from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repocontext.git import ChangedFile, get_changed_files


ScannerFunction = Callable[[Path], Any]


@dataclass(frozen=True)
class ChangedFileScan:
    """A changed file together with optional scanner metadata."""

    changed_file: ChangedFile
    file_info: Any | None = None

    @property
    def path(self) -> str:
        return self.changed_file.path

    @property
    def status(self) -> str:
        return self.changed_file.status

    @property
    def is_deleted(self) -> bool:
        return self.changed_file.is_deleted

    @property
    def is_untracked(self) -> bool:
        return self.changed_file.is_untracked

    @property
    def is_binary(self) -> bool:
        return bool(getattr(self.file_info, "is_binary", False))


def _default_scan_file(path: Path) -> Any:
    """Scan a file by reusing the existing scanner module.

    RepoContext has evolved over milestones, so this adapter supports the
    stable scanner entrypoint while keeping the changed export independent
    from exporter-specific details.
    """
    from repocontext import scanner

    scan_file = getattr(scanner, "scan_file", None)
    if scan_file is None:
        raise RuntimeError("repocontext.scanner.scan_file is not available")

    return scan_file(path)


def scan_changed_file(
    repo_path: str | Path,
    changed_file: ChangedFile,
    *,
    scanner: ScannerFunction | None = None,
) -> ChangedFileScan:
    """Scan one changed file unless it was deleted."""

    if changed_file.is_deleted:
        return ChangedFileScan(changed_file=changed_file, file_info=None)

    absolute_path = Path(repo_path) / changed_file.path
    if not absolute_path.exists():
        return ChangedFileScan(changed_file=changed_file, file_info=None)

    scan = scanner or _default_scan_file
    return ChangedFileScan(
        changed_file=changed_file,
        file_info=scan(absolute_path),
    )


def collect_changed_file_scans(
    repo_path: str | Path = ".",
    *,
    changed_files: Sequence[ChangedFile] | None = None,
    scanner: ScannerFunction | None = None,
) -> list[ChangedFileScan]:
    """Return scanner metadata for all changed files in stable path order."""

    repo = Path(repo_path)
    files = list(changed_files) if changed_files is not None else get_changed_files(repo)

    return [
        scan_changed_file(repo, changed_file, scanner=scanner)
        for changed_file in sorted(files, key=lambda item: item.path)
    ]
