"""Milestone 16 acceptance tests for split exports."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from repodossier.cli_split import enable_split_write_interceptor_for_args
from repodossier.split_config import SplitExportConfig


@pytest.mark.parametrize(
    ("command", "output_name", "part_prefix"),
    [
        ("full", "full.txt", "full"),
        ("export-ai", "ai.txt", "ai"),
        ("export-docs", "docs.txt", "docs"),
        ("changed", "changed.txt", "changed"),
    ],
)
def test_supported_exports_keep_complete_file_and_write_split_parts(
    tmp_path: Path,
    command: str,
    output_name: str,
    part_prefix: str,
) -> None:
    args = SimpleNamespace(
        command=command,
        output=output_name,
        split_enabled=True,
        split_max_chars=4,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        output_path = tmp_path / output_name
        output_path.write_text("abcdefghij", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert output_path.read_text(encoding="utf-8") == "abcdefghij"
    assert (tmp_path / f"{part_prefix}.part01.txt").read_text(encoding="utf-8").endswith("abcd")
    assert (tmp_path / f"{part_prefix}.part02.txt").read_text(encoding="utf-8").endswith("efgh")
    assert (tmp_path / f"{part_prefix}.part03.txt").read_text(encoding="utf-8").endswith("ij")


@pytest.mark.parametrize(
    ("command", "output_name", "part_prefix"),
    [
        ("full", "full.txt", "full"),
        ("export-ai", "ai.txt", "ai"),
        ("export-docs", "docs.txt", "docs"),
        ("changed", "changed.txt", "changed"),
    ],
)
def test_no_split_cli_override_disables_parts_even_when_config_enables_split(
    tmp_path: Path,
    command: str,
    output_name: str,
    part_prefix: str,
) -> None:
    args = SimpleNamespace(
        command=command,
        output=output_name,
        split_enabled=False,
        split_max_chars=None,
        split_strategy=None,
    )
    base_config = SplitExportConfig(enabled=True, max_chars=2, strategy="plain")

    restore = enable_split_write_interceptor_for_args(args, base_config=base_config)

    try:
        (tmp_path / output_name).write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert restore is None
    assert not list(tmp_path.glob(f"{part_prefix}.part*.txt"))


@pytest.mark.parametrize(
    ("command", "output_name", "part_prefix"),
    [
        ("full", "full.txt", "full"),
        ("export-ai", "ai.txt", "ai"),
        ("export-docs", "docs.txt", "docs"),
        ("changed", "changed.txt", "changed"),
    ],
)
def test_split_config_enables_parts_when_cli_has_no_override(
    tmp_path: Path,
    command: str,
    output_name: str,
    part_prefix: str,
) -> None:
    args = SimpleNamespace(
        command=command,
        output=output_name,
        split_enabled=None,
        split_max_chars=None,
        split_strategy=None,
    )
    base_config = SplitExportConfig(enabled=True, max_chars=3, strategy="plain")

    restore = enable_split_write_interceptor_for_args(args, base_config=base_config)

    try:
        (tmp_path / output_name).write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / f"{part_prefix}.part01.txt").read_text(encoding="utf-8").endswith("abc")
    assert (tmp_path / f"{part_prefix}.part02.txt").read_text(encoding="utf-8").endswith("def")


def test_changed_split_uses_custom_output_basename_for_part_files(tmp_path: Path) -> None:
    args = SimpleNamespace(
        command="changed",
        output="review-changes.txt",
        split_enabled=True,
        split_max_chars=3,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "review-changes.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "review-changes.part01.txt").read_text(encoding="utf-8").endswith("abc")
    assert (tmp_path / "review-changes.part02.txt").read_text(encoding="utf-8").endswith("def")
    assert not list(tmp_path.glob("changed.part*.txt"))


def test_split_export_removes_stale_part_files_before_writing_new_parts(tmp_path: Path) -> None:
    stale_part = tmp_path / "ai.part03.txt"
    stale_part.write_text("stale", encoding="utf-8")

    args = SimpleNamespace(
        command="export-ai",
        output="ai.txt",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "ai.txt").write_text("abcd", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "ai.part01.txt").exists()
    assert (tmp_path / "ai.part02.txt").exists()
    assert not stale_part.exists()


def test_split_interceptor_does_not_split_unrelated_export_files(tmp_path: Path) -> None:
    args = SimpleNamespace(
        command="export-docs",
        output="docs.txt",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "full.txt").write_text("abcdef", encoding="utf-8")
        (tmp_path / "ai.txt").write_text("abcdef", encoding="utf-8")
        (tmp_path / "changed.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert not list(tmp_path.glob("full.part*.txt"))
    assert not list(tmp_path.glob("ai.part*.txt"))
    assert not list(tmp_path.glob("changed.part*.txt"))


def test_non_export_commands_do_not_enable_split_interceptor(tmp_path: Path) -> None:
    args = SimpleNamespace(
        command="info",
        output=None,
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "full.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert restore is None
    assert not list(tmp_path.glob("*.part*.txt"))


def test_split_parts_are_additional_and_do_not_replace_main_export(tmp_path: Path) -> None:
    args = SimpleNamespace(
        command="full",
        output="full.txt",
        split_enabled=True,
        split_max_chars=5,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        output_path = tmp_path / "full.txt"
        output_path.write_text("abcdefghij", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "abcdefghij"
    assert (tmp_path / "full.part01.txt").exists()
    assert (tmp_path / "full.part02.txt").exists()
