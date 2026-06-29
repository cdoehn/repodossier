import re

from repocontext.secrets import (
    SecretFinding,
    SecretPattern,
    default_secret_patterns,
    mask_secret_in_line,
    mask_secret_value,
)


def test_secret_finding_sets_all_fields():
    finding = SecretFinding(
        file_path="config.py",
        line_number=3,
        secret_type="API_KEY",
        matched_text="sk_test_1234567890",
        masked_text="sk_t***REDACTED***7890",
        variable_name="OPENAI_API_KEY",
        confidence="high",
    )

    assert finding.file_path == "config.py"
    assert finding.line_number == 3
    assert finding.secret_type == "API_KEY"
    assert finding.matched_text == "sk_test_1234567890"
    assert finding.masked_text == "sk_t***REDACTED***7890"
    assert finding.variable_name == "OPENAI_API_KEY"
    assert finding.confidence == "high"
    assert finding.has_secret is True


def test_secret_finding_summary_line_does_not_expose_value():
    finding = SecretFinding(
        file_path="settings.py",
        line_number=9,
        secret_type="TOKEN",
        matched_text="real-token-value",
        masked_text="real***REDACTED***alue",
        variable_name="ACCESS_TOKEN",
        confidence="high",
    )

    summary = finding.summary_line

    assert "settings.py:9" in summary
    assert "TOKEN" in summary
    assert "ACCESS_TOKEN" in summary
    assert "real-token-value" not in summary


def test_secret_pattern_model_accepts_compiled_regex():
    pattern = SecretPattern(
        name="custom",
        regex=re.compile(r"SECRET=(?P<value>.+)"),
        secret_type="SECRET",
        confidence="medium",
        value_group="value",
    )

    assert pattern.name == "custom"
    assert pattern.regex.search("SECRET=abc")
    assert pattern.secret_type == "SECRET"
    assert pattern.confidence == "medium"
    assert pattern.value_group == "value"


def test_default_secret_patterns_are_not_empty():
    assert default_secret_patterns()


def test_default_secret_pattern_names_are_unique():
    patterns = default_secret_patterns()
    names = [pattern.name for pattern in patterns]

    assert len(names) == len(set(names))


def test_default_secret_patterns_define_secret_types():
    patterns = default_secret_patterns()

    assert {pattern.secret_type for pattern in patterns} == {
        "API_KEY",
        "TOKEN",
        "SECRET",
        "PASSWORD",
    }


def test_default_secret_patterns_have_value_group():
    assert all(pattern.value_group == "value" for pattern in default_secret_patterns())


def test_mask_secret_value_keeps_empty_value_empty():
    assert mask_secret_value("") == ""


def test_mask_secret_value_fully_masks_short_values():
    assert mask_secret_value("abc") == "***REDACTED***"
    assert mask_secret_value("12345678") == "***REDACTED***"


def test_mask_secret_value_partially_masks_long_values():
    masked = mask_secret_value("sk_live_1234567890abcdef")

    assert masked == "sk_l***REDACTED***cdef"
    assert "sk_live_1234567890abcdef" not in masked


def test_mask_secret_value_is_deterministic():
    value = "ghp_1234567890abcdef"

    assert mask_secret_value(value) == mask_secret_value(value)


def test_mask_secret_in_line_replaces_only_secret_value():
    line = "OPENAI_API_KEY = 'sk_live_1234567890abcdef'  # production key"

    masked = mask_secret_in_line(line, "sk_live_1234567890abcdef")

    assert masked == "OPENAI_API_KEY = 'sk_l***REDACTED***cdef'  # production key"
    assert "sk_live_1234567890abcdef" not in masked
    assert "OPENAI_API_KEY = '" in masked
    assert "# production key" in masked


def test_mask_secret_in_line_without_secret_value_returns_original_line():
    line = "API_KEY = 'abc'"

    assert mask_secret_in_line(line, "") == line
