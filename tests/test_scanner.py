"""Focused tests for repocontext.scanner behaviors from task 2.3.c."""
from pathlib import Path

import pytest

from repocontext.models import FileInfo
from repocontext.scanner import (
    detect_language_from_extension,
    is_binary_file,
    is_text_file,
    scan_multiple_files,
    scan_single_file,
)


def test_is_text_file_returns_true_for_utf8_text(tmp_path: Path) -> None:
    text_file = tmp_path / "example.txt"
    text_file.write_text("Hello, RepoContext!")

    assert is_text_file(text_file) is True


def test_is_text_file_returns_false_for_invalid_utf8_bytes(tmp_path: Path) -> None:
    binary_file = tmp_path / "invalid.bin"
    binary_file.write_bytes(b"\xff\xfe\xfa")

    assert is_text_file(binary_file) is False


def test_is_binary_file_returns_true_with_null_byte(tmp_path: Path) -> None:
    binary_file = tmp_path / "has_null.bin"
    binary_file.write_bytes(b"abc\x00def")

    assert is_binary_file(binary_file) is True


def test_is_binary_file_returns_false_for_text_file(tmp_path: Path) -> None:
    text_file = tmp_path / "plain.txt"
    text_file.write_text("Just some ordinary text.")

    assert is_binary_file(text_file) is False


def test_scan_single_file_classifies_text_file(tmp_path: Path) -> None:
    text_file = tmp_path / "sample.txt"
    text_file.write_text("Readable UTF-8 content.")

    info = scan_single_file(tmp_path, text_file.relative_to(tmp_path))

    assert info.is_text is True
    assert info.is_binary is False


def test_scan_single_file_classifies_binary_file(tmp_path: Path) -> None:
    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b"\x00\xff\x01")

    info = scan_single_file(tmp_path, binary_file.relative_to(tmp_path))

    assert info.is_text is False
    assert info.is_binary is True


def test_scan_single_file_detects_extensionless_text(tmp_path: Path) -> None:
    text_file = tmp_path / "README"
    text_file.write_text("Extensionless but valid UTF-8 text.")

    info = scan_single_file(tmp_path, text_file.relative_to(tmp_path))

    assert info.is_text is True
    assert info.is_binary is False


def test_scan_single_file_with_absolute_relative_path_raises_value_error(
    tmp_path: Path,
) -> None:
    text_file = tmp_path / "absolute.txt"
    text_file.write_text("Content does not matter.")

    with pytest.raises(ValueError):
        scan_single_file(tmp_path, text_file)


def test_scan_single_file_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        scan_single_file(tmp_path, Path("missing.txt"))


def test_scan_multiple_files_preserves_order(tmp_path: Path) -> None:
    file_names = ["first.txt", "second.txt", "third.txt"]
    for name in file_names:
        (tmp_path / name).write_text(f"Contents for {name}")

    relative_paths = [Path(name) for name in file_names]
    results = scan_multiple_files(tmp_path, relative_paths)

    assert [info.relative_path.name for info in results] == file_names
    assert all(isinstance(info, FileInfo) for info in results)


def test_detect_language_from_extension_case_insensitive() -> None:
    assert detect_language_from_extension("SCRIPT.PY") == "python"
    assert detect_language_from_extension("notes.TXT") == "text"


def test_detect_language_from_extension_yaml_aliases() -> None:
    assert detect_language_from_extension("config.yaml") == "yaml"
    assert detect_language_from_extension("config.yml") == "yaml"


def test_detect_language_from_extension_unknown_extension() -> None:
    assert detect_language_from_extension("archive.zip") is None


def test_detect_language_from_extension_without_extension() -> None:
    assert detect_language_from_extension("LICENSE") is None
