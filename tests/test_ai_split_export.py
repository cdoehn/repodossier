from types import SimpleNamespace

from repocontext.cli_split import enable_split_write_interceptor_for_args
from repocontext.split_config import SplitExportConfig


def test_ai_command_split_interceptor_writes_ai_part_files(tmp_path):
    args = SimpleNamespace(
        command="export-ai",
        split_enabled=True,
        split_max_chars=4,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        output_path = tmp_path / "ai.txt"
        output_path.write_text("abcdefghij", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert output_path.read_text(encoding="utf-8") == "abcdefghij"
    assert (tmp_path / "ai.part01.txt").read_text(encoding="utf-8").endswith("abcd")
    assert (tmp_path / "ai.part02.txt").read_text(encoding="utf-8").endswith("efgh")
    assert (tmp_path / "ai.part03.txt").read_text(encoding="utf-8").endswith("ij")


def test_ai_command_split_interceptor_removes_stale_ai_parts(tmp_path):
    stale_path = tmp_path / "ai.part03.txt"
    stale_path.write_text("stale", encoding="utf-8")

    args = SimpleNamespace(
        command="export-ai",
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
    assert not stale_path.exists()


def test_ai_command_split_interceptor_does_not_split_full_file(tmp_path):
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

    assert not list(tmp_path.glob("full.part*.txt"))


def test_ai_command_split_interceptor_uses_base_config_when_cli_has_no_override(tmp_path):
    args = SimpleNamespace(
        command="export-ai",
        split_enabled=None,
        split_max_chars=None,
        split_strategy=None,
    )
    base_config = SplitExportConfig(enabled=True, max_chars=3, strategy="plain")

    restore = enable_split_write_interceptor_for_args(args, base_config=base_config)

    try:
        (tmp_path / "ai.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "ai.part01.txt").read_text(encoding="utf-8").endswith("abc")
    assert (tmp_path / "ai.part02.txt").read_text(encoding="utf-8").endswith("def")


def test_full_command_still_only_splits_full_export(tmp_path):
    args = SimpleNamespace(
        command="full",
        split_enabled=True,
        split_max_chars=2,
        split_strategy="plain",
    )

    restore = enable_split_write_interceptor_for_args(args)

    try:
        (tmp_path / "full.txt").write_text("abcd", encoding="utf-8")
        (tmp_path / "ai.txt").write_text("abcdef", encoding="utf-8")
    finally:
        if restore is not None:
            restore()

    assert (tmp_path / "full.part01.txt").exists()
    assert (tmp_path / "full.part02.txt").exists()
    assert not list(tmp_path.glob("ai.part*.txt"))
