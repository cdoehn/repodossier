import re

from repocontext.secrets import (
    SecretFinding,
    SecretPattern,
    default_secret_patterns,
    detect_secrets_in_text,
    is_placeholder_secret,
    is_probably_secret_value,
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


def test_detects_python_api_key_assignment():
    text = 'OPENAI_API_KEY = "sk-live-1234567890abcdef"\n'

    findings = detect_secrets_in_text(text, "config.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "API_KEY"
    assert findings[0].variable_name == "OPENAI_API_KEY"
    assert findings[0].line_number == 1
    assert findings[0].matched_text == "sk-live-1234567890abcdef"
    assert "sk-live-1234567890abcdef" not in findings[0].masked_text
    assert "***REDACTED***" in findings[0].masked_text


def test_detects_dotenv_api_key_assignment():
    text = "API_KEY=abcdef1234567890\n"

    findings = detect_secrets_in_text(text, ".env")

    assert len(findings) == 1
    assert findings[0].secret_type == "API_KEY"
    assert findings[0].variable_name == "API_KEY"


def test_detects_yaml_style_api_key_assignment():
    text = "api_key: abcdef1234567890\n"

    findings = detect_secrets_in_text(text, "config.yml")

    assert len(findings) == 1
    assert findings[0].secret_type == "API_KEY"
    assert findings[0].variable_name == "api_key"


def test_detects_export_api_key_assignment():
    text = 'export GOOGLE_API_KEY="abcdef1234567890"\n'

    findings = detect_secrets_in_text(text, ".envrc")

    assert len(findings) == 1
    assert findings[0].secret_type == "API_KEY"
    assert findings[0].variable_name == "GOOGLE_API_KEY"


def test_detects_os_environ_api_key_assignment():
    text = 'os.environ["OPENAI_API_KEY"] = "sk-live-1234567890abcdef"\n'

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "API_KEY"
    assert findings[0].variable_name == "OPENAI_API_KEY"


def test_detects_camelcase_api_key_assignment():
    text = 'apiKey = "abcdef1234567890"\n'

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "API_KEY"
    assert findings[0].variable_name == "apiKey"


def test_detects_access_token_assignment():
    text = 'ACCESS_TOKEN = "ghp_1234567890abcdef"\n'

    findings = detect_secrets_in_text(text, "config.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "TOKEN"
    assert findings[0].variable_name == "ACCESS_TOKEN"


def test_detects_refresh_token_assignment():
    text = "refresh_token='refresh_1234567890abcdef'\n"

    findings = detect_secrets_in_text(text, "config.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "TOKEN"
    assert findings[0].variable_name == "refresh_token"


def test_detects_github_token_assignment():
    text = 'GITHUB_TOKEN = "ghp_1234567890abcdef"\n'

    findings = detect_secrets_in_text(text, "config.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "TOKEN"


def test_does_not_detect_token_word_without_assignment():
    text = "this token is mentioned in prose only\n"

    assert detect_secrets_in_text(text, "README.md") == []


def test_detects_client_secret_assignment():
    text = 'CLIENT_SECRET = "client-secret-1234567890"\n'

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "SECRET"
    assert findings[0].variable_name == "CLIENT_SECRET"


def test_detects_jwt_secret_assignment():
    text = 'jwt_secret = "jwt-secret-1234567890"\n'

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "SECRET"


def test_detects_webhook_secret_assignment():
    text = 'WEBHOOK_SECRET = "webhook-secret-1234567890"\n'

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "SECRET"


def test_does_not_detect_secret_word_in_comment_without_value():
    text = "# secret should be configured in production\n"

    assert detect_secrets_in_text(text, "README.md") == []


def test_detects_db_password_assignment():
    text = 'DB_PASSWORD = "database-password-1234567890"\n'

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "PASSWORD"
    assert findings[0].variable_name == "DB_PASSWORD"


def test_detects_password_assignment():
    text = 'password = "database-password-1234567890"\n'

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "PASSWORD"


def test_detects_passwd_assignment():
    text = "passwd='database-password-1234567890'\n"

    findings = detect_secrets_in_text(text, "settings.py")

    assert len(findings) == 1
    assert findings[0].secret_type == "PASSWORD"


def test_detects_pwd_yaml_assignment():
    text = 'pwd: "database-password-1234567890"\n'

    findings = detect_secrets_in_text(text, "settings.yml")

    assert len(findings) == 1
    assert findings[0].secret_type == "PASSWORD"


def test_does_not_detect_password_required_boolean():
    text = "password_required = True\n"

    assert detect_secrets_in_text(text, "settings.py") == []


def test_placeholder_values_are_identified_case_insensitively():
    assert is_placeholder_secret("changeme")
    assert is_placeholder_secret("CHANGE-ME")
    assert is_placeholder_secret("your-api-key")
    assert is_placeholder_secret(" insert-key-here ")


def test_realistic_long_token_is_not_placeholder():
    assert not is_placeholder_secret("test_very_long_realistic_token_123456")


def test_probably_secret_value_rejects_booleans_numbers_and_short_values():
    assert not is_probably_secret_value("True")
    assert not is_probably_secret_value("false")
    assert not is_probably_secret_value("123")
    assert not is_probably_secret_value("abcde")
    assert not is_probably_secret_value("password")


def test_probably_secret_value_accepts_realistic_value():
    assert is_probably_secret_value("sk-123456789abcdef")


def test_detect_ignores_placeholder_api_key():
    text = 'API_KEY = "your-api-key"\n'

    assert detect_secrets_in_text(text, "README.md") == []


def test_detect_ignores_numeric_token_count():
    text = "TOKEN = 123\n"

    assert detect_secrets_in_text(text, "config.py") == []


def test_detect_ignores_secret_enabled_boolean():
    text = "SECRET = false\n"

    assert detect_secrets_in_text(text, "config.py") == []


def test_detect_ignores_full_line_comment_assignment():
    text = '# API_KEY = "sk-live-1234567890abcdef"\n'

    assert detect_secrets_in_text(text, "README.md") == []


def test_detect_preserves_inline_comment_in_masked_text():
    text = 'API_KEY = "sk-live-1234567890abcdef"  # comment remains\n'

    findings = detect_secrets_in_text(text, "config.py")

    assert len(findings) == 1
    assert "# comment remains" in findings[0].masked_text
    assert "sk-live-1234567890abcdef" not in findings[0].masked_text


def test_detects_multiple_secret_types_in_file_order():
    text = "\n".join(
        [
            'OPENAI_API_KEY = "sk-live-1234567890abcdef"',
            'ACCESS_TOKEN = "ghp_1234567890abcdef"',
            'CLIENT_SECRET = "client-secret-1234567890"',
            'DB_PASSWORD = "database-password-1234567890"',
        ]
    )

    findings = detect_secrets_in_text(text, "settings.py")

    assert [finding.secret_type for finding in findings] == [
        "API_KEY",
        "TOKEN",
        "SECRET",
        "PASSWORD",
    ]
    assert [finding.line_number for finding in findings] == [1, 2, 3, 4]
