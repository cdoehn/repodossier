from repodossier.export_model import FileEntry
from repodossier.export_model_content import (
    content_line_count,
    content_size_bytes,
    estimate_tokens_from_content,
    file_entry_content_for_rendering,
    file_entry_has_exportable_content,
    make_file_entry_from_content,
)


def test_content_line_count_handles_empty_and_trailing_newline_content():
    assert content_line_count(None) == 0
    assert content_line_count("") == 0
    assert content_line_count("one") == 1
    assert content_line_count("one\n") == 1
    assert content_line_count("one\ntwo") == 2
    assert content_line_count("one\n\n") == 2


def test_content_size_bytes_uses_utf8_by_default():
    assert content_size_bytes(None) == 0
    assert content_size_bytes("") == 0
    assert content_size_bytes("abc") == 3
    assert content_size_bytes("ä") == 2


def test_estimate_tokens_from_content_is_deterministic_and_conservative():
    assert estimate_tokens_from_content(None) == 0
    assert estimate_tokens_from_content("") == 0
    assert estimate_tokens_from_content("a") == 1
    assert estimate_tokens_from_content("abcd") == 1
    assert estimate_tokens_from_content("abcde") == 2


def test_file_entry_content_for_rendering_prefers_masked_content():
    entry = FileEntry(
        path="config.env",
        language="text",
        content="TOKEN=secret",
        masked_content="TOKEN=***",
    )

    assert file_entry_content_for_rendering(entry) == "TOKEN=***"
    assert file_entry_has_exportable_content(entry)


def test_file_entry_content_for_rendering_ignores_binary_content():
    entry = FileEntry(
        path="image.png",
        language="unknown",
        text_status="binary",
        content="raw bytes represented as text",
    )

    assert file_entry_content_for_rendering(entry) is None
    assert not file_entry_has_exportable_content(entry)


def test_make_file_entry_from_content_derives_metadata():
    entry = make_file_entry_from_content(
        path="src/app.py",
        language="python",
        content="print('hi')\n",
    )

    assert entry.path == "src/app.py"
    assert entry.language == "python"
    assert entry.size_bytes == len("print('hi')\n".encode("utf-8"))
    assert entry.line_count == 1
    assert entry.estimated_tokens > 0
    assert entry.content == "print('hi')\n"


def test_make_file_entry_from_content_accepts_explicit_metadata():
    entry = make_file_entry_from_content(
        path="large.txt",
        language="text",
        content="hello",
        status="truncated",
        size_bytes=999,
        line_count=123,
        estimated_tokens=456,
        reason="limit reached",
    )

    assert entry.status == "truncated"
    assert entry.size_bytes == 999
    assert entry.line_count == 123
    assert entry.estimated_tokens == 456
    assert entry.reason == "limit reached"
