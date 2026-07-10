"""
Foundational structures for repository scanning within RepoDossier.

This module currently provides placeholders so that future tasks can
incrementally add file inspection, classification, and repository-wide
scanning features without altering module layout.
"""

from pathlib import Path
import re
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
    """Infer a language from a file extension only."""

    extension_languages = {
        ".py": "python",
        ".sh": "bash",
        ".bash": "bash",
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "text",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "jsx",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".hh": "cpp",
        ".hxx": "cpp",
        ".cs": "csharp",
    }

    return extension_languages.get(Path(path).suffix.lower())

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

def _content_sample_as_text(content_sample: str | bytes | None) -> str | None:
    """Return a text representation of a language-detection content sample."""

    if content_sample is None:
        return None

    if isinstance(content_sample, bytes):
        return content_sample.decode("utf-8", errors="ignore")

    return content_sample


def _split_shebang_parts(content_sample: str | bytes | None) -> list[str]:
    """Return normalized shebang command parts from the first line only."""

    text = _content_sample_as_text(content_sample)
    if not text:
        return []

    first_line = text.splitlines()[0] if text.splitlines() else ""
    if not first_line.startswith("#!"):
        return []

    return first_line[2:].strip().lower().replace("\t", " ").split()


def detect_language_from_shebang(content_sample: str | bytes | None) -> Optional[str]:
    """
    Infer a language from a script shebang.

    Only the first line is inspected. Leading whitespace before ``#!`` is not
    treated as a valid shebang, which keeps the behavior conservative.
    """

    parts = _split_shebang_parts(content_sample)
    if not parts:
        return None

    executable = parts[0].rsplit("/", 1)[-1]

    if executable == "env":
        command_parts = [
            part.rsplit("/", 1)[-1]
            for part in parts[1:]
            if part and not part.startswith("-")
        ]
    else:
        command_parts = [executable]

    for command in command_parts:
        if command in {"python", "python3"} or command.startswith("python3."):
            return "python"
        if command in {"bash", "sh"}:
            return "bash"
        if command == "node":
            return "javascript"

    return None

CONTENT_LANGUAGE_SAMPLE_MAX_CHARS = 8192
CONTENT_LANGUAGE_MIN_SCORE = 20
CONTENT_LANGUAGE_MIN_MARGIN = 10


def _score_language(scores: dict[str, int], language: str, points: int) -> None:
    scores[language] = scores.get(language, 0) + points


def _content_language_sample(content_sample: str | bytes | None) -> str:
    text = _content_sample_as_text(content_sample)
    if not text:
        return ""
    return text[:CONTENT_LANGUAGE_SAMPLE_MAX_CHARS]


def _looks_like_markdown_document(text: str) -> bool:
    """Return whether text looks like a real Markdown document, not just code."""

    has_heading = bool(re.search(r"(?m)^#{1,6}\s+\S+", text))
    has_fence = "```" in text or "~~~" in text
    has_list = bool(re.search(r"(?m)^\s*[-*+]\s+\S+", text))
    has_blank_line = "\n\n" in text
    return has_heading and (has_fence or has_list or has_blank_line)


def _apply_false_positive_guards(scores: dict[str, int], text: str) -> None:
    """Reduce known false positives without hiding strong positive signals."""

    markdown_like = _looks_like_markdown_document(text)

    if markdown_like:
        _score_language(scores, "markdown", 60)
        for language in ("python", "javascript", "typescript", "html", "css"):
            scores[language] = max(0, scores.get(language, 0) - 80)

    if scores.get("json", 0) >= 35:
        for language in ("javascript", "typescript", "css"):
            scores[language] = max(0, scores.get(language, 0) - 25)

    if scores.get("yaml", 0) >= 20:
        scores["typescript"] = max(0, scores.get("typescript", 0) - 25)
        scores["css"] = max(0, scores.get("css", 0) - 15)

    if scores.get("toml", 0) >= 35:
        scores["ini"] = max(0, scores.get("ini", 0) - 15)


def detect_language_content_scores(
    path: Path | str,
    content_sample: str | bytes | None,
) -> dict[str, int]:
    """
    Return deterministic language scores from content heuristics only.

    The scoring is intentionally conservative. It does not parse, compile, or
    execute project code. Known file extensions and known filenames are handled
    by ``detect_language`` before these heuristics are allowed to decide.
    """

    text = _content_language_sample(content_sample)
    if not text.strip():
        return {}

    scores: dict[str, int] = {}
    stripped = text.lstrip()
    lower_text = text.lower()

    # Existing languages.
    if re.search(r"(?m)^\s*(?:async\s+def|def|class)\s+[A-Za-z_]\w*", text):
        _score_language(scores, "python", 30)
    if re.search(r"(?m)^\s*(?:from\s+[\w.]+\s+import\s+\w+|import\s+[\w.]+)", text):
        _score_language(scores, "python", 12)
    if '__name__ == "__main__"' in text or "__name__ == '__main__'" in text:
        _score_language(scores, "python", 25)

    if "set -euo pipefail" in text or re.search(r"(?m)^\s*set\s+-eu\b", text):
        _score_language(scores, "bash", 25)
    if re.search(r"(?m)^\s*(?:function\s+)?[A-Za-z_][\w-]*\s*\(\s*\)\s*\{", text):
        _score_language(scores, "bash", 25)

    if re.search(r"(?m)^#{1,6}\s+\S+", text):
        _score_language(scores, "markdown", 12)
    if "```" in text:
        _score_language(scores, "markdown", 12)

    if stripped.startswith("{") or stripped.startswith("["):
        if re.search(r'"[^"]+"\s*:', stripped):
            _score_language(scores, "json", 35)

    yaml_key_lines = re.findall(r"(?m)^[A-Za-z_][\w.-]*:\s+\S+", text)
    if len(yaml_key_lines) >= 2:
        _score_language(scores, "yaml", 22)
    if re.search(r"(?m)^\s*-\s+\S+", text) and yaml_key_lines:
        _score_language(scores, "yaml", 8)

    if re.search(r"(?m)^\s*\[(?:project|tool\.[^\]]+)\]\s*$", text):
        _score_language(scores, "toml", 35)
    if re.search(r'(?m)^[A-Za-z_][\w.-]*\s*=\s*"[^"]*"\s*$', text):
        _score_language(scores, "toml", 10)

    if re.search(r"(?m)^\s*\[[A-Za-z_][\w.-]*\]\s*$", text):
        _score_language(scores, "ini", 18)
    if re.search(r"(?m)^[A-Za-z_][\w.-]*\s*=\s*[^#;\n]+$", text):
        _score_language(scores, "ini", 8)

    # Web languages.
    if re.search(r"\binterface\s+[A-Za-z_]\w*\s*\{", text):
        _score_language(scores, "typescript", 30)
    if re.search(r"\btype\s+[A-Za-z_]\w*\s*=", text):
        _score_language(scores, "typescript", 25)
    if re.search(r"\benum\s+[A-Za-z_]\w*", text):
        _score_language(scores, "typescript", 20)
    if re.search(r"\b(?:const|let|var)\s+[A-Za-z_]\w*\s*:\s*[A-Za-z_][\w<>[\]|& ]*\s*=", text):
        _score_language(scores, "typescript", 30)
    if re.search(r"\b[A-Za-z_]\w*\s*:\s*(?:string|number|boolean|unknown|any)\b", text):
        _score_language(scores, "typescript", 15)

    if re.search(r"\bmodule\.exports\b|\brequire\s*\(", text):
        _score_language(scores, "javascript", 25)
    if re.search(r"\bexport\s+default\b", text):
        _score_language(scores, "javascript", 25)
    if re.search(r"\bimport\s+.+?\s+from\s+['\"][^'\"]+['\"]", text):
        _score_language(scores, "javascript", 15)
    if re.search(r"\bfunction\s+[A-Za-z_]\w*\s*\(", text):
        _score_language(scores, "javascript", 15)
    if re.search(r"\bconst\s+[A-Za-z_]\w*\s*=\s*(?:\([^)]*\)|[A-Za-z_]\w*)\s*=>", text):
        _score_language(scores, "javascript", 20)

    if "<!doctype html" in lower_text:
        _score_language(scores, "html", 50)
    if re.search(r"(?s)^\s*<html\b|<html\b.*</html>", lower_text):
        _score_language(scores, "html", 40)
    if re.search(r"<head\b", lower_text) and re.search(r"<body\b", lower_text):
        _score_language(scores, "html", 25)

    if re.search(r"(?m)^\s*@(media|import|keyframes)\b", text):
        _score_language(scores, "css", 30)
    if re.search(
        r"(?s)[.#]?[A-Za-z][\w\s.,:#>*+\-\[\]='\"]*\{\s*"
        r"(?:display|margin|padding|color|font-size|background|border)\s*:",
        text,
    ):
        _score_language(scores, "css", 35)

    # Java, C, C++, C#.
    if re.search(r"(?m)^\s*package\s+[A-Za-z_][\w.]*\s*;", text):
        _score_language(scores, "java", 20)
    if re.search(r"(?m)^\s*import\s+java[\w.]*\s*;", text):
        _score_language(scores, "java", 20)
    if re.search(r"\bpublic\s+(?:final\s+)?class\s+[A-Za-z_]\w*", text):
        _score_language(scores, "java", 30)
    if "public static void main" in text:
        _score_language(scores, "java", 25)

    if re.search(r"(?m)^\s*#\s*include\s+<stdio\.h>", text):
        _score_language(scores, "c", 30)
    if re.search(r"(?m)^\s*#\s*include\s+[<\"][^>\"]+[>\"]", text):
        _score_language(scores, "c", 10)
    if re.search(r"\bint\s+main\s*\(", text):
        _score_language(scores, "c", 30)
    if re.search(r"\btypedef\s+struct\b", text):
        _score_language(scores, "c", 30)
    if re.search(r"\bstruct\s+[A-Za-z_]\w*", text):
        _score_language(scores, "c", 12)

    if re.search(r"(?m)^\s*#\s*include\s+<(?:iostream|vector|string|map|memory)>", text):
        _score_language(scores, "cpp", 30)
    if re.search(r"\bnamespace\s+[A-Za-z_]\w*", text):
        _score_language(scores, "cpp", 30)
    if re.search(r"\btemplate\s*<", text):
        _score_language(scores, "cpp", 30)
    if "std::" in text:
        _score_language(scores, "cpp", 30)
    if re.search(r"\busing\s+namespace\s+[A-Za-z_]\w*", text):
        _score_language(scores, "cpp", 25)
    if re.search(r"\bclass\s+[A-Za-z_]\w*", text):
        _score_language(scores, "cpp", 15)

    if re.search(r"(?m)^\s*using\s+System(?:\.[A-Za-z_][\w.]*)?\s*;", text):
        _score_language(scores, "csharp", 30)
    if re.search(r"\bnamespace\s+[A-Za-z_][\w.]*\s*\{", text):
        _score_language(scores, "csharp", 20)
    if re.search(r"\bpublic\s+class\s+[A-Za-z_]\w*", text):
        _score_language(scores, "csharp", 15)
    if re.search(r"\basync\s+Task\b", text):
        _score_language(scores, "csharp", 25)
    if re.search(r"(?m)^\s*\[(?:Serializable|Test|Fact)\]", text):
        _score_language(scores, "csharp", 20)

    # Conflict guards for common false positives.
    _apply_false_positive_guards(scores, text)

    return {
        language: scores[language]
        for language in sorted(scores)
        if scores[language] > 0
    }


def detect_language_from_content(
    path: Path | str,
    content_sample: str | bytes | None,
) -> Optional[str]:
    """Infer a language from conservative content scores."""

    scores = detect_language_content_scores(path, content_sample)
    if not scores:
        return None

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_language, best_score = ranked[0]

    if best_score < CONTENT_LANGUAGE_MIN_SCORE:
        return None

    if len(ranked) > 1:
        _, second_score = ranked[1]
        if best_score - second_score < CONTENT_LANGUAGE_MIN_MARGIN:
            return None

    return best_language


def detect_language(
    path: Path | str,
    content_sample: str | bytes | None = None,
) -> Optional[str]:
    """
    Infer a file's language from shebang, extension, filename, and content.

    Clear shebangs win first. Known extensions and known extensionless
    filenames stay stable to avoid reclassifying Markdown, JSON, YAML, or
    project metadata because of embedded examples. Content heuristics decide
    only when filename/extension are unknown or intentionally ambiguous.
    """
    shebang_language = detect_language_from_shebang(content_sample)
    if shebang_language is not None:
        return shebang_language

    extension_language = detect_language_from_extension(path)
    if extension_language is not None:
        return extension_language

    filename_language = detect_language_from_filename(path)
    if filename_language is not None:
        return filename_language

    content_language = detect_language_from_content(path, content_sample)
    if content_language is not None:
        return content_language

    if is_bash_source_file(path, None):
        return "bash"

    return None

SOURCE_CODE_LANGUAGES = frozenset({
    "bash",
    "c",
    "cpp",
    "csharp",
    "css",
    "html",
    "java",
    "javascript",
    "jsx",
    "python",
    "tsx",
    "typescript",
})


def is_source_code_language(language: str | None) -> bool:
    """Return True when a detected language represents source code.

    This helper classifies central language-detection labels instead of
    maintaining another file-extension list.
    """
    return language in SOURCE_CODE_LANGUAGES


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
    detected_language = detect_language(relative_file_path)

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
            detected_language = detect_language(relative_file_path, content)
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
