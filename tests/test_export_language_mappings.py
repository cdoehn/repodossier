from __future__ import annotations

import pytest

from repodossier.languages import code_fence_language, display_language_name, normalize_language


@pytest.mark.parametrize(
    ("language", "expected_display", "expected_fence"),
    [
        ("python", "Python", "python"),
        ("bash", "Bash", "bash"),
        ("shell", "Bash", "bash"),
        ("markdown", "Markdown", "markdown"),
        ("toml", "TOML", "toml"),
        ("yaml", "YAML", "yaml"),
        ("json", "JSON", "json"),
        ("ini", "INI", "ini"),
        ("typescript", "TypeScript", "typescript"),
        ("tsx", "TSX", "tsx"),
        ("javascript", "JavaScript", "javascript"),
        ("jsx", "JSX", "jsx"),
        ("html", "HTML", "html"),
        ("css", "CSS", "css"),
        ("java", "Java", "java"),
        ("c", "C", "c"),
        ("cpp", "C++", "cpp"),
        ("csharp", "C#", "csharp"),
        ("sql", "SQL", "sql"),
        ("text", "Text", "text"),
        ("makefile", "Makefile", "makefile"),
        ("dockerfile", "Dockerfile", "dockerfile"),
    ],
)
def test_export_language_mappings_are_shared(
    language: str,
    expected_display: str,
    expected_fence: str,
) -> None:
    assert display_language_name(language) == expected_display
    assert code_fence_language(language) == expected_fence


def test_export_language_mapping_normalizes_blank_or_missing_values() -> None:
    assert normalize_language(None) == "unknown"
    assert normalize_language("") == "unknown"
    assert normalize_language("  TypeScript  ") == "typescript"


def test_export_language_mapping_falls_back_conservatively() -> None:
    assert display_language_name("customlang") == "Customlang"
    assert code_fence_language("customlang") == "text"
