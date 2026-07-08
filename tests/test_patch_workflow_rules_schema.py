from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "scripts" / "dev" / "patch-workflow-rules.json"
SCHEMA = ROOT / "scripts" / "dev" / "patch-workflow-rules.schema.json"
VALIDATOR = ROOT / "scripts" / "dev" / "validate_patch_workflow_rules.py"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_patch_workflow_schema_and_rules_are_valid_json() -> None:
    schema = _load(SCHEMA)
    rules = _load(RULES)
    assert schema["title"] == "RepoDossier patch workflow rules"
    assert schema["type"] == "object"
    assert rules["version"] == 1
    assert rules["rules"]


def test_patch_workflow_rules_have_unique_ids_and_known_categories() -> None:
    rules = _load(RULES)
    categories = set(rules["categories"])
    ids = [rule["id"] for rule in rules["rules"]]
    assert len(ids) == len(set(ids))
    assert {"metadata", "safety", "tests", "git", "runner"}.issubset(categories)
    for rule in rules["rules"]:
        assert rule["category"] in categories
        assert rule["severity"] in {"must", "should", "may"}
        assert rule["title"].strip()
        assert rule["description"].strip()
        assert rule["rationale"].strip()
        assert rule["applies_to"]
        assert rule["checks"]


def test_patch_workflow_rules_validator_accepts_repo_rules() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--rules", str(RULES), "--schema", str(SCHEMA)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Patch workflow rules OK" in result.stdout


def test_patch_workflow_rules_validator_rejects_duplicate_ids(tmp_path: Path) -> None:
    rules = _load(RULES)
    rules["rules"][1]["id"] = rules["rules"][0]["id"]
    broken = tmp_path / "rules.json"
    broken.write_text(json.dumps(rules), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--rules", str(broken), "--schema", str(SCHEMA)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 10
    assert "duplicate rule id" in result.stdout
