"""Focused tests for repocontext.scanner behaviors from task 2.3.c."""
from pathlib import Path

import pytest

from repocontext.models import FileInfo
from repocontext.scanner import (
    count_empty_lines,
    count_python_comment_lines,
    count_shell_comment_lines,
    count_total_lines,
    detect_language_from_extension,
    detect_language_from_filename,
    estimate_tokens,
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


def test_count_empty_lines_returns_zero_for_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    assert count_empty_lines(file_path) == 0


def test_count_empty_lines_returns_zero_when_no_empty_lines(tmp_path: Path) -> None:
    file_path = tmp_path / "no_empty.txt"
    file_path.write_text("line one\nline two\nline three")

    assert count_empty_lines(file_path) == 0


def test_count_empty_lines_counts_blank_lines(tmp_path: Path) -> None:
    file_path = tmp_path / "blank_lines.txt"
    file_path.write_text("line one\n\nline three\n\n")

    assert count_empty_lines(file_path) == 2


def test_count_empty_lines_treats_whitespace_only_lines_as_empty(tmp_path: Path) -> None:
    file_path = tmp_path / "whitespace_lines.txt"
    file_path.write_text("line one\n   \n\t\nline four\n")

    assert count_empty_lines(file_path) == 2


def test_count_python_comment_lines_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.py"
    file_path.write_text("")

    assert count_python_comment_lines(file_path) == 0


def test_count_python_comment_lines_only_comments(tmp_path: Path) -> None:
    file_path = tmp_path / "comments.py"
    file_path.write_text("# comment one\n# comment two\n# comment three\n")

    assert count_python_comment_lines(file_path) == 3


def test_count_python_comment_lines_mixed_code_and_comments(tmp_path: Path) -> None:
    file_path = tmp_path / "mixed.py"
    file_path.write_text(
        "# module comment\nprint('hello')\n# trailing comment block\nvalue = 42\n"
    )

    assert count_python_comment_lines(file_path) == 2


def test_count_python_comment_lines_indented_comments(tmp_path: Path) -> None:
    file_path = tmp_path / "indented.py"
    file_path.write_text("    # indented comment\n\t# tab indented comment\n")

    assert count_python_comment_lines(file_path) == 2


def test_count_python_comment_lines_inline_comments_ignored(tmp_path: Path) -> None:
    file_path = tmp_path / "inline.py"
    file_path.write_text("print('value')  # inline comment\nvalue = 10  # still inline\n")

    assert count_python_comment_lines(file_path) == 0


def test_count_python_comment_lines_hash_in_string_ignored(tmp_path: Path) -> None:
    file_path = tmp_path / "strings.py"
    file_path.write_text("print('# not a comment')\n# actual comment\n")

    assert count_python_comment_lines(file_path) == 1


def test_count_shell_comment_lines_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.sh"
    file_path.write_text("")

    assert count_shell_comment_lines(file_path) == 0


def test_count_shell_comment_lines_only_comments(tmp_path: Path) -> None:
    file_path = tmp_path / "comments.sh"
    file_path.write_text("# comment one\n# comment two\n")

    assert count_shell_comment_lines(file_path) == 2


def test_count_shell_comment_lines_mixed_code_and_comments(tmp_path: Path) -> None:
    file_path = tmp_path / "mixed.sh"
    file_path.write_text("# header\necho hello\n# footer\n")

    assert count_shell_comment_lines(file_path) == 2


def test_count_shell_comment_lines_indented_comments(tmp_path: Path) -> None:
    file_path = tmp_path / "indented.sh"
    file_path.write_text("    # indented comment\n\t# tab comment\n")

    assert count_shell_comment_lines(file_path) == 2


def test_count_shell_comment_lines_ignores_shebang(tmp_path: Path) -> None:
    file_path = tmp_path / "script.sh"
    file_path.write_text("#!/usr/bin/env bash\n# real comment\n")

    assert count_shell_comment_lines(file_path) == 1


def test_count_shell_comment_lines_inline_comments_ignored(tmp_path: Path) -> None:
    file_path = tmp_path / "inline.sh"
    file_path.write_text("echo hi # inline comment\nvalue=1 # another inline\n")

    assert count_shell_comment_lines(file_path) == 0


def test_count_shell_comment_lines_hash_in_string_ignored(tmp_path: Path) -> None:
    file_path = tmp_path / "strings.sh"
    file_path.write_text("echo '# not a comment'\n# actual comment\n")

    assert count_shell_comment_lines(file_path) == 1


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


def test_detect_language_from_filename_known_extensionless_names() -> None:
    assert detect_language_from_filename("README") == "markdown"
    assert detect_language_from_filename("LICENSE") == "text"
    assert detect_language_from_filename("LICENCE") == "text"
    assert detect_language_from_filename("COPYING") == "text"
    assert detect_language_from_filename("CHANGELOG") == "markdown"
    assert detect_language_from_filename("TODO") == "text"
    assert detect_language_from_filename("Makefile") == "makefile"
    assert detect_language_from_filename("Dockerfile") == "dockerfile"


def test_detect_language_from_filename_lowercase_variants() -> None:
    assert detect_language_from_filename("readme") == "markdown"
    assert detect_language_from_filename("license") == "text"
    assert detect_language_from_filename(Path("docs/todo")) == "text"


def test_detect_language_from_filename_unknown_name_returns_none() -> None:
    assert detect_language_from_filename("HISTORY") is None
    assert detect_language_from_filename(Path("notes/overview")) is None


def test_detect_language_from_filename_with_extension_returns_none() -> None:
    assert detect_language_from_filename("README.md") is None
    assert detect_language_from_filename("Makefile.txt") is None
    assert detect_language_from_filename(Path("docker/Dockerfile.template")) is None


def test_scan_single_file_language_from_python_extension(tmp_path: Path) -> None:
    file_path = tmp_path / "example.py"
    file_path.write_text("print('hello')")
    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.language == "python"


def test_scan_single_file_language_from_markdown_extension(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.md"
    file_path.write_text("# Notes")
    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.language == "markdown"


def test_scan_single_file_language_from_yaml_extension(tmp_path: Path) -> None:
    file_path = tmp_path / "config.yml"
    file_path.write_text("key: value")
    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.language == "yaml"


def test_scan_single_file_language_from_readme_filename(tmp_path: Path) -> None:
    file_path = tmp_path / "README"
    file_path.write_text("Project overview.")
    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.language == "markdown"


def test_scan_single_file_language_from_license_filename(tmp_path: Path) -> None:
    file_path = tmp_path / "LICENSE"
    file_path.write_text("License text.")
    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.language == "text"


def test_scan_single_file_language_for_unknown_extension_is_none(tmp_path: Path) -> None:
    file_path = tmp_path / "data.unknown"
    file_path.write_text("Unrecognized extension content.")
    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.language is None


def test_count_total_lines_returns_zero_for_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    assert count_total_lines(file_path) == 0


def test_count_total_lines_returns_correct_count_for_multi_line_text_file(tmp_path: Path) -> None:
    file_path = tmp_path / "multi.txt"
    file_path.write_text("first line\nsecond line\nthird line")

    assert count_total_lines(file_path) == 3


def test_scan_single_file_stores_line_count_for_text_file(tmp_path: Path) -> None:
    file_path = tmp_path / "lines.txt"
    file_path.write_text("line one\nline two\n")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.line_count == 2


def test_scan_single_file_stores_empty_line_count_for_text_file(tmp_path: Path) -> None:
    file_path = tmp_path / "lines_with_empty.txt"
    file_path.write_text("line one\n\n   \nline four\n")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.empty_line_count == 2


def test_scan_single_file_populates_line_and_empty_counts_together(tmp_path: Path) -> None:
    file_path = tmp_path / "lines_and_empty.txt"
    file_path.write_text("line one\n\nline three\n")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.line_count == 3
    assert info.empty_line_count == 1


def test_scan_single_file_keeps_line_count_none_for_binary_file(tmp_path: Path) -> None:
    file_path = tmp_path / "binary.bin"
    file_path.write_bytes(b"\x00\x01\x02")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.is_binary is True
    assert info.line_count is None


def test_scan_single_file_keeps_empty_line_count_none_for_binary_file(tmp_path: Path) -> None:
    file_path = tmp_path / "binary_empty.bin"
    file_path.write_bytes(b"\x00\x01\x02")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.is_binary is True
    assert info.empty_line_count is None


def test_scan_single_file_stores_python_comment_line_count(tmp_path: Path) -> None:
    file_path = tmp_path / "module.py"
    file_path.write_text("# module comment\nprint('hello')\n# another comment\n")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.comment_line_count == 2


def test_scan_single_file_stores_shell_comment_line_count(tmp_path: Path) -> None:
    file_path = tmp_path / "script.sh"
    file_path.write_text("#!/usr/bin/env bash\n# script comment\necho hello\n# done\n")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.comment_line_count == 2


def test_scan_single_file_keeps_comment_line_count_none_for_plain_text(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("# not counted as language-specific comment\nplain text\n")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.comment_line_count is None


def test_scan_single_file_keeps_comment_line_count_none_for_binary_file(tmp_path: Path) -> None:
    file_path = tmp_path / "binary.bin"
    file_path.write_bytes(b"\x00\x01\x02")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.comment_line_count is None


def test_scan_multiple_files_populates_line_metrics_for_text_files(tmp_path: Path) -> None:
    file_specs: dict[str, str] = {
        "alpha.txt": "alpha\nbeta\n",
        "beta.txt": "one\n\nthree\n",
    }
    for name, content in file_specs.items():
        (tmp_path / name).write_text(content)

    relative_paths = [Path(name) for name in file_specs]
    results = scan_multiple_files(tmp_path, relative_paths)

    expected_line_counts = [2, 3]
    expected_empty_counts = [0, 1]

    for info, expected_lines, expected_empty in zip(results, expected_line_counts, expected_empty_counts):
        assert info.line_count == expected_lines
        assert info.empty_line_count == expected_empty


def test_scan_multiple_files_keeps_line_metrics_none_for_binary_files(tmp_path: Path) -> None:
    text_file = tmp_path / "plain.txt"
    text_file.write_text("line one\nline two\n")

    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")

    relative_paths = [Path("binary.bin"), Path("plain.txt")]
    results = scan_multiple_files(tmp_path, relative_paths)

    binary_info = results[0]
    assert binary_info.is_binary is True
    assert binary_info.line_count is None
    assert binary_info.empty_line_count is None

    text_info = results[1]
    assert text_info.is_text is True
    assert text_info.line_count == 2
    assert text_info.empty_line_count == 0


def test_scan_single_file_stores_estimated_tokens_for_text_file(tmp_path: Path) -> None:
    file_path = tmp_path / "tokens.txt"
    file_path.write_text("a" * 100)

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.estimated_tokens == 25


def test_scan_single_file_keeps_estimated_tokens_none_for_binary_file(tmp_path: Path) -> None:
    file_path = tmp_path / "binary_tokens.bin"
    file_path.write_bytes(b"\x00\x01\x02")

    info = scan_single_file(tmp_path, file_path.relative_to(tmp_path))

    assert info.is_binary is True
    assert info.estimated_tokens is None


def test_scan_multiple_files_populates_estimated_tokens_for_text_files(tmp_path: Path) -> None:
    first_file = tmp_path / "first.txt"
    second_file = tmp_path / "second.txt"
    first_file.write_text("a" * 8)
    second_file.write_text("b" * 12)

    results = scan_multiple_files(tmp_path, [Path("first.txt"), Path("second.txt")])

    assert [info.estimated_tokens for info in results] == [2, 3]


def test_estimate_tokens_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    assert estimate_tokens(file_path) == 0


def test_estimate_tokens_small_text(tmp_path: Path) -> None:
    file_path = tmp_path / "small.txt"
    file_path.write_text("abcd")

    assert estimate_tokens(file_path) == 1


def test_estimate_tokens_rounds_up(tmp_path: Path) -> None:
    file_path = tmp_path / "rounding.txt"
    file_path.write_text("abcde")

    assert estimate_tokens(file_path) == 2


def test_estimate_tokens_larger_text(tmp_path: Path) -> None:
    file_path = tmp_path / "large.txt"
    file_path.write_text("a" * 100)

    assert estimate_tokens(file_path) == 25
