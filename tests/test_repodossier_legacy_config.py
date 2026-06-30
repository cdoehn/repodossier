from pathlib import Path


def test_config_module_documents_current_and_legacy_config_filenames():
    text = Path("src/repodossier/config.py").read_text(encoding="utf-8")

    assert ".repodossier.yml" in text
    assert ".repodossier.yaml" in text
    assert ".repodossier.toml" in text

    assert ".repocontext.yml" in text
    assert ".repocontext.yaml" in text
    assert ".repocontext.toml" in text


def test_legacy_tool_section_helper_prefers_current_config():
    from repodossier.config import _get_current_or_legacy_tool_section

    tool_table = {
        "repodossier": {"exclude": ["current/**"]},
        "repocontext": {"exclude": ["legacy/**"]},
    }

    assert _get_current_or_legacy_tool_section(tool_table) == {
        "exclude": ["current/**"]
    }


def test_legacy_tool_section_helper_falls_back_to_repocontext_config():
    from repodossier.config import _get_current_or_legacy_tool_section

    tool_table = {
        "repocontext": {"include": ["legacy-src/**"]},
    }

    assert _get_current_or_legacy_tool_section(tool_table) == {
        "include": ["legacy-src/**"]
    }


def test_legacy_tool_section_helper_handles_missing_or_invalid_tool_table():
    from repodossier.config import _get_current_or_legacy_tool_section

    assert _get_current_or_legacy_tool_section(None) == {}
    assert _get_current_or_legacy_tool_section({}) == {}
