from pathlib import Path

import pytest

from repocontext.config import (
    ConfigError,
    RepoContextConfig,
    discover_repository_root,
    filter_file_infos,
    filter_file_paths,
    is_path_included,
    load_config,
    load_config_for_path,
    parse_config,

)


def test_load_config_returns_defaults_when_file_is_missing(tmp_path):
    config = load_config(tmp_path)

    assert config == RepoContextConfig()
    assert config.enabled is False
    assert config.path is None


def test_load_config_reads_root_config(tmp_path):
    config_file = tmp_path / ".repocontext.yml"
    config_file.write_text(
        """
include:
  paths:
    - src
  globs:
    - "*.md"
exclude:
  paths:
    - build
  globs:
    - "*.log"
limits:
  max_file_bytes: 1000
  max_total_files: 25
  max_export_bytes: 5000
  max_line_count: 300
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.enabled is True
    assert config.path == config_file.resolve()
    assert config.include.paths == ("src",)
    assert config.include.globs == ("*.md",)
    assert config.exclude.paths == ("build",)
    assert config.exclude.globs == ("*.log",)
    assert config.limits.max_file_bytes == 1000
    assert config.limits.max_total_files == 25
    assert config.limits.max_export_bytes == 5000
    assert config.limits.max_line_count == 300


def test_load_config_for_path_discovers_repository_root_from_subdirectory(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
""",
        encoding="utf-8",
    )
    subdir = tmp_path / "src" / "repocontext"
    subdir.mkdir(parents=True)

    config = load_config_for_path(subdir)

    assert config.enabled is True
    assert config.path == (tmp_path / ".repocontext.yml").resolve()
    assert config.include.paths == ("src",)


def test_explicit_config_path_is_resolved_relative_to_repository_root(tmp_path):
    (tmp_path / "config").mkdir()
    custom_config = tmp_path / "config" / "custom.yml"
    custom_config.write_text(
        """
exclude:
  globs:
    - "*.sqlite"
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path, "config/custom.yml")

    assert config.enabled is True
    assert config.path == custom_config.resolve()
    assert config.exclude.globs == ("*.sqlite",)


def test_no_config_ignores_existing_config_file(tmp_path):
    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path, no_config=True)

    assert config == RepoContextConfig()


def test_empty_config_file_uses_defaults(tmp_path):
    (tmp_path / ".repocontext.yml").write_text("", encoding="utf-8")

    config = load_config(tmp_path)

    assert config.enabled is True
    assert config.include.paths == ()
    assert config.exclude.globs == ()
    assert config.limits.max_file_bytes is None


def test_invalid_yaml_raises_clear_config_error(tmp_path):
    (tmp_path / ".repocontext.yml").write_text(
        "include: [unterminated",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(tmp_path)


def test_missing_explicit_config_raises_clear_error(tmp_path):
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config(tmp_path, "missing.yml")


def test_unknown_top_level_key_is_rejected():
    with pytest.raises(ConfigError, match="Unknown configuration key"):
        parse_config({"unknown": {}})


def test_include_must_be_mapping():
    with pytest.raises(ConfigError, match="include must be a mapping"):
        parse_config({"include": []})


def test_include_paths_must_be_list():
    with pytest.raises(ConfigError, match="include.paths must be a list"):
        parse_config({"include": {"paths": "src"}})


def test_exclude_globs_must_be_list():
    with pytest.raises(ConfigError, match="exclude.globs must be a list"):
        parse_config({"exclude": {"globs": "*.log"}})


def test_filter_items_must_be_strings():
    with pytest.raises(ConfigError, match=r"include\.paths\[1\] must be a string"):
        parse_config({"include": {"paths": ["src", 123]}})


def test_empty_filter_items_are_rejected():
    with pytest.raises(ConfigError, match=r"exclude\.paths\[0\] must not be empty"):
        parse_config({"exclude": {"paths": ["  "]}})


def test_limits_must_be_mapping():
    with pytest.raises(ConfigError, match="limits must be a mapping"):
        parse_config({"limits": []})


def test_limits_must_be_positive_integers_or_null():
    with pytest.raises(ConfigError, match="limits.max_file_bytes must be greater than 0"):
        parse_config({"limits": {"max_file_bytes": 0}})

    with pytest.raises(ConfigError, match="limits.max_total_files must be greater than 0"):
        parse_config({"limits": {"max_total_files": -1}})

    with pytest.raises(ConfigError, match="limits.max_export_bytes must be a positive integer"):
        parse_config({"limits": {"max_export_bytes": "1000"}})


def test_limit_null_is_allowed():
    config = parse_config({"limits": {"max_file_bytes": None}})

    assert config.limits.max_file_bytes is None




class DummyFileInfo:
    def __init__(self, relative_path):
        self.relative_path = relative_path


class DummyAbsoluteFileInfo:
    def __init__(self, path):
        self.path = path


def test_filter_file_infos_filters_objects_by_relative_path():
    config = parse_config(
        {
            "include": {"paths": ["src"]},
            "exclude": {"globs": ["**/private/**"]},
        }
    )
    files = [
        DummyFileInfo("src/repocontext/config.py"),
        DummyFileInfo("src/repocontext/private/secrets.py"),
        DummyFileInfo("tests/test_config.py"),
    ]

    assert filter_file_infos(files, config) == [files[0]]


def test_filter_file_infos_filters_dictionaries_by_relative_path():
    config = parse_config(
        {
            "include": {"globs": ["*.md", "docs/**/*.md"]},
            "exclude": {"paths": ["docs/private"]},
        }
    )
    files = [
        {"relative_path": "README.md"},
        {"path": "docs/usage.md"},
        {"file_path": "docs/private/internal.md"},
        {"filepath": "src/repocontext/config.py"},
    ]

    assert filter_file_infos(files, config) == [files[0], files[1]]


def test_filter_file_infos_can_convert_absolute_paths_with_repository_root(tmp_path):
    src_file = tmp_path / "src" / "repocontext" / "config.py"
    test_file = tmp_path / "tests" / "test_config.py"
    src_file.parent.mkdir(parents=True)
    test_file.parent.mkdir(parents=True)
    src_file.write_text("", encoding="utf-8")
    test_file.write_text("", encoding="utf-8")

    config = parse_config({"include": {"paths": ["src"]}})
    files = [
        DummyAbsoluteFileInfo(src_file),
        DummyAbsoluteFileInfo(test_file),
    ]

    assert filter_file_infos(files, config, repository_root=tmp_path) == [files[0]]


def test_filter_file_infos_raises_clear_error_for_unknown_file_shape():
    config = parse_config({})

    with pytest.raises(ConfigError, match="file entry has no path field"):
        filter_file_infos([object()], config)

def test_path_is_included_when_no_filter_rules_are_configured():
    config = parse_config({})

    assert is_path_included("src/repocontext/config.py", config) is True
    assert is_path_included(Path("README.md"), config) is True


def test_include_path_selects_files_under_directory():
    config = parse_config({"include": {"paths": ["src"]}})

    assert is_path_included("src/repocontext/config.py", config) is True
    assert is_path_included("src", config) is True
    assert is_path_included("tests/test_config.py", config) is False


def test_include_path_can_select_single_file():
    config = parse_config({"include": {"paths": ["README.md"]}})

    assert is_path_included("README.md", config) is True
    assert is_path_included("docs/README.md", config) is False


def test_include_glob_selects_matching_files():
    config = parse_config({"include": {"globs": ["src/**/*.py"]}})

    assert is_path_included("src/repocontext/config.py", config) is True
    assert is_path_included("tests/test_config.py", config) is False


def test_include_paths_and_globs_are_additive():
    config = parse_config(
        {
            "include": {
                "paths": ["src"],
                "globs": ["*.md"],
            }
        }
    )

    assert is_path_included("src/repocontext/config.py", config) is True
    assert is_path_included("README.md", config) is True
    assert is_path_included("tests/test_config.py", config) is False


def test_exclude_path_removes_files_under_directory():
    config = parse_config({"exclude": {"paths": ["build"]}})

    assert is_path_included("src/repocontext/config.py", config) is True
    assert is_path_included("build/generated.py", config) is False
    assert is_path_included("build", config) is False


def test_exclude_glob_removes_matching_files():
    config = parse_config({"exclude": {"globs": ["*.log", "**/__pycache__/**"]}})

    assert is_path_included("src/repocontext/config.py", config) is True
    assert is_path_included("debug.log", config) is False
    assert is_path_included("src/repocontext/__pycache__/config.pyc", config) is False


def test_exclude_wins_over_include():
    config = parse_config(
        {
            "include": {
                "paths": ["src"],
                "globs": ["*.md"],
            },
            "exclude": {
                "paths": ["src/repocontext/private"],
                "globs": ["README.md"],
            },
        }
    )

    assert is_path_included("src/repocontext/config.py", config) is True
    assert is_path_included("src/repocontext/private/secrets.py", config) is False
    assert is_path_included("README.md", config) is False


def test_filter_file_paths_preserves_order_and_original_values():
    paths = [
        Path("src/repocontext/config.py"),
        Path("src/repocontext/private/secrets.py"),
        Path("README.md"),
        Path("tests/test_config.py"),
    ]
    config = parse_config(
        {
            "include": {
                "paths": ["src"],
                "globs": ["README.md"],
            },
            "exclude": {
                "paths": ["src/repocontext/private"],
            },
        }
    )

    assert filter_file_paths(paths, config) == [
        Path("src/repocontext/config.py"),
        Path("README.md"),
    ]


def test_filter_matching_normalizes_dot_prefixes_and_trailing_slashes():
    config = parse_config(
        {
            "include": {
                "paths": ["./src/"],
            },
            "exclude": {
                "paths": ["./src/generated/"],
            },
        }
    )

    assert is_path_included("./src/repocontext/config.py", config) is True
    assert is_path_included("src/generated/file.py", config) is False

def test_discover_repository_root_falls_back_to_git_directory(tmp_path):
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)

    assert discover_repository_root(nested) == tmp_path.resolve()
