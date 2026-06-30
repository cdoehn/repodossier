"""Integration tests for split exports written via atomic Path.replace."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from repocontext.cli_split import enable_split_write_interceptor_for_args


@pytest.mark.parametrize(
    ("command", "output_name", "part_prefix"),
    [
        ("full", "full.txt", "full"),
        ("export-ai", "ai.txt", "ai"),
        ("export-docs", "docs.txt", "docs"),
    ],
)
def test_split_interceptor_handles_atomic_replace_writes(
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
        temporary_output_path = tmp_path / f".{output_name}.tmp"
        final_output_path = tmp_path / output_name

        temporary_output_path.write_text("abcdefghij", encoding="utf-8")
        temporary_output_path.replace(final_output_path)
    finally:
        if restore is not None:
            restore()

    assert final_output_path.read_text(encoding="utf-8") == "abcdefghij"
    assert not (tmp_path / f".{output_name}.tmp").exists()
    assert (tmp_path / f"{part_prefix}.part01.txt").read_text(encoding="utf-8").endswith("abcd")
    assert (tmp_path / f"{part_prefix}.part02.txt").read_text(encoding="utf-8").endswith("efgh")
    assert (tmp_path / f"{part_prefix}.part03.txt").read_text(encoding="utf-8").endswith("ij")


def test_atomic_replace_split_removes_stale_part_files(tmp_path: Path) -> None:
    stale_part = tmp_path / "docs.part03.txt"
    stale_part.write_text("stale", encoding="utf-8")

    args = SimpleNamespace(
        command="export-docs",
        output="docs.txt",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        temporary_output_path = tmp_path / ".docs.txt.tmp"
        final_output_path = tmp_path / "docs.txt"

        temporary_output_path.write_text("abcd", encoding="utf-8")
        temporary_output_path.replace(final_output_path)
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "docs.part01.txt").exists()
    assert (tmp_path / "docs.part02.txt").exists()
    assert not stale_part.exists()


def test_atomic_replace_split_does_not_split_unrelated_final_names(tmp_path: Path) -> None:
    args = SimpleNamespace(
        command="export-ai",
        output="ai.txt",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        temporary_output_path = tmp_path / ".full.txt.tmp"
        final_output_path = tmp_path / "full.txt"

        temporary_output_path.write_text("abcdef", encoding="utf-8")
        temporary_output_path.replace(final_output_path)
    finally:
        if restore is not None:
            restore()

    assert final_output_path.read_text(encoding="utf-8") == "abcdef"
    assert not list(tmp_path.glob("full.part*.txt"))
    assert not list(tmp_path.glob("ai.part*.txt"))
