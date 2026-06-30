from pathlib import Path

import pytest

from repodossier.output_writer import (
    ExportWriteResult,
    build_part_header,
    part_path_for,
    write_export_output,
)
from repodossier.split_config import SplitExportConfig


def test_write_export_output_writes_single_file_without_split(tmp_path):
    output_path = tmp_path / "full.txt"

    result = write_export_output(output_path, "complete export")

    assert result == ExportWriteResult(output_path=output_path, part_paths=())
    assert output_path.read_text(encoding="utf-8") == "complete export"
    assert list(tmp_path.glob("full.part*.txt")) == []


def test_write_export_output_creates_parent_directories(tmp_path):
    output_path = tmp_path / "nested" / "full.txt"

    write_export_output(output_path, "complete export")

    assert output_path.read_text(encoding="utf-8") == "complete export"


def test_write_export_output_writes_main_file_and_part_files_with_split(tmp_path):
    output_path = tmp_path / "full.txt"
    text = "# A\n12345\n# B\n67890\n"

    result = write_export_output(
        output_path,
        text,
        SplitExportConfig(enabled=True, max_chars=10, strategy="heading"),
    )

    assert output_path.read_text(encoding="utf-8") == text
    assert [path.name for path in result.part_paths] == [
        "full.part01.txt",
        "full.part02.txt",
    ]
    assert all(path.exists() for path in result.part_paths)
    assert result.part_paths[0].read_text(encoding="utf-8").startswith(
        "# RepoDossier Export Part 1/2\n\n"
        "Source export: full.txt\n"
        "Part: 1 of 2\n\n"
    )


def test_write_export_output_accepts_mapping_split_config(tmp_path):
    output_path = tmp_path / "ai.txt"

    result = write_export_output(
        output_path,
        "abcdef",
        {"enabled": True, "max_chars": 2, "strategy": "plain"},
    )

    assert [path.name for path in result.part_paths] == [
        "ai.part01.txt",
        "ai.part02.txt",
        "ai.part03.txt",
    ]


def test_write_export_output_removes_stale_part_files_before_split(tmp_path):
    output_path = tmp_path / "docs.txt"
    stale = tmp_path / "docs.part03.txt"
    stale.write_text("stale", encoding="utf-8")

    result = write_export_output(
        output_path,
        "abcd",
        SplitExportConfig(enabled=True, max_chars=2, strategy="plain"),
    )

    assert [path.name for path in result.part_paths] == [
        "docs.part01.txt",
        "docs.part02.txt",
    ]
    assert not stale.exists()


def test_write_export_output_removes_stale_part_files_when_split_disabled(tmp_path):
    output_path = tmp_path / "changed.txt"
    stale = tmp_path / "changed.part01.txt"
    stale.write_text("stale", encoding="utf-8")

    result = write_export_output(output_path, "new text")

    assert result.part_paths == ()
    assert output_path.read_text(encoding="utf-8") == "new text"
    assert not stale.exists()


def test_write_export_output_does_not_remove_unrelated_files(tmp_path):
    output_path = tmp_path / "full.txt"
    unrelated = tmp_path / "other.part01.txt"
    unrelated.write_text("keep", encoding="utf-8")

    write_export_output(
        output_path,
        "abcd",
        SplitExportConfig(enabled=True, max_chars=2, strategy="plain"),
    )

    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_write_export_output_uses_sortable_part_names_above_99_parts(tmp_path):
    output_path = tmp_path / "large.txt"

    result = write_export_output(
        output_path,
        "x" * 101,
        SplitExportConfig(enabled=True, max_chars=1, strategy="plain"),
    )

    assert result.part_paths[0].name == "large.part001.txt"
    assert result.part_paths[98].name == "large.part099.txt"
    assert result.part_paths[99].name == "large.part100.txt"


def test_part_path_for_handles_extensionless_output_paths(tmp_path):
    output_path = tmp_path / "export"

    assert part_path_for(output_path, 1, 2) == tmp_path / "export.part01"


def test_build_part_header_returns_expected_header():
    assert build_part_header("full.txt", 2, 3) == (
        "# RepoDossier Export Part 2/3\n\n"
        "Source export: full.txt\n"
        "Part: 2 of 3\n\n"
    )


@pytest.mark.parametrize(
    "part_number,total_parts",
    [
        (0, 1),
        (1, 0),
        (2, 1),
    ],
)
def test_build_part_header_rejects_invalid_numbers(part_number, total_parts):
    with pytest.raises(ValueError):
        build_part_header("full.txt", part_number, total_parts)


def test_write_export_output_rejects_non_string_text(tmp_path):
    with pytest.raises(TypeError, match="text"):
        write_export_output(tmp_path / "full.txt", 123)
