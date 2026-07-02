from dataclasses import FrozenInstanceError

import pytest

from repodossier.export_model import (
    ExportConfigurationSummary,
    ExportSummary,
    FileEntry,
    LanguageStatistics,
    RepositoryExport,
    RepositoryMetadata,
    empty_repository_export,
)


def test_empty_repository_export_builds_minimal_model():
    export = empty_repository_export(
        mode="full",
        root_path="/tmp/example",
        root_name="example",
    )

    assert isinstance(export, RepositoryExport)
    assert export.mode == "full"
    assert export.repository.root_path == "/tmp/example"
    assert export.repository.root_name == "example"
    assert export.files == ()
    assert export.warnings == ()


def test_file_entry_prefers_masked_content_for_rendering():
    entry = FileEntry(
        path="config.env",
        language="text",
        content="TOKEN=secret",
        masked_content="TOKEN=***",
    )

    assert entry.rendered_content == "TOKEN=***"


def test_file_entry_uses_raw_content_without_mask():
    entry = FileEntry(
        path="README.md",
        language="markdown",
        content="# Hello",
    )

    assert entry.rendered_content == "# Hello"


def test_repository_export_filters_included_files():
    included = FileEntry(path="a.py", language="python", status="included")
    skipped = FileEntry(path="image.png", language="unknown", status="skipped")
    truncated = FileEntry(path="large.py", language="python", status="truncated")

    export = RepositoryExport(
        mode="ai",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(included, skipped, truncated),
    )

    assert export.included_files() == (included,)


def test_repository_export_all_paths_are_deterministic_and_deduplicated():
    export = RepositoryExport(
        mode="changed",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
        files=(
            FileEntry(path="b.py", language="python"),
            FileEntry(path="a.py", language="python"),
        ),
        omitted_files=(FileEntry(path="z.bin", language="unknown"),),
        truncated_files=(FileEntry(path="a.py", language="python"),),
    )

    assert export.all_paths() == ("a.py", "b.py", "z.bin")


def test_language_statistics_increment_is_immutable():
    stats = LanguageStatistics()
    next_stats = stats.increment("python").increment("python").increment("markdown")

    assert stats.counts == {}
    assert next_stats.counts == {"python": 2, "markdown": 1}


def test_export_model_dataclasses_are_frozen():
    metadata = RepositoryMetadata(root_path="/repo", root_name="repo")

    with pytest.raises(FrozenInstanceError):
        metadata.root_name = "other"


def test_configuration_and_summary_defaults_are_independent():
    config_a = ExportConfigurationSummary()
    config_b = ExportConfigurationSummary()
    config_a.limits["max_file_bytes"] = 123

    summary_a = ExportSummary()
    summary_b = ExportSummary()
    summary_a.file_type_statistics[".py"] = 1

    assert config_b.limits == {}
    assert summary_b.file_type_statistics == {}
