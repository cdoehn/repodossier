"""Regression tests for RepoDossier's central language detection API."""

from __future__ import annotations

from pathlib import Path

import pytest

from repodossier.scanner import (
    detect_language,
    detect_language_from_extension,
    detect_language_from_filename,
    scan_single_file,
)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("src/example.py", "python"),
        ("scripts/deploy.sh", "bash"),
        ("scripts/deploy.bash", "bash"),
        ("README.md", "markdown"),
        ("notes.txt", "text"),
        ("package.json", "json"),
        ("config.yaml", "yaml"),
        ("config.yml", "yaml"),
        ("pyproject.toml", "toml"),
        ("tox.ini", "ini"),
        ("setup.cfg", "ini"),
    ],
)
def test_detect_language_preserves_existing_extension_labels(
    path: str,
    expected: str,
) -> None:
    assert detect_language(path) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("README", "markdown"),
        ("readme", "markdown"),
        ("LICENSE", "text"),
        ("LICENCE", "text"),
        ("COPYING", "text"),
        ("CHANGELOG", "markdown"),
        ("TODO", "text"),
        ("Makefile", "makefile"),
        ("Dockerfile", "dockerfile"),
    ],
)
def test_detect_language_preserves_existing_extensionless_filename_labels(
    path: str,
    expected: str,
) -> None:
    assert detect_language(path) == expected


def test_detect_language_keeps_unknown_extension_conservative() -> None:
    assert detect_language("archive.zip") is None
    assert detect_language("data.unknown") is None


def test_detect_language_keeps_unknown_extensionless_text_conservative() -> None:
    assert detect_language(Path("notes/overview"), "plain text without strong signals") is None


def test_detect_language_uses_content_sample_for_existing_bash_shebang() -> None:
    assert detect_language("deploy", "#!/usr/bin/env bash\nset -euo pipefail\n") == "bash"
    assert detect_language("run", "#!/bin/sh\necho hello\n") == "bash"


def test_scan_single_file_uses_central_language_detection_for_bash_shebang(
    tmp_path: Path,
) -> None:
    script = tmp_path / "deploy"
    script.write_text("#!/usr/bin/env bash\nset -e\necho deploy\n", encoding="utf-8")

    info = scan_single_file(tmp_path, script.relative_to(tmp_path))

    assert info.is_text is True
    assert info.is_binary is False
    assert info.language == "bash"


def test_compatibility_language_helpers_remain_available() -> None:
    assert detect_language_from_extension("script.py") == "python"
    assert detect_language_from_extension("notes.txt") == "text"
    assert detect_language_from_extension("archive.zip") is None

    assert detect_language_from_filename("README") == "markdown"
    assert detect_language_from_filename("LICENSE") == "text"
    assert detect_language_from_filename("README.md") is None
