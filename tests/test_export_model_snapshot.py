import json

import pytest

from repodossier.export_model_factory import make_repository_export
from repodossier.export_model_content import make_file_entry_from_content
from repodossier.export_model_warnings import make_export_warning
from repodossier.export_model_snapshot import (
    repository_export_fingerprint,
    repository_export_snapshot_header,
    repository_export_snapshot_lines,
    repository_export_to_json,
)


def make_export():
    return make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        files=(
            make_file_entry_from_content(
                path="src/app.py",
                language="python",
                content="print('hello')\n",
            ),
        ),
        warnings=(
            make_export_warning(
                "Example warning",
                path="src/app.py",
                code="example",
            ),
        ),
    )


def test_repository_export_to_json_returns_parseable_deterministic_json():
    export = make_export()

    first = repository_export_to_json(export)
    second = repository_export_to_json(export)

    assert first == second

    data = json.loads(first)
    assert data["mode"] == "full"
    assert data["repository"]["root_name"] == "repo"
    assert data["files"][0]["path"] == "src/app.py"
    assert data["files"][0]["content"] == "print('hello')\n"


def test_repository_export_to_json_can_omit_content_fields():
    export = make_export()

    data = json.loads(
        repository_export_to_json(
            export,
            include_content=False,
        )
    )

    assert "content" not in data["files"][0]
    assert "masked_content" not in data["files"][0]
    assert data["files"][0]["path"] == "src/app.py"


def test_repository_export_to_json_supports_compact_output():
    export = make_export()

    compact = repository_export_to_json(export, indent=None)

    assert "\n" not in compact
    assert json.loads(compact)["mode"] == "full"


def test_repository_export_fingerprint_is_stable_and_content_sensitive():
    export = make_export()

    with_content = repository_export_fingerprint(export)
    without_content = repository_export_fingerprint(
        export,
        include_content=False,
    )

    assert len(with_content) == 64
    assert with_content == repository_export_fingerprint(export)
    assert with_content != without_content


def test_repository_export_fingerprint_rejects_unknown_algorithm():
    with pytest.raises(ValueError, match="unsupported fingerprint algorithm"):
        repository_export_fingerprint(make_export(), algorithm="unknown-hash")


def test_repository_export_snapshot_header_is_compact_and_deterministic():
    export = make_export()

    header = repository_export_snapshot_header(export)

    assert header == {
        "fingerprint": repository_export_fingerprint(export),
        "file_count": 1,
        "mode": "full",
        "root_name": "repo",
        "warning_count": 1,
    }


def test_repository_export_snapshot_lines_returns_json_lines():
    lines = repository_export_snapshot_lines(make_export())

    assert lines[0] == "{"
    assert lines[-1] == "}"
    assert any('"mode": "full"' in line for line in lines)
    assert json.loads("\n".join(lines))["repository"]["root_name"] == "repo"
