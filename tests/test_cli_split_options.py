import argparse

import pytest

from repodossier.cli_split import add_split_export_options, resolve_split_export_config
from repodossier.split_config import DEFAULT_SPLIT_MAX_CHARS, SplitExportConfig


def _parse_args(*args):
    parser = argparse.ArgumentParser()
    add_split_export_options(parser)
    return parser.parse_args(list(args))


def test_split_cli_options_default_to_none_for_overrides():
    args = _parse_args()

    assert args.split_enabled is None
    assert args.split_max_chars is None
    assert args.split_strategy is None


def test_split_cli_option_enables_split():
    args = _parse_args("--split")

    assert args.split_enabled is True


def test_no_split_cli_option_disables_split():
    args = _parse_args("--no-split")

    assert args.split_enabled is False


def test_split_and_no_split_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        _parse_args("--split", "--no-split")


def test_split_max_chars_accepts_positive_integer():
    args = _parse_args("--split-max-chars", "12345")

    assert args.split_max_chars == 12345


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_split_max_chars_rejects_invalid_values(value):
    with pytest.raises(SystemExit):
        _parse_args("--split-max-chars", value)


def test_split_strategy_accepts_plain_and_heading():
    assert _parse_args("--split-strategy", "plain").split_strategy == "plain"
    assert _parse_args("--split-strategy", "heading").split_strategy == "heading"


def test_split_strategy_rejects_unknown_value():
    with pytest.raises(SystemExit):
        _parse_args("--split-strategy", "smart")


def test_resolve_split_export_config_uses_defaults_without_cli_or_config():
    config = resolve_split_export_config(None, _parse_args())

    assert config == SplitExportConfig(
        enabled=False,
        max_chars=DEFAULT_SPLIT_MAX_CHARS,
        strategy="heading",
    )


def test_resolve_split_export_config_uses_base_config():
    config = resolve_split_export_config(
        {"exports": {"split": {"enabled": True, "max_chars": 999, "strategy": "plain"}}},
        _parse_args(),
    )

    assert config == SplitExportConfig(enabled=True, max_chars=999, strategy="plain")


def test_resolve_split_export_config_cli_overrides_base_config():
    config = resolve_split_export_config(
        SplitExportConfig(enabled=True, max_chars=999, strategy="plain"),
        _parse_args("--no-split", "--split-max-chars", "123", "--split-strategy", "heading"),
    )

    assert config == SplitExportConfig(enabled=False, max_chars=123, strategy="heading")


@pytest.mark.parametrize(
    "parser_hook",
    [
        "add_split_export_options(full_parser)",
        "add_split_export_options(ai_export_parser)",
        "add_split_export_options(docs_export_parser)",
    ],
)
def test_existing_export_commands_have_split_option_hooks(parser_hook):
    import repodossier.cli as cli

    assert cli.__file__ is not None
    source = open(cli.__file__, encoding="utf-8").read()

    assert "from .cli_split import add_split_export_options" in source
    assert parser_hook in source


def test_changed_command_hook_is_only_required_when_changed_parser_exists():
    import repodossier.cli as cli

    assert cli.__file__ is not None
    source = open(cli.__file__, encoding="utf-8").read()

    if "changed_parser =" in source:
        assert "add_split_export_options(changed_parser)" in source

def test_resolve_split_export_config_uses_loaded_repodossier_config():
    from repodossier.config import RepoDossierConfig

    loaded_config = RepoDossierConfig(
        split=SplitExportConfig(enabled=True, max_chars=888, strategy="plain")
    )

    config = resolve_split_export_config(loaded_config, _parse_args())

    assert config == SplitExportConfig(enabled=True, max_chars=888, strategy="plain")


def test_cli_loads_config_before_enabling_split_interceptor():
    import repodossier.cli as cli

    assert cli.__file__ is not None
    source = open(cli.__file__, encoding="utf-8").read()

    assert source.index("config = _load_config_for_cli_args(arguments)") < source.index(
        "enable_split_write_interceptor_for_args(arguments, base_config=config)"
    )

