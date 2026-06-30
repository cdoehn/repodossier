import pytest

from repocontext.config import get_split_export_config
from repocontext.split_config import (
    DEFAULT_SPLIT_MAX_CHARS,
    DEFAULT_SPLIT_STRATEGY,
    SplitExportConfig,
    parse_split_export_config,
)


def test_split_export_config_defaults_without_config():
    config = parse_split_export_config({})

    assert config == SplitExportConfig(
        enabled=False,
        max_chars=DEFAULT_SPLIT_MAX_CHARS,
        strategy=DEFAULT_SPLIT_STRATEGY,
    )


def test_split_export_config_defaults_without_split_section():
    config = parse_split_export_config({"exports": {}})

    assert config.enabled is False
    assert config.max_chars == DEFAULT_SPLIT_MAX_CHARS
    assert config.strategy == DEFAULT_SPLIT_STRATEGY


def test_split_export_config_parses_enabled_split_section():
    config = parse_split_export_config(
        {
            "exports": {
                "split": {
                    "enabled": True,
                    "max_chars": 12345,
                    "strategy": "plain",
                }
            }
        }
    )

    assert config == SplitExportConfig(
        enabled=True,
        max_chars=12345,
        strategy="plain",
    )


def test_split_export_config_accepts_direct_split_mapping():
    config = parse_split_export_config(
        {
            "enabled": True,
            "max_chars": 1000,
            "strategy": "heading",
        }
    )

    assert config.enabled is True
    assert config.max_chars == 1000
    assert config.strategy == "heading"


@pytest.mark.parametrize("bad_value", [0, -1, "1000", True, None])
def test_split_export_config_rejects_invalid_max_chars(bad_value):
    with pytest.raises(ValueError, match="exports.split.max_chars"):
        parse_split_export_config({"exports": {"split": {"max_chars": bad_value}}})


@pytest.mark.parametrize("bad_value", ["smart", "", 123, None])
def test_split_export_config_rejects_unknown_strategy(bad_value):
    with pytest.raises(ValueError, match="exports.split.strategy"):
        parse_split_export_config({"exports": {"split": {"strategy": bad_value}}})


@pytest.mark.parametrize("bad_value", ["maybe", 1, 0, None])
def test_split_export_config_rejects_invalid_enabled_value(bad_value):
    with pytest.raises(ValueError, match="exports.split.enabled"):
        parse_split_export_config({"exports": {"split": {"enabled": bad_value}}})


def test_split_export_config_accepts_boolean_strings_for_cli_bridge():
    enabled = parse_split_export_config({"enabled": "yes"})
    disabled = parse_split_export_config({"enabled": "off"})

    assert enabled.enabled is True
    assert disabled.enabled is False


def test_config_module_exposes_split_config_helper():
    config = get_split_export_config(
        {
            "exports": {
                "split": {
                    "enabled": True,
                    "max_chars": 777,
                    "strategy": "heading",
                }
            }
        }
    )

    assert config == SplitExportConfig(
        enabled=True,
        max_chars=777,
        strategy="heading",
    )
