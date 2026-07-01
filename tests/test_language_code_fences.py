"""Tests for Markdown code fence language mapping."""

from __future__ import annotations

import pytest

from repodossier.exporters.full import _code_fence_language


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("python", "python"),
        ("bash", "bash"),
        ("markdown", "markdown"),
        ("toml", "toml"),
        ("yaml", "yaml"),
        ("json", "json"),
        ("ini", "ini"),
        ("typescript", "typescript"),
        ("tsx", "tsx"),
        ("javascript", "javascript"),
        ("jsx", "jsx"),
        ("html", "html"),
        ("css", "css"),
        ("java", "java"),
        ("c", "c"),
        ("cpp", "cpp"),
        ("csharp", "csharp"),
        ("text", "text"),
        ("makefile", "makefile"),
        ("dockerfile", "dockerfile"),
    ],
)
def test_code_fence_language_maps_supported_language_labels(
    language: str,
    expected: str,
) -> None:
    assert _code_fence_language(language) == expected


@pytest.mark.parametrize("language", [None, "", "unknown", "not-a-language"])
def test_code_fence_language_falls_back_to_text_for_unknown_labels(
    language: str | None,
) -> None:
    assert _code_fence_language(language) == "text"
