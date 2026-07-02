"""Shared language label helpers for RepoDossier exports."""

from __future__ import annotations


_DISPLAY_LANGUAGE_NAMES = {
    "python": "Python",
    "bash": "Bash",
    "shell": "Bash",
    "markdown": "Markdown",
    "toml": "TOML",
    "yaml": "YAML",
    "json": "JSON",
    "ini": "INI",
    "typescript": "TypeScript",
    "tsx": "TSX",
    "javascript": "JavaScript",
    "jsx": "JSX",
    "html": "HTML",
    "css": "CSS",
    "java": "Java",
    "c": "C",
    "cpp": "C++",
    "csharp": "C#",
    "sql": "SQL",
    "text": "Text",
    "unknown": "Unknown",
    "makefile": "Makefile",
    "dockerfile": "Dockerfile",
}


_CODE_FENCE_LANGUAGES = {
    "python": "python",
    "bash": "bash",
    "shell": "bash",
    "markdown": "markdown",
    "toml": "toml",
    "yaml": "yaml",
    "json": "json",
    "ini": "ini",
    "typescript": "typescript",
    "tsx": "tsx",
    "javascript": "javascript",
    "jsx": "jsx",
    "html": "html",
    "css": "css",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "csharp": "csharp",
    "sql": "sql",
    "text": "text",
    "makefile": "makefile",
    "dockerfile": "dockerfile",
}


def normalize_language(language: str | None) -> str:
    """Return a normalized language key used by export label helpers."""

    return (language or "unknown").strip().lower() or "unknown"


def display_language_name(language: str | None) -> str:
    """Return a human-readable language name for summaries."""

    normalized_language = normalize_language(language)
    return _DISPLAY_LANGUAGE_NAMES.get(normalized_language, normalized_language.title())


def code_fence_language(language: str | None) -> str:
    """Return a Markdown code fence language for source blocks."""

    normalized_language = normalize_language(language)
    return _CODE_FENCE_LANGUAGES.get(normalized_language, "text")
