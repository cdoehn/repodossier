"""
Foundational structures for repository scanning within RepoContext.

This module currently provides placeholders so that future tasks can
incrementally add file inspection, classification, and repository-wide
scanning features without altering module layout.
"""

from pathlib import Path
from typing import Iterable, Optional

from .models import FileInfo

_EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".sh": "bash",
    ".bash": "bash",
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
}

_FILENAME_LANGUAGE_MAP: dict[str, str] = {
    "readme": "markdown",
    "license": "text",
    "licence": "text",
    "copying": "text",
    "changelog": "markdown",
    "todo": "text",
    "makefile": "makefile",
    "dockerfile": "dockerfile",
}


def detect_language_from_extension(path: Path | str) -> Optional[str]:
    """
    Infer a file's language based on its extension.

    Parameters
    ----------
    path:
        Filesystem path or filename whose extension will be inspected.

    Returns
    -------
    Optional[str]
        The detected language name in lowercase if the extension is known,
        otherwise ``None``.
    """
    suffix = Path(path).suffix.lower()
    if not suffix:
        return None
    return _EXTENSION_LANGUAGE_MAP.get(suffix)


def detect_language_from_filename(path: Path | str) -> Optional[str]:
    """
    Infer a file's language based on common extensionless filenames.

    Parameters
    ----------
    path:
        Filesystem path or filename whose basename will be inspected.

    Returns
    -------
    Optional[str]
        The detected language name in lowercase if the filename is recognized
        and does not include an extension, otherwise ``None``.
    """
    file_path = Path(path)
    if file_path.suffix:
        return None

    filename = file_path.name.lower()
    if not filename:
        return None

    return _FILENAME_LANGUAGE_MAP.get(filename)


def is_text_file(path: Path | str, sample_size: int = 1024) -> bool:
    """
    Determine whether a file can be read as UTF-8 text.

    Parameters
    ----------
    path:
        Filesystem path to the file being examined.
    sample_size:
        Maximum number of bytes to read when probing the file.

    Returns
    -------
    bool
        True if the file's contents can be decoded as UTF-8 text, False otherwise.
    """
    file_path = Path(path)

    try:
        with file_path.open("rb") as file:
            sample = file.read(sample_size)
        sample.decode("utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def is_binary_file(path: Path | str, sample_size: int = 1024) -> bool:
    """
    Determine whether the file appears to be binary based on a small sample.

    Returns True if a null byte is present in the sampled bytes or if the file
    cannot be read. Returns False otherwise.
    """
    file_path = Path(path)

    try:
        with file_path.open("rb") as file:
            sample = file.read(sample_size)
    except OSError:
        return True

    return b"\x00" in sample


def scan_single_file(repository_root: Path | str, relative_path: Path | str) -> FileInfo:
    """
    Scan a single file within the repository and return its basic metadata.

    Parameters
    ----------
    repository_root:
        Filesystem path to the repository root.
    relative_path:
        Path to the file to scan, relative to the repository root.

    Returns
    -------
    FileInfo
        Metadata for the requested file, including resolved paths and file size.

    Raises
    ------
    ValueError
        If ``relative_path`` is an absolute path.
    FileNotFoundError
        If the file does not exist.
    """
    root_path = Path(repository_root).resolve()
    relative_file_path = Path(relative_path)

    if relative_file_path.is_absolute():
        raise ValueError("relative_path must be relative to repository root.")

    absolute_file_path = (root_path / relative_file_path).resolve()

    try:
        file_stat = absolute_file_path.stat()
    except PermissionError:
        return FileInfo(
            relative_path=relative_file_path,
            absolute_path=absolute_file_path,
            size_bytes=None,
            error=f"Permission denied: {absolute_file_path}",
        )
    except OSError as exc:
        if isinstance(exc, FileNotFoundError):
            raise
        return FileInfo(
            relative_path=relative_file_path,
            absolute_path=absolute_file_path,
            size_bytes=None,
            error=f"Unable to access file: {absolute_file_path} ({exc})",
        )

    is_binary = is_binary_file(absolute_file_path)
    is_text = is_text_file(absolute_file_path)

    return FileInfo(
        relative_path=relative_file_path,
        absolute_path=absolute_file_path,
        size_bytes=file_stat.st_size,
        is_text=is_text,
        is_binary=is_binary,
    )


def scan_multiple_files(
    repository_root: Path | str, relative_paths: Iterable[Path | str]
) -> list[FileInfo]:
    """
    Scan multiple files within the repository and return their metadata.

    Parameters
    ----------
    repository_root:
        Filesystem path to the repository root.
    relative_paths:
        Iterable of paths to the files to scan, relative to the repository root.

    Returns
    -------
    list[FileInfo]
        Metadata for each requested file, preserving the order of the provided paths.
    """
    return [scan_single_file(repository_root, relative_path) for relative_path in relative_paths]


class RepositoryScanner:
    """
    Placeholder for repository scanning functionality.

    Future implementations will handle walking filesystem trees,
    collecting file metadata, and producing scan results that other
    components of RepoContext can consume.
    """

    def scan(self, root_path: str) -> None:
        """
        Scan the repository located at ``root_path``.

        Parameters
        ----------
        root_path:
            The filesystem path to the repository that will be scanned.

        Raises
        ------
        NotImplementedError
            Always raised until the scanning logic is implemented in a
            subsequent task.
        """
        raise NotImplementedError("Repository scanning has not been implemented yet.")
