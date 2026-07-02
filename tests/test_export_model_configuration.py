from repodossier.export_model import ExportConfigurationSummary
from repodossier.export_model_configuration import (
    make_export_configuration_summary,
    merge_configuration_summaries,
    normalize_configuration_mapping,
    normalize_configuration_paths,
    normalize_configuration_patterns,
)


def test_make_export_configuration_summary_normalizes_all_fields():
    summary = make_export_configuration_summary(
        config_active=True,
        config_path=" repodossier.yml ",
        include_paths=["src\\repodossier", "./README.md", "src/repodossier"],
        include_globs=[" **/*.py ", "*.md", "*.md"],
        exclude_paths=["build", "./dist"],
        exclude_globs=[" *.pyc ", "__pycache__/**"],
        limits={"z": 2, "a": 1},
        split_settings={"max_parts": 5},
    )

    assert summary.config_active is True
    assert summary.config_path == "repodossier.yml"
    assert summary.include_paths == ("README.md", "src/repodossier")
    assert summary.include_globs == ("**/*.py", "*.md")
    assert summary.exclude_paths == ("build", "dist")
    assert summary.exclude_globs == ("*.pyc", "__pycache__/**")
    assert list(summary.limits) == ["a", "z"]
    assert summary.split_settings == {"max_parts": 5}


def test_normalize_configuration_paths_rejects_invalid_repository_paths():
    try:
        normalize_configuration_paths(["../secret.txt"])
    except ValueError as exc:
        assert "must not escape repository" in str(exc)
    else:
        raise AssertionError("Expected invalid path to be rejected")


def test_normalize_configuration_patterns_strips_empty_values_and_backslashes():
    assert normalize_configuration_patterns(
        ["", "  ", "src\\**\\*.py", "*.py", "*.py"]
    ) == ("*.py", "src/**/*.py")


def test_normalize_configuration_mapping_sorts_keys_and_copies_nested_values():
    original = {
        "z": 1,
        "a": {"b": 2, "a": 1},
        "list": ["b", "a"],
        "set": {"y", "x"},
    }

    normalized = normalize_configuration_mapping(original)

    assert list(normalized) == ["a", "list", "set", "z"]
    assert list(normalized["a"]) == ["a", "b"]
    assert normalized["list"] == ["a", "b"]
    assert normalized["set"] == ["x", "y"]

    normalized["a"]["a"] = 99
    assert original["a"]["a"] == 1


def test_make_export_configuration_summary_uses_empty_defaults():
    summary = make_export_configuration_summary()

    assert summary == ExportConfigurationSummary()


def test_make_export_configuration_summary_normalizes_blank_config_path_to_none():
    summary = make_export_configuration_summary(config_path="   ")

    assert summary.config_path is None


def test_merge_configuration_summaries_combines_paths_patterns_and_mappings():
    base = make_export_configuration_summary(
        config_active=False,
        config_path="base.yml",
        include_paths=["src"],
        include_globs=["*.py"],
        exclude_paths=["build"],
        exclude_globs=["*.pyc"],
        limits={"max_file_bytes": 100},
        split_settings={"enabled": False},
    )
    override = make_export_configuration_summary(
        config_active=True,
        config_path="override.yml",
        include_paths=["tests"],
        include_globs=["*.md"],
        exclude_paths=["dist"],
        exclude_globs=["*.tmp"],
        limits={"max_file_bytes": 200, "max_files": 10},
        split_settings={"enabled": True},
    )

    merged = merge_configuration_summaries(base, override)

    assert merged.config_active is True
    assert merged.config_path == "override.yml"
    assert merged.include_paths == ("src", "tests")
    assert merged.include_globs == ("*.md", "*.py")
    assert merged.exclude_paths == ("build", "dist")
    assert merged.exclude_globs == ("*.pyc", "*.tmp")
    assert merged.limits == {
        "max_file_bytes": 200,
        "max_files": 10,
    }
    assert merged.split_settings == {"enabled": True}
