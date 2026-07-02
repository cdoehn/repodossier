from repodossier.export_model_collector import repository_export_from_file_mappings
from repodossier.export_model_inventory import (
    FileInventoryEntry,
    repository_export_file_inventory,
    repository_export_file_inventory_by_group,
    repository_export_file_inventory_lines,
    repository_export_file_inventory_to_dicts,
)


def make_export():
    return repository_export_from_file_mappings(
        mode="full",
        root_path="/repo",
        root_name="repo",
        mappings=(
            {
                "path": "src/app.py",
                "language": "python",
                "content": "print(1)\n",
            },
            {
                "path": "assets/logo.png",
                "language": "binary",
                "binary": True,
                "skipped": True,
                "size": 123,
                "skip_reason": "binary file",
            },
            {
                "path": "large.log",
                "language": "text",
                "content": "partial",
                "truncated": True,
                "skip_reason": "too large",
            },
        ),
    )


def test_repository_export_file_inventory_lists_all_known_files():
    export = make_export()

    inventory = repository_export_file_inventory(export)

    assert inventory == (
        FileInventoryEntry(
            path="assets/logo.png",
            group="omitted_files",
            language="binary",
            status="skipped",
            text_status="binary",
            size_bytes=123,
            line_count=0,
            estimated_tokens=0,
            reason="binary file",
        ),
        FileInventoryEntry(
            path="large.log",
            group="truncated_files",
            language="text",
            status="truncated",
            text_status="text",
            size_bytes=7,
            line_count=1,
            estimated_tokens=2,
            reason="too large",
        ),
        FileInventoryEntry(
            path="src/app.py",
            group="files",
            language="python",
            status="included",
            text_status="text",
            size_bytes=9,
            line_count=1,
            estimated_tokens=3,
            reason=None,
        ),
    )


def test_repository_export_file_inventory_by_group_partitions_entries():
    grouped = repository_export_file_inventory_by_group(make_export())

    assert tuple(grouped) == ("files", "omitted_files", "truncated_files")
    assert [entry.path for entry in grouped["files"]] == ["src/app.py"]
    assert [entry.path for entry in grouped["omitted_files"]] == [
        "assets/logo.png"
    ]
    assert [entry.path for entry in grouped["truncated_files"]] == [
        "large.log"
    ]


def test_repository_export_file_inventory_to_dicts_is_json_ready():
    data = repository_export_file_inventory_to_dicts(make_export())

    assert data[0] == {
        "path": "assets/logo.png",
        "group": "omitted_files",
        "language": "binary",
        "status": "skipped",
        "text_status": "binary",
        "size_bytes": 123,
        "line_count": 0,
        "estimated_tokens": 0,
        "reason": "binary file",
    }


def test_repository_export_file_inventory_lines_are_stable():
    lines = repository_export_file_inventory_lines(make_export())

    assert lines == (
        "assets/logo.png | group=omitted_files | language=binary | "
        "status=skipped | text=binary | lines=0 | tokens=0 | bytes=123 | "
        "reason=binary file",
        "large.log | group=truncated_files | language=text | "
        "status=truncated | text=text | lines=1 | tokens=2 | bytes=7 | "
        "reason=too large",
        "src/app.py | group=files | language=python | status=included | "
        "text=text | lines=1 | tokens=3 | bytes=9",
    )
