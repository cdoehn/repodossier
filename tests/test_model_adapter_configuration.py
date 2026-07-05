"""Configuration preservation for RepositoryExport adapter helpers."""

from __future__ import annotations

from dataclasses import dataclass

from repodossier.export_model import ExportConfigurationSummary, FileEntry
from repodossier.exporters.model_adapter import (
    build_repository_export_from_entries,
    export_configuration_from_mapping,
    export_configuration_from_object,
)
from repodossier.renderers import render_markdown


@dataclass(frozen=True)
class LegacyConfiguration:
    config_active: bool = True
    config_path: str = "repo.yml"
    include_paths: tuple[str, ...] = ("src",)
    include_globs: tuple[str, ...] = ("*.py",)
    exclude_paths: tuple[str, ...] = ("build",)
    exclude_globs: tuple[str, ...] = ("*.log",)
    limits: dict[str, object] | None = None
    split_settings: dict[str, object] | None = None


def _file_entry() -> FileEntry:
    return FileEntry(
        path="src/app.py",
        language="python",
        content="print('hi')\n",
        line_count=1,
        estimated_tokens=3,
    )


def test_export_configuration_from_mapping_uses_safe_defaults() -> None:
    configuration = export_configuration_from_mapping(
        {
            "config_active": True,
            "config_path": "repodossier.yml",
            "include_paths": ["src", "tests"],
            "include_globs": ["*.py"],
            "exclude_paths": ["build"],
            "exclude_globs": ["*.log"],
            "limits": {"max_total_files": 100},
            "split_settings": {"enabled": True},
        }
    )

    assert configuration.config_active is True
    assert configuration.config_path == "repodossier.yml"
    assert configuration.include_paths == ("src", "tests")
    assert configuration.include_globs == ("*.py",)
    assert configuration.exclude_paths == ("build",)
    assert configuration.exclude_globs == ("*.log",)
    assert configuration.limits == {"max_total_files": 100}
    assert configuration.split_settings == {"enabled": True}


def test_export_configuration_from_object_accepts_existing_summary() -> None:
    existing = ExportConfigurationSummary(
        config_active=True,
        config_path="existing.yml",
        include_paths=("src",),
    )

    configuration = export_configuration_from_object(existing)

    assert configuration is existing


def test_export_configuration_from_object_accepts_legacy_object() -> None:
    configuration = export_configuration_from_object(
        LegacyConfiguration(
            limits={"max_export_bytes": 2000},
            split_settings={"chunk_count": 2},
        )
    )

    assert configuration.config_active is True
    assert configuration.config_path == "repo.yml"
    assert configuration.include_paths == ("src",)
    assert configuration.include_globs == ("*.py",)
    assert configuration.exclude_paths == ("build",)
    assert configuration.exclude_globs == ("*.log",)
    assert configuration.limits == {"max_export_bytes": 2000}
    assert configuration.split_settings == {"chunk_count": 2}


def test_build_repository_export_from_entries_accepts_configuration_mapping() -> None:
    export = build_repository_export_from_entries(
        mode="full",
        root_path="/tmp/repo",
        files=(_file_entry(),),
        configuration={
            "config_active": True,
            "config_path": "repodossier.yml",
            "include_paths": ["src"],
            "include_globs": ["*.py"],
            "exclude_paths": ["build"],
            "exclude_globs": ["*.log"],
            "limits": {"max_total_files": 100},
            "split_settings": {"enabled": True},
        },
    )

    assert export.configuration.config_active is True
    assert export.configuration.config_path == "repodossier.yml"
    assert export.configuration.include_paths == ("src",)
    assert export.configuration.include_globs == ("*.py",)
    assert export.configuration.exclude_paths == ("build",)
    assert export.configuration.exclude_globs == ("*.log",)
    assert export.configuration.limits == {"max_total_files": 100}
    assert export.configuration.split_settings == {"enabled": True}


def test_build_repository_export_from_entries_accepts_configuration_kwargs() -> None:
    export = build_repository_export_from_entries(
        mode="full",
        root_path="/tmp/repo",
        files=(_file_entry(),),
        config_active=True,
        config_path="repodossier.yml",
        include_paths=("src",),
        include_globs=("*.py",),
        exclude_paths=("build",),
        exclude_globs=("*.log",),
        limits={"max_total_files": 100},
        split_settings={"enabled": True},
    )

    assert export.configuration.config_active is True
    assert export.configuration.config_path == "repodossier.yml"
    assert export.configuration.include_paths == ("src",)
    assert export.configuration.include_globs == ("*.py",)
    assert export.configuration.exclude_paths == ("build",)
    assert export.configuration.exclude_globs == ("*.log",)
    assert export.configuration.limits == {"max_total_files": 100}
    assert export.configuration.split_settings == {"enabled": True}


def test_adapted_configuration_is_visible_to_generic_markdown_renderer() -> None:
    export = build_repository_export_from_entries(
        mode="full",
        root_path="/tmp/repo",
        files=(_file_entry(),),
        config_active=True,
        config_path="repodossier.yml",
        include_paths=("src",),
        include_globs=("*.py",),
        exclude_paths=("build",),
        exclude_globs=("*.log",),
        limits={"max_total_files": 100},
        split_settings={"enabled": True},
    )

    rendered = render_markdown(export)

    assert "## Configuration" in rendered
    assert "- Config active: True" in rendered
    assert "- Config path: repodossier.yml" in rendered
    assert "- Include paths:" in rendered
    assert "  - src" in rendered
    assert "- Include globs:" in rendered
    assert "  - *.py" in rendered
    assert "- Exclude paths:" in rendered
    assert "  - build" in rendered
    assert "- Exclude globs:" in rendered
    assert "  - *.log" in rendered
    assert "- Limits:" in rendered
    assert "  - max_total_files: 100" in rendered
    assert "- Split settings:" in rendered
    assert "  - enabled: True" in rendered
