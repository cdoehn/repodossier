"""Deterministic snapshot helpers for RepoDossier's export model."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from repodossier.export_model import RepositoryExport
from repodossier.export_model_serialization import repository_export_to_dict


def repository_export_to_json(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    indent: int | None = 2,
) -> str:
    """Serialize an export model to deterministic JSON text."""

    data = repository_export_to_dict(
        export,
        include_content=include_content,
    )
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
    )


def repository_export_fingerprint(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    algorithm: str = "sha256",
) -> str:
    """Return a deterministic content fingerprint for an export model."""

    payload = repository_export_to_json(
        export,
        include_content=include_content,
        indent=None,
    ).encode("utf-8")

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"unsupported fingerprint algorithm: {algorithm}") from exc

    digest.update(payload)
    return digest.hexdigest()


def repository_export_snapshot_header(
    export: RepositoryExport,
    *,
    include_content: bool = True,
) -> dict[str, Any]:
    """Return compact deterministic metadata for snapshot comparisons."""

    return {
        "fingerprint": repository_export_fingerprint(
            export,
            include_content=include_content,
        ),
        "file_count": len(export.files),
        "mode": export.mode,
        "root_name": export.repository.root_name,
        "warning_count": len(export.warnings),
    }


def repository_export_snapshot_lines(
    export: RepositoryExport,
    *,
    include_content: bool = True,
) -> tuple[str, ...]:
    """Return deterministic JSON as lines for snapshot-style tests."""

    return tuple(
        repository_export_to_json(
            export,
            include_content=include_content,
            indent=2,
        ).splitlines()
    )
