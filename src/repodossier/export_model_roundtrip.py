"""Round-trip checks for RepoDossier's structured export model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from repodossier.export_model import RepositoryExport
from repodossier.export_model_deserialization import repository_export_from_dict
from repodossier.export_model_serialization import repository_export_to_dict
from repodossier.export_model_snapshot import repository_export_fingerprint


@dataclass(frozen=True)
class RepositoryExportRoundTripStatus:
    """Result of a RepositoryExport serialization round-trip check."""

    valid: bool
    issues: tuple[str, ...]
    before_fingerprint: str
    after_fingerprint: str
    same_fingerprint: bool


class RepositoryExportRoundTripError(AssertionError):
    """Raised when a RepositoryExport does not round-trip cleanly."""


def repository_export_round_trip(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    validate: bool = True,
) -> RepositoryExport:
    """Serialize an export to plain data and deserialize it again."""

    return repository_export_from_dict(
        repository_export_to_dict(
            export,
            include_content=include_content,
        ),
        validate=validate,
    )


def repository_export_canonical_dict(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    validate: bool = True,
) -> dict[str, Any]:
    """Return a canonical dict after one serialization round trip."""

    restored = repository_export_round_trip(
        export,
        include_content=include_content,
        validate=validate,
    )
    return repository_export_to_dict(
        restored,
        include_content=include_content,
    )


def repository_export_round_trip_status(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    validate: bool = True,
) -> RepositoryExportRoundTripStatus:
    """Return detailed status for a RepositoryExport round-trip check."""

    issues: list[str] = []

    before_data = repository_export_to_dict(
        export,
        include_content=include_content,
    )
    before_fingerprint = repository_export_fingerprint(
        export,
        include_content=include_content,
    )

    try:
        restored = repository_export_from_dict(
            before_data,
            validate=validate,
        )
    except Exception as exc:
        return RepositoryExportRoundTripStatus(
            valid=False,
            issues=(f"deserialization failed: {exc}",),
            before_fingerprint=before_fingerprint,
            after_fingerprint="",
            same_fingerprint=False,
        )

    after_data = repository_export_to_dict(
        restored,
        include_content=include_content,
    )
    after_fingerprint = repository_export_fingerprint(
        restored,
        include_content=include_content,
    )

    if before_data != after_data:
        issues.append("serialized data changed after round trip")

    if before_fingerprint != after_fingerprint:
        issues.append("fingerprint changed after round trip")

    return RepositoryExportRoundTripStatus(
        valid=not issues,
        issues=tuple(issues),
        before_fingerprint=before_fingerprint,
        after_fingerprint=after_fingerprint,
        same_fingerprint=before_fingerprint == after_fingerprint,
    )


def assert_repository_export_round_trips(
    export: RepositoryExport,
    *,
    include_content: bool = True,
    validate: bool = True,
) -> None:
    """Raise if a RepositoryExport does not round-trip cleanly."""

    status = repository_export_round_trip_status(
        export,
        include_content=include_content,
        validate=validate,
    )

    if status.valid:
        return

    formatted = "\n".join(f"- {issue}" for issue in status.issues)
    raise RepositoryExportRoundTripError(
        f"RepositoryExport does not round-trip cleanly:\n{formatted}"
    )
