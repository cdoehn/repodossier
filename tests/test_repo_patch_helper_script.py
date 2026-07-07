"""Repository-local patch helper smoke tests."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


HELPER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "repo_patch_helper.py"


def _load_helper_module():
    spec = importlib.util.spec_from_file_location(
        "repo_patch_helper_under_test",
        HELPER_PATH,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_repo_patch_helper_exists_in_repository_scripts_dev() -> None:
    assert HELPER_PATH.exists()
    assert HELPER_PATH.name == "repo_patch_helper.py"


def test_repo_patch_helper_exports_core_text_helpers(tmp_path: Path) -> None:
    helper = _load_helper_module()

    target = tmp_path / "sample.txt"
    helper.write_text(target, "alpha beta")

    assert helper.read_text(target) == "alpha beta\n"
    assert helper.replace_once_text("alpha beta", "alpha", "ALPHA") == "ALPHA beta"


def test_repo_patch_helper_collects_existing_paths_only(tmp_path: Path) -> None:
    helper = _load_helper_module()

    existing = tmp_path / "exists.py"
    existing.write_text("print('ok')\n", encoding="utf-8")

    collected = helper.collect_existing(
        ("exists.py", "missing.py"),
        cwd=tmp_path,
    )

    assert collected == ["exists.py"]


def test_repo_patch_helper_cli_smoke() -> None:
    result = subprocess.run(
        [sys.executable, str(HELPER_PATH), "smoke"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "repo_patch_helper.py smoke OK" in result.stdout


def test_repo_patch_helper_cli_footer() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(HELPER_PATH),
            "footer",
            "--done",
            "X|Done task|Commit message|",
            "--task",
            "Y",
            "--title",
            "Current task",
            "--next",
            "Z|Next task",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Erledigt:" in result.stdout
    assert "Aktuell:" in result.stdout
    assert "Danach:" in result.stdout
