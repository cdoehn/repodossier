from dataclasses import dataclass

from repodossier.export_model import FileEntry
from repodossier.export_model_collector import (
    FileEntryPartitions,
    partition_file_entries,
    repository_export_from_file_entries,
    repository_export_from_file_mappings,
    repository_export_from_file_objects,
)
from repodossier.export_model_configuration import make_export_configuration_summary
from repodossier.export_model_warnings import make_export_warning


def test_partition_file_entries_routes_entries_by_export_status():
    partitions = partition_file_entries(
        (
            FileEntry(path="z.py", language="python"),
            FileEntry(path="large.py", language="python", status="truncated"),
            FileEntry(path="broken.py", language="text", status="error"),
            FileEntry(path="assets/logo.png", language="binary", text_status="binary"),
            FileEntry(path="skipped.txt", language="text", status="skipped"),
            FileEntry(path="a.py", language="python"),
        )
    )

    assert isinstance(partitions, FileEntryPartitions)
    assert [entry.path for entry in partitions.files] == ["a.py", "z.py"]
    assert [entry.path for entry in partitions.truncated_files] == ["large.py"]
    assert [entry.path for entry in partitions.omitted_files] == [
        "assets/logo.png",
        "broken.py",
        "skipped.txt",
    ]


def test_file_entry_partitions_all_entries_returns_sorted_entries():
    partitions = FileEntryPartitions(
        files=(
            FileEntry(path="z.py", language="python"),
        ),
        omitted_files=(
            FileEntry(path="b.py", language="text", status="skipped"),
        ),
        truncated_files=(
            FileEntry(path="a.py", language="python", status="truncated"),
        ),
    )

    assert [entry.path for entry in partitions.all_entries()] == [
        "a.py",
        "b.py",
        "z.py",
    ]


def test_repository_export_from_file_entries_builds_finalized_export():
    export = repository_export_from_file_entries(
        mode="full",
        root_path="/repo",
        root_name="repo",
        entries=(
            FileEntry(
                path="src/app.py",
                language="python",
                content="print(1)\n",
            ),
            FileEntry(
                path="src/large.py",
                language="python",
                status="truncated",
                content="print(2)\n",
            ),
            FileEntry(
                path="assets/logo.png",
                language="binary",
                text_status="binary",
                status="skipped",
            ),
        ),
        configuration=make_export_configuration_summary(
            config_active=True,
            include_paths=("src",),
        ),
        warnings=(
            make_export_warning(
                "Example warning",
                path="src/large.py",
                code="truncated",
            ),
        ),
    )

    assert [entry.path for entry in export.files] == ["src/app.py"]
    assert [entry.path for entry in export.truncated_files] == ["src/large.py"]
    assert [entry.path for entry in export.omitted_files] == ["assets/logo.png"]

    assert export.configuration.config_active is True
    assert export.summary.total_tracked_files == 3
    assert export.summary.exported_text_files == 1
    assert export.summary.skipped_binary_files == 1
    assert export.warnings[0].code == "truncated"


def test_repository_export_from_file_mappings_uses_adapter_keys():
    export = repository_export_from_file_mappings(
        mode="docs",
        root_path="/repo",
        root_name="repo",
        mappings=(
            {
                "relative_path": "README.md",
                "lang": "markdown",
                "text": "# Hello\n",
            },
            {
                "path": "private.env",
                "language": "text",
                "skipped": True,
                "skip_reason": "excluded",
            },
            {
                "path": "huge.log",
                "language": "text",
                "truncated": True,
                "content": "partial",
            },
        ),
    )

    assert export.mode == "docs"
    assert [entry.path for entry in export.files] == ["README.md"]
    assert [entry.path for entry in export.omitted_files] == ["private.env"]
    assert [entry.path for entry in export.truncated_files] == ["huge.log"]
    assert export.omitted_files[0].reason == "excluded"


def test_repository_export_from_file_objects_uses_adapter_attributes():
    @dataclass
    class LegacyFile:
        relative_path: str
        language: str
        content: str
        truncated: bool = False

    export = repository_export_from_file_objects(
        mode="changed",
        root_path="/repo",
        root_name="repo",
        objects=(
            LegacyFile(
                relative_path="src/app.py",
                language="python",
                content="print(1)",
            ),
            LegacyFile(
                relative_path="src/large.py",
                language="python",
                content="partial",
                truncated=True,
            ),
        ),
    )

    assert export.mode == "changed"
    assert [entry.path for entry in export.files] == ["src/app.py"]
    assert [entry.path for entry in export.truncated_files] == ["src/large.py"]
