from pathlib import Path
from types import SimpleNamespace

from repocontext.cli_split import enable_split_write_interceptor_for_args
from repocontext.split_config import SplitExportConfig


def test_full_command_split_interceptor_writes_full_part_files(tmp_path):
    args = SimpleNamespace(
        command="full",
        split_enabled=True,
        split_max_chars=4,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        output_path = tmp_path / "full.txt"
        output_path.write_text("abcdefghij", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert output_path.read_text(encoding="utf-8") == "abcdefghij"
    assert (tmp_path / "full.part01.txt").read_text(encoding="utf-8").endswith("abcd")
    assert (tmp_path / "full.part02.txt").read_text(encoding="utf-8").endswith("efgh")
    assert (tmp_path / "full.part03.txt").read_text(encoding="utf-8").endswith("ij")


def test_full_command_split_interceptor_removes_stale_parts(tmp_path):
    stale_path = tmp_path / "full.part03.txt"
    stale_path.write_text("stale", encoding="utf-8")

    args = SimpleNamespace(
        command="full",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "full.txt").write_text("abcd", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "full.part01.txt").exists()
    assert (tmp_path / "full.part02.txt").exists()
    assert not stale_path.exists()


def test_full_command_split_interceptor_ignores_ai_file_written_by_full_command(tmp_path):
    args = SimpleNamespace(
        command="full",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "ai.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert not list(tmp_path.glob("ai.part*.txt"))


def test_full_command_split_interceptor_is_disabled_for_other_commands(tmp_path):
    args = SimpleNamespace(
        command="export-ai",
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
    assert not list(tmp_path.glob("full.part*.txt"))


def test_full_command_split_interceptor_uses_base_config_when_cli_has_no_override(tmp_path):
    args = SimpleNamespace(
        command="full",
        split_enabled=None,
        split_max_chars=None,
        split_strategy=None,
    )
    base_config = SplitExportConfig(enabled=True, max_chars=3, strategy="plain")

    restore = enable_split_write_interceptor_for_args(args, base_config=base_config)

    try:
        (tmp_path / "full.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "full.part01.txt").read_text(encoding="utf-8").endswith("abc")
    assert (tmp_path / "full.part02.txt").read_text(encoding="utf-8").endswith("def")


def test_cli_main_enables_split_interceptor_after_parse_args():
    import repocontext.cli as cli

    assert cli.__file__ is not None
    source = Path(cli.__file__).read_text(encoding="utf-8")

    assert "arguments = parser.parse_args(list(argv) if argv is not None else None)" in source
    assert "enable_split_write_interceptor_for_args(arguments)" in source
