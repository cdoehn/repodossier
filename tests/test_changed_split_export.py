import argparse
from types import SimpleNamespace

from repocontext.changed_command import add_changed_subparser
from repocontext.cli_split import enable_split_write_interceptor_for_args
from repocontext.split_config import SplitExportConfig


def test_changed_command_split_interceptor_writes_changed_part_files(tmp_path):
    args = SimpleNamespace(
        command="changed",
        output="changed.txt",
        split_enabled=True,
        split_max_chars=4,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        output_path = tmp_path / "changed.txt"
        output_path.write_text("abcdefghij", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert output_path.read_text(encoding="utf-8") == "abcdefghij"
    assert (tmp_path / "changed.part01.txt").read_text(encoding="utf-8").endswith("abcd")
    assert (tmp_path / "changed.part02.txt").read_text(encoding="utf-8").endswith("efgh")
    assert (tmp_path / "changed.part03.txt").read_text(encoding="utf-8").endswith("ij")


def test_changed_command_split_interceptor_removes_stale_changed_parts(tmp_path):
    stale_path = tmp_path / "changed.part03.txt"
    stale_path.write_text("stale", encoding="utf-8")

    args = SimpleNamespace(
        command="changed",
        output="changed.txt",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "changed.txt").write_text("abcd", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "changed.part01.txt").exists()
    assert (tmp_path / "changed.part02.txt").exists()
    assert not stale_path.exists()


def test_changed_command_split_interceptor_uses_custom_output_name(tmp_path):
    args = SimpleNamespace(
        command="changed",
        output="review-changes.txt",
        split_enabled=True,
        split_max_chars=3,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        output_path = tmp_path / "review-changes.txt"
        output_path.write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "review-changes.part01.txt").read_text(encoding="utf-8").endswith("abc")
    assert (tmp_path / "review-changes.part02.txt").read_text(encoding="utf-8").endswith("def")
    assert not list(tmp_path.glob("changed.part*.txt"))


def test_changed_command_split_interceptor_does_not_split_other_exports(tmp_path):
    args = SimpleNamespace(
        command="changed",
        output="changed.txt",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "full.txt").write_text("abcdef", encoding="utf-8")
        (tmp_path / "ai.txt").write_text("abcdef", encoding="utf-8")
        (tmp_path / "docs.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert not list(tmp_path.glob("full.part*.txt"))
    assert not list(tmp_path.glob("ai.part*.txt"))
    assert not list(tmp_path.glob("docs.part*.txt"))


def test_changed_command_split_interceptor_uses_base_config_when_cli_has_no_override(tmp_path):
    args = SimpleNamespace(
        command="changed",
        output="changed.txt",
        split_enabled=None,
        split_max_chars=None,
        split_strategy=None,
    )
    base_config = SplitExportConfig(enabled=True, max_chars=3, strategy="plain")

    restore = enable_split_write_interceptor_for_args(args, base_config=base_config)

    try:
        (tmp_path / "changed.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "changed.part01.txt").read_text(encoding="utf-8").endswith("abc")
    assert (tmp_path / "changed.part02.txt").read_text(encoding="utf-8").endswith("def")


def test_changed_subparser_accepts_split_cli_options():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_changed_subparser(subparsers)

    args = parser.parse_args(
        [
            "changed",
            "--split",
            "--split-max-chars",
            "123",
            "--split-strategy",
            "plain",
        ]
    )

    assert args.command == "changed"
    assert args.split_enabled is True
    assert args.split_max_chars == 123
    assert args.split_strategy == "plain"


def test_changed_subparser_accepts_no_split_cli_option():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_changed_subparser(subparsers)

    args = parser.parse_args(["changed", "--no-split"])

    assert args.command == "changed"
    assert args.split_enabled is False
