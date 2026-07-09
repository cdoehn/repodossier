#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PREFIX = "# repodossier-meta:"
ALLOWED_TYPES = {"patch", "progress", "display"}
ALLOWED_PATCH_FIELDS = {"type", "id", "title", "commit", "fix_for", "requires_direct_bash"}
ALLOWED_PROGRESS_FIELDS = {"type", "panel", "status", "file", "start", "end", "anchor", "label"}
ALLOWED_DISPLAY_FIELDS = {"type", "context", "layout", "frame", "progress_context"}
ALLOWED_PANELS = {"roadmap", "milestone"}
ALLOWED_STATUSES = {"done", "active", "partial", "todo"}
ALLOWED_LAYOUTS = {"side-by-side", "stacked"}


@dataclass(frozen=True)
class MetaRecord:
    line_number: int
    data: dict[str, Any]


def _error(line: int | None, message: str) -> str:
    if line is None:
        return message
    return f"line {line}: {message}"


def parse_metadata_lines(script_path: Path) -> tuple[list[MetaRecord], list[str]]:
    records: list[MetaRecord] = []
    errors: list[str] = []

    try:
        lines = script_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        return [], [f"cannot read script as UTF-8: {exc}"]

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith(PREFIX):
            continue

        payload = stripped[len(PREFIX) :].strip()
        if not payload:
            errors.append(_error(line_number, "empty repodossier-meta payload"))
            continue

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            errors.append(_error(line_number, f"invalid JSON: {exc.msg}"))
            continue

        if not isinstance(decoded, dict):
            errors.append(_error(line_number, "metadata payload must be a JSON object"))
            continue

        records.append(MetaRecord(line_number=line_number, data=decoded))

    return records, errors


def _require_string(
    record: MetaRecord,
    errors: list[str],
    key: str,
    *,
    allow_empty: bool = False,
) -> None:
    value = record.data.get(key)
    if not isinstance(value, str):
        errors.append(_error(record.line_number, f'missing or invalid string field "{key}"'))
        return
    if not allow_empty and not value.strip():
        errors.append(_error(record.line_number, f'field "{key}" must not be empty'))


def _require_bool(record: MetaRecord, errors: list[str], key: str) -> None:
    if key in record.data and not isinstance(record.data[key], bool):
        errors.append(_error(record.line_number, f'field "{key}" must be a boolean'))


def _require_int(record: MetaRecord, errors: list[str], key: str, *, minimum: int = 1) -> None:
    value = record.data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(_error(record.line_number, f'missing or invalid integer field "{key}"'))
        return
    if value < minimum:
        errors.append(_error(record.line_number, f'field "{key}" must be >= {minimum}'))


def _check_unknown_fields(record: MetaRecord, errors: list[str], allowed: set[str]) -> None:
    unknown = sorted(set(record.data) - allowed)
    for key in unknown:
        errors.append(_error(record.line_number, f'unknown field "{key}"'))


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def validate_records(
    records: list[MetaRecord],
    *,
    script_path: Path,
    repo_root: Path,
    require_metadata: bool = True,
) -> list[str]:
    errors: list[str] = []

    if not records:
        if require_metadata:
            errors.append("missing required repodossier-meta block")
        return errors

    patch_records = [record for record in records if record.data.get("type") == "patch"]
    progress_records = [record for record in records if record.data.get("type") == "progress"]
    display_records = [record for record in records if record.data.get("type") == "display"]

    if len(patch_records) != 1:
        errors.append(f"expected exactly one patch metadata record, found {len(patch_records)}")

    if len(display_records) > 1:
        errors.append(f"expected at most one display metadata record, found {len(display_records)}")

    requires_direct_bash = any(
        record.data.get("requires_direct_bash") is True for record in patch_records
    )
    if patch_records and not requires_direct_bash:
        progress_panels = {
            record.data.get("panel")
            for record in progress_records
            if isinstance(record.data.get("panel"), str)
        }
        if "roadmap" not in progress_panels:
            errors.append("missing required roadmap progress metadata record")
        if "milestone" not in progress_panels:
            errors.append("missing required milestone progress metadata record")

    for record in records:
        meta_type = record.data.get("type")
        if not isinstance(meta_type, str):
            errors.append(_error(record.line_number, 'missing or invalid string field "type"'))
            continue

        if meta_type not in ALLOWED_TYPES:
            errors.append(
                _error(
                    record.line_number,
                    f'type must be one of {sorted(ALLOWED_TYPES)}, got {meta_type!r}',
                )
            )
            continue

        if meta_type == "patch":
            _check_unknown_fields(record, errors, ALLOWED_PATCH_FIELDS)
            _require_string(record, errors, "id")
            _require_string(record, errors, "title")
            _require_string(record, errors, "commit")
            if "fix_for" in record.data:
                _require_string(record, errors, "fix_for")
            _require_bool(record, errors, "requires_direct_bash")

        elif meta_type == "progress":
            _check_unknown_fields(record, errors, ALLOWED_PROGRESS_FIELDS)
            _require_string(record, errors, "panel")
            _require_string(record, errors, "status")
            _require_string(record, errors, "file")

            has_start = "start" in record.data
            has_end = "end" in record.data
            has_anchor = "anchor" in record.data

            if has_start != has_end:
                errors.append(_error(record.line_number, '"start" and "end" must be provided together'))
            if not has_anchor and not (has_start and has_end):
                errors.append(_error(record.line_number, 'progress metadata must provide either "start"/"end" or "anchor"'))

            if has_start:
                _require_int(record, errors, "start")
            if has_end:
                _require_int(record, errors, "end")
            if has_anchor:
                _require_string(record, errors, "anchor")

            panel = record.data.get("panel")
            status = record.data.get("status")
            rel_file = record.data.get("file")
            start = record.data.get("start")
            end = record.data.get("end")
            anchor = record.data.get("anchor")

            if isinstance(panel, str) and panel not in ALLOWED_PANELS:
                errors.append(_error(record.line_number, f'panel must be one of {sorted(ALLOWED_PANELS)}'))

            if isinstance(status, str) and status not in ALLOWED_STATUSES:
                errors.append(_error(record.line_number, f'status must be one of {sorted(ALLOWED_STATUSES)}'))

            if isinstance(rel_file, str):
                if Path(rel_file).is_absolute() or "." in Path(rel_file).parts:
                    errors.append(_error(record.line_number, 'file must be a safe repo-relative path'))
                else:
                    full_path = repo_root / rel_file
                    if not full_path.exists():
                        errors.append(_error(record.line_number, f'file does not exist: {rel_file}'))
                    elif full_path.is_dir():
                        errors.append(_error(record.line_number, f'file is a directory: {rel_file}'))
                    else:
                        if isinstance(start, int) and isinstance(end, int) and start >= 1 and end >= 1:
                            if start > end:
                                errors.append(_error(record.line_number, "start must be <= end"))
                            else:
                                count = _line_count(full_path)
                                if end > count:
                                    errors.append(
                                        _error(
                                            record.line_number,
                                            f'end line {end} exceeds file length {count}: {rel_file}',
                                        )
                                    )

                        if isinstance(anchor, str) and anchor.strip():
                            file_text = full_path.read_text(encoding="utf-8")
                            if anchor not in file_text:
                                errors.append(_error(record.line_number, f'anchor not found in file: {anchor!r}'))

            if "label" in record.data:
                _require_string(record, errors, "label")

        elif meta_type == "display":
            _check_unknown_fields(record, errors, ALLOWED_DISPLAY_FIELDS)
            if "context" in record.data:
                _require_int(record, errors, "context", minimum=0)
                context = record.data.get("context")
                if isinstance(context, int) and context > 50:
                    errors.append(_error(record.line_number, 'field "context" must be <= 50'))
            if "layout" in record.data:
                _require_string(record, errors, "layout")
                layout = record.data.get("layout")
                if isinstance(layout, str) and layout not in ALLOWED_LAYOUTS:
                    errors.append(_error(record.line_number, f'layout must be one of {sorted(ALLOWED_LAYOUTS)}'))
            if "frame" in record.data and not isinstance(record.data["frame"], bool):
                errors.append(_error(record.line_number, 'field "frame" must be a boolean'))
            if "progress_context" in record.data and not isinstance(record.data["progress_context"], bool):
                errors.append(_error(record.line_number, 'field "progress_context" must be a boolean'))

    return errors


def validate_script(
    script_path: Path,
    *,
    repo_root: Path,
    require_metadata: bool = True,
) -> tuple[list[MetaRecord], list[str]]:
    records, parse_errors = parse_metadata_lines(script_path)
    validation_errors = validate_records(
        records,
        script_path=script_path,
        repo_root=repo_root,
        require_metadata=require_metadata,
    )
    return records, parse_errors + validation_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repodossier-meta lines in patch scripts.")
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--repo", default=Path.cwd(), type=Path)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    script_path = args.script.expanduser().resolve()
    repo_root = args.repo.expanduser().resolve()

    _records, errors = validate_script(
        script_path,
        repo_root=repo_root,
        require_metadata=not args.allow_missing,
    )

    if errors:
        if not args.quiet:
            print("Metadata invalid:")
            for error in errors:
                print(f"  - {error}")
        return 10

    if not args.quiet:
        print("Metadata OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
