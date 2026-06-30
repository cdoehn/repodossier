"""
Foundational structures for repository scanning within RepoDossier.

This module currently provides placeholders so that future tasks can
incrementally add file inspection, classification, and repository-wide
scanning features without altering module layout.
"""

from pathlib import Path
from typing import Iterable, Optional

from .git import list_tracked_files
from .models import FileInfo


BASH_SOURCE_EXTENSIONS = (".sh", ".bash")


def is_bash_source_file(path: object, content: str | bytes | None = None) -> bool:
    """Return True when a path or shebang identifies a Bash or POSIX shell script."""

    path_text = str(path).lower()
    if path_text.endswith(BASH_SOURCE_EXTENSIONS):
        return True

    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    if not content:
        return False

    lines = content.splitlines()
    if not lines:
        return False

    first_line = lines[0].strip()
    if not first_line.startswith("#!"):
        return False

    parts = first_line[2:].strip().lower().replace("\t", " ").split()
    if not parts:
        return False

    executable = parts[0].rsplit("/", 1)[-1]
    if executable in {"bash", "sh"}:
        return True

    if executable == "env":
        for part in parts[1:]:
            if part.startswith("-"):
                continue
            if part.rsplit("/", 1)[-1] in {"bash", "sh"}:
                return True

    return False

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
    if is_bash_source_file(path, None):
        return "bash"

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


def estimate_tokens(path: Path | str) -> int:
    """Estimate token count using a simple 1 token per 4 characters heuristic."""
    content = Path(path).read_text(encoding="utf-8")
    if not content:
        return 0
    return (len(content) + 3) // 4


def count_total_lines(path: Path | str) -> int:
    """
    Count the total number of lines in a UTF-8 encoded text file.

    Parameters
    ----------
    path:
        Filesystem path to the file being examined.

    Returns
    -------
    int
        The total number of lines contained in the file. Returns 0 for empty files.

    Raises
    ------
    UnicodeDecodeError
        Propagated if the file cannot be decoded as UTF-8.
    OSError
        Propagated if the file cannot be accessed.
    """
    file_path = Path(path)
    line_count = 0

    with file_path.open("r", encoding="utf-8") as file:
        for line_count, _ in enumerate(file, start=1):
            pass

    return line_count


def count_empty_lines(path: Path | str) -> int:
    """
    Count the number of empty or whitespace-only lines in a UTF-8 encoded text file.

    Parameters
    ----------
    path:
        Filesystem path to the file being examined.

    Returns
    -------
    int
        The number of lines that are empty or contain only whitespace.
        Returns 0 for empty files.

    Raises
    ------
    UnicodeDecodeError
        Propagated if the file cannot be decoded as UTF-8.
    OSError
        Propagated if the file cannot be accessed.
    """
    file_path = Path(path)
    empty_line_count = 0

    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                empty_line_count += 1

    return empty_line_count


def count_python_comment_lines(path: Path | str) -> int:
    """
    Count the number of Python comment lines in a UTF-8 encoded text file.

    A line is considered a comment line if its first non-whitespace character
    is ``#``. Blank or whitespace-only lines are ignored, as are inline comments
    that appear after code on the same line.

    Parameters
    ----------
    path:
        Filesystem path to the file being examined.

    Returns
    -------
    int
        The number of Python comment lines detected. Returns 0 for empty files.

    Raises
    ------
    UnicodeDecodeError
        Propagated if the file cannot be decoded as UTF-8.
    OSError
        Propagated if the file cannot be accessed.
    """
    file_path = Path(path)
    comment_count = 0

    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.lstrip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                comment_count += 1

    return comment_count


def count_shell_comment_lines(path: Path | str) -> int:
    """
    Count shell comment lines in a UTF-8 encoded text file.

    Counts lines whose first non-whitespace character is '#',
    but ignores blank lines and shebang lines.
    """
    file_path = Path(path)
    comment_count = 0

    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.lstrip()
            if not stripped:
                continue
            if stripped.startswith("#!") :
                continue
            if stripped.startswith("#"):
                comment_count += 1

    return comment_count


def load_text_content(path: Path | str) -> str:
    """
    Load the complete UTF-8 text content of a file.

    Parameters
    ----------
    path:
        Path to a UTF-8 encoded text file.

    Returns
    -------
    str
        Complete file contents.

    Raises
    ------
    UnicodeDecodeError
        If the file is not valid UTF-8.
    OSError
        If the file cannot be accessed.
    """
    return Path(path).read_text(encoding="utf-8")


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
    detected_language = detect_language_from_extension(relative_file_path)
    if detected_language is None:
        detected_language = detect_language_from_filename(relative_file_path)

    if not is_text and not is_binary:
        return FileInfo(
            relative_path=relative_file_path,
            absolute_path=absolute_file_path,
            size_bytes=file_stat.st_size,
            is_text=False,
            is_binary=False,
            language=detected_language,
            error=f"Unable to decode file as UTF-8: {absolute_file_path}",
        )

    line_count: Optional[int] = None
    empty_line_count: Optional[int] = None
    comment_line_count: Optional[int] = None
    estimated_token_count: Optional[int] = None
    content: Optional[str] = None

    if is_text and not is_binary:
        try:
            line_count = count_total_lines(absolute_file_path)
            empty_line_count = count_empty_lines(absolute_file_path)
            estimated_token_count = estimate_tokens(absolute_file_path)
            content = load_text_content(absolute_file_path)
            if detected_language == "python":
                comment_line_count = count_python_comment_lines(absolute_file_path)
            elif detected_language == "bash":
                comment_line_count = count_shell_comment_lines(absolute_file_path)
        except UnicodeDecodeError as exc:
            return FileInfo(
                relative_path=relative_file_path,
                absolute_path=absolute_file_path,
                size_bytes=file_stat.st_size,
                is_text=False,
                is_binary=False,
                language=detected_language,
                error=f"Unable to decode file as UTF-8: {absolute_file_path} ({exc})",
            )
        except OSError as exc:
            return FileInfo(
                relative_path=relative_file_path,
                absolute_path=absolute_file_path,
                size_bytes=file_stat.st_size,
                is_text=is_text,
                is_binary=is_binary,
                language=detected_language,
                error=f"Unable to read file: {absolute_file_path} ({exc})",
            )

    return FileInfo(
        relative_path=relative_file_path,
        absolute_path=absolute_file_path,
        size_bytes=file_stat.st_size,
        is_text=is_text,
        is_binary=is_binary,
        language=detected_language,
        line_count=line_count,
        empty_line_count=empty_line_count,
        comment_line_count=comment_line_count,
        estimated_tokens=estimated_token_count,
        content=content,
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
    """Scan Git-tracked repository files into FileInfo objects."""

    def scan(self, root_path: Path | str) -> list[FileInfo]:
        """
        Scan Git-tracked files in the repository located at ``root_path``.

        Parameters
        ----------
        root_path:
            Filesystem path to the repository root.

        Returns
        -------
        list[FileInfo]
            File metadata for every existing Git-tracked file.
        """
        repository_root = Path(root_path).resolve()
        tracked_files = list_tracked_files(repository_root)
        return scan_multiple_files(
            repository_root,
            [tracked_file.path for tracked_file in tracked_files],
        )
