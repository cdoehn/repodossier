#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

RULE_ID_RE = re.compile(r"^[A-Z]+-[0-9]{3}$")
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_rules(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("version") != 1:
        errors.append("version must be 1")

    categories = data.get("categories")
    if not isinstance(categories, list) or not categories:
        errors.append("categories must be a non-empty list")
        categories = []
    category_set = set()
    for category in categories:
        if not isinstance(category, str) or not NAME_RE.match(category):
            errors.append(f"invalid category: {category!r}")
            continue
        if category in category_set:
            errors.append(f"duplicate category: {category}")
        category_set.add(category)

    if data.get("severities") != ["must", "should", "may"]:
        errors.append('severities must be ["must", "should", "may"]')

    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty list")
        return errors

    required = {"id", "category", "severity", "title", "description", "rationale", "applies_to", "checks"}
    allowed = required | {"examples"}
    seen_ids = set()

    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            errors.append(f"rule #{index} must be an object")
            continue
        for field in sorted(required - rule.keys()):
            errors.append(f"rule #{index} missing field: {field}")
        for field in sorted(rule.keys() - allowed):
            errors.append(f"rule #{index} unknown field: {field}")

        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not RULE_ID_RE.match(rule_id):
            errors.append(f"rule #{index} has invalid id: {rule_id!r}")
        elif rule_id in seen_ids:
            errors.append(f"duplicate rule id: {rule_id}")
        else:
            seen_ids.add(rule_id)

        category = rule.get("category")
        if not isinstance(category, str) or category not in category_set:
            errors.append(f"rule {rule_id or index} references unknown category: {category!r}")

        if rule.get("severity") not in {"must", "should", "may"}:
            errors.append(f"rule {rule_id or index} has invalid severity")

        for field in ("title", "description", "rationale"):
            value = rule.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"rule {rule_id or index} field {field} must be a non-empty string")

        applies_to = rule.get("applies_to")
        if not isinstance(applies_to, list) or not applies_to:
            errors.append(f"rule {rule_id or index} applies_to must be a non-empty list")
        else:
            for target in applies_to:
                if not isinstance(target, str) or not NAME_RE.match(target):
                    errors.append(f"rule {rule_id or index} has invalid applies_to target: {target!r}")

        checks = rule.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append(f"rule {rule_id or index} checks must be a non-empty list")
        else:
            for check in checks:
                if not isinstance(check, str) or not check.strip():
                    errors.append(f"rule {rule_id or index} checks must contain non-empty strings")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate normalized RepoDossier patch workflow rules.")
    parser.add_argument("--rules", type=Path, default=Path("scripts/dev/patch-workflow-rules.json"))
    parser.add_argument("--schema", type=Path, default=Path("scripts/dev/patch-workflow-rules.schema.json"))
    args = parser.parse_args(argv)

    try:
        rules = _load_json(args.rules)
        schema = _load_json(args.schema)
    except Exception as exc:
        print(f"Patch workflow rules invalid: {exc}")
        return 10

    errors = []
    if not isinstance(schema, dict) or schema.get("title") != "RepoDossier patch workflow rules":
        errors.append("schema title mismatch")
    if not isinstance(rules, dict):
        errors.append("rules root must be an object")
    else:
        errors.extend(validate_rules(rules))

    if errors:
        print("Patch workflow rules invalid:")
        for error in errors:
            print(f"  - {error}")
        return 10

    print("Patch workflow rules OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
