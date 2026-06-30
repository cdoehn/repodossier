import importlib


def test_changed_export_masks_diff_secret_values_and_reports_summary(monkeypatch):
    changed_exporter = importlib.import_module("repodossier.changed_exporter")

    api_secret = "sk-live-1234567890abcdefSECRET"
    token_secret = "ghp_1234567890abcdefSECRET"

    def fake_render(*args, **kwargs):
        return (
            "# Changed Export\n\n"
            "diff --git a/config.py b/config.py\n"
            f"+OPENAI_API_KEY = \"{api_secret}\"\n"
            f"-ACCESS_TOKEN='{token_secret}'\n"
            " unchanged line\n"
        )

    monkeypatch.setattr(changed_exporter, "_render_changed_export_unmasked", fake_render)

    rendered = changed_exporter.render_changed_export(object())

    assert api_secret not in rendered
    assert token_secret not in rendered
    assert "***REDACTED***" in rendered
    assert "+OPENAI_API_KEY" in rendered
    assert "-ACCESS_TOKEN" in rendered
    assert "# Secret Detection" in rendered
    assert "Potential secrets masked in changed export: 2" in rendered
    assert "- API_KEY: 1" in rendered
    assert "- TOKEN: 1" in rendered
    assert " unchanged line" in rendered
