from dataclasses import dataclass

import pytest

from repodossier.export_model_adapters import (
    file_entries_from_mappings,
    file_entries_from_objects,
    file_entry_from_mapping,
    file_entry_from_object,
)


def test_file_entry_from_mapping_accepts_basic_payload():
    entry = file_entry_from_mapping(
        {
            "path": "./src\\app.py",
            "language": "python",
            "content": "print('hello')\n",
        }
    )

    assert entry.path == "src/app.py"
    assert entry.language == "python"
    assert entry.content == "print('hello')\n"
    assert entry.status == "included"
    assert entry.text_status == "text"
    assert entry.line_count == 1
    assert entry.size_bytes == len("print('hello')\n".encode("utf-8"))


def test_file_entry_from_mapping_accepts_legacy_key_names():
    entry = file_entry_from_mapping(
        {
            "relative_path": "README.md",
            "lang": "markdown",
            "text": "# Hello",
            "tokens": "10",
            "lines": "1",
            "bytes": "7",
        }
    )

    assert entry.path == "README.md"
    assert entry.language == "markdown"
    assert entry.content == "# Hello"
    assert entry.estimated_tokens == 10
    assert entry.line_count == 1
    assert entry.size_bytes == 7


def test_file_entry_from_mapping_prefers_masked_content_and_status_flags():
    entry = file_entry_from_mapping(
        {
            "file_path": "config.env",
            "language": "text",
            "content": "TOKEN=secret",
            "redacted_content": "TOKEN=***",
            "truncated": True,
            "skip_reason": "limit reached",
        }
    )

    assert entry.path == "config.env"
    assert entry.status == "truncated"
    assert entry.masked_content == "TOKEN=***"
    assert entry.rendered_content == "TOKEN=***"
    assert entry.reason == "limit reached"


def test_file_entry_from_mapping_detects_binary_and_error_payloads():
    binary = file_entry_from_mapping(
        {
            "path": "assets/logo.png",
            "binary": True,
            "skipped": True,
            "size": 123,
        }
    )
    errored = file_entry_from_mapping(
        {
            "path": "broken.txt",
            "error": "failed to read",
            "language": "text",
        }
    )

    assert binary.text_status == "binary"
    assert binary.status == "skipped"
    assert binary.size_bytes == 123

    assert errored.status == "error"
    assert errored.reason == "failed to read"


def test_file_entry_from_mapping_rejects_missing_path():
    with pytest.raises(ValueError, match="must include a path"):
        file_entry_from_mapping({"language": "python"})


def test_file_entries_from_mappings_returns_entries_sorted_by_path():
    entries = file_entries_from_mappings(
        (
            {"path": "b.py", "language": "python"},
            {"path": "a.py", "language": "python"},
        )
    )

    assert [entry.path for entry in entries] == ["a.py", "b.py"]


def test_file_entry_from_object_uses_scanner_like_attributes():
    @dataclass
    class LegacyFile:
        relative_path: str
        language: str
        content: str
        estimated_tokens: int

    entry = file_entry_from_object(
        LegacyFile(
            relative_path="src/app.py",
            language="python",
            content="print(1)",
            estimated_tokens=3,
        )
    )

    assert entry.path == "src/app.py"
    assert entry.language == "python"
    assert entry.content == "print(1)"
    assert entry.estimated_tokens == 3


def test_file_entries_from_objects_returns_entries_sorted_by_path():
    @dataclass
    class LegacyFile:
        path: str
        language: str

    entries = file_entries_from_objects(
        (
            LegacyFile(path="z.py", language="python"),
            LegacyFile(path="a.py", language="python"),
        )
    )

    assert [entry.path for entry in entries] == ["a.py", "z.py"]


def test_file_entry_from_mapping_respects_explicit_status_values():
    entry = file_entry_from_mapping(
        {
            "path": "large.py",
            "language": "python",
            "status": "truncated",
            "text_status": "text",
        }
    )

    assert entry.status == "truncated"
    assert entry.text_status == "text"
