from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repodossier.git import ChangedFile, get_changed_files, get_changed_files_against_branch


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


def _default_scan_file(repository_root: Path, relative_path: str) -> Any:
    """Scan a changed file by reusing the existing scanner module.

    RepoDossier has used two scanner entrypoints over time. Prefer the newer
    scan_file(path) function when available, but support the existing
    scan_single_file(repo_root, relative_path) API used by the repository
    scanner.
    """
    from repodossier import scanner

    absolute_path = repository_root / relative_path

    scan_file = getattr(scanner, "scan_file", None)
    if scan_file is not None:
        return scan_file(absolute_path)

    scan_single_file = getattr(scanner, "scan_single_file", None)
    if scan_single_file is not None:
        return scan_single_file(repository_root, relative_path)

    raise RuntimeError(
        "Neither repodossier.scanner.scan_file nor "
        "repodossier.scanner.scan_single_file is available"
    )


def scan_changed_file(
    repo_path: str | Path,
    changed_file: ChangedFile,
    *,
    scanner: ScannerFunction | None = None,
) -> ChangedFileScan:
    """Scan one changed file unless it was deleted."""

    if changed_file.is_deleted:
        return ChangedFileScan(changed_file=changed_file, file_info=None)

    repo = Path(repo_path)
    absolute_path = repo / changed_file.path
    if not absolute_path.exists():
        return ChangedFileScan(changed_file=changed_file, file_info=None)

    if scanner is None:
        file_info = _default_scan_file(repo, changed_file.path)
    else:
        file_info = scanner(absolute_path)

    return ChangedFileScan(
        changed_file=changed_file,
        file_info=file_info,
    )


def collect_changed_file_scans(
    repo_path: str | Path = ".",
    *,
    changed_files: Sequence[ChangedFile] | None = None,
    branch: str | None = None,
    scanner: ScannerFunction | None = None,
) -> list[ChangedFileScan]:
    """Return scanner metadata for changed files in stable path order."""

    repo = Path(repo_path)

    if changed_files is not None:
        files = list(changed_files)
    elif branch:
        files = get_changed_files_against_branch(repo, branch)
    else:
        files = get_changed_files(repo)

    return [
        scan_changed_file(repo, changed_file, scanner=scanner)
        for changed_file in sorted(files, key=lambda item: item.path)
    ]
