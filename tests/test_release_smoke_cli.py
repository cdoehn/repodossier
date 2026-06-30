import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"


def _repodossier_command() -> list[str]:
    executable = shutil.which("repodossier")
    if executable:
        return [executable]

    return [
        sys.executable,
        "-c",
        "import sys; from repodossier.cli import main; raise SystemExit(main())",
    ]


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    pythonpath_parts = [str(SRC_ROOT)]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    result = subprocess.run(
        _repodossier_command() + args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    return result


def _git(args: list[str], cwd: Path) -> None:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout


def _create_smoke_repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git is required for release smoke tests")

    repo = tmp_path / "smoke_repo"
    repo.mkdir()

    (repo / "src").mkdir()
    (repo / "scripts").mkdir()
    (repo / "docs").mkdir()

    (repo / "README.md").write_text(
        "# Smoke README\n\nThis repository validates RepoDossier release smoke exports.\n",
        encoding="utf-8",
    )

    (repo / "pyproject.toml").write_text(
        "[project]\n"
        "name = \"smoke-repo\"\n"
        "version = \"0.1.0\"\n",
        encoding="utf-8",
    )

    (repo / "src" / "example.py").write_text(
        "import math\n\n"
        "class Greeter:\n"
        "    def greet(self, name: str) -> str:\n"
        "        return f\"Hello, {name}\"\n\n"
        "def area(radius: float) -> float:\n"
        "    return math.pi * radius * radius\n\n"
        "def main() -> str:\n"
        "    return Greeter().greet(\"RepoDossier\")\n",
        encoding="utf-8",
    )

    (repo / "scripts" / "build.sh").write_text(
        "#!/usr/bin/env bash\n\n"
        "say_hello() {\n"
        "  echo \"hello from bash\"\n"
        "}\n\n"
        "main() {\n"
        "  say_hello\n"
        "}\n\n"
        "main \"$@\"\n",
        encoding="utf-8",
    )

    (repo / "docs" / "SPEC.md").write_text(
        "# Smoke Spec\n\nThe smoke spec is included in docs exports.\n",
        encoding="utf-8",
    )

    _git(["init"], cwd=repo)
    _git(["config", "user.email", "smoke@example.invalid"], cwd=repo)
    _git(["config", "user.name", "RepoDossier Smoke Test"], cwd=repo)
    _git(["add", "."], cwd=repo)
    _git(["commit", "-m", "Initial smoke repo"], cwd=repo)

    return repo


def _read_export(repo: Path, filename: str) -> str:
    export_path = repo / filename
    assert export_path.exists(), f"Expected export file was not created: {filename}"
    text = export_path.read_text(encoding="utf-8")
    assert text.strip(), f"Expected export file to be non-empty: {filename}"
    return text


def test_release_smoke_full_export_creates_full_txt(tmp_path: Path) -> None:
    repo = _create_smoke_repo(tmp_path)

    _run(["full"], cwd=repo)

    text = _read_export(repo, "full.txt")
    assert "Smoke README" in text
    assert "src/example.py" in text
    assert "scripts/build.sh" in text


def test_release_smoke_ai_export_creates_ai_txt(tmp_path: Path) -> None:
    repo = _create_smoke_repo(tmp_path)

    _run(["export-ai"], cwd=repo)

    text = _read_export(repo, "ai.txt")
    assert "src/example.py" in text
    assert "Greeter" in text or "area" in text


def test_release_smoke_docs_export_creates_docs_txt(tmp_path: Path) -> None:
    repo = _create_smoke_repo(tmp_path)

    _run(["export-docs"], cwd=repo)

    text = _read_export(repo, "docs.txt")
    assert "Smoke README" in text
    assert "Smoke Spec" in text


def test_release_smoke_changed_export_creates_changed_txt(tmp_path: Path) -> None:
    repo = _create_smoke_repo(tmp_path)

    example_path = repo / "src" / "example.py"
    example_path.write_text(
        example_path.read_text(encoding="utf-8")
        + "\n\ndef changed_name() -> str:\n"
        + "    return \"changed\"\n",
        encoding="utf-8",
    )

    _run(["changed"], cwd=repo)

    text = _read_export(repo, "changed.txt")
    assert "src/example.py" in text
    assert "changed_name" in text
