from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

from repodossier.cli import main

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    assert _git(path, "init").returncode == 0
    assert _git(path, "config", "user.name", "Example User").returncode == 0
    assert _git(path, "config", "user.email", "example@example.invalid").returncode == 0
    return path


def _names(archive_path: Path) -> set[str]:
    with zipfile.ZipFile(archive_path) as archive:
        return set(archive.namelist())


def _text(archive_path: Path, name: str) -> str:
    with zipfile.ZipFile(archive_path) as archive:
        return archive.read(name).decode("utf-8")


def test_end_to_end_archive_cli_creates_zip_with_reports_and_snapshot(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "projekt")
    output = tmp_path / "output"
    src = repo / "src" / "backend"
    src.mkdir(parents=True)
    (src / "main.py").write_text("VALUE = 'visible working tree'\n", encoding="utf-8")
    (repo / "README.md").write_text("# Projekt\n", encoding="utf-8")
    (repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (repo / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    assert _git(repo, "add", "README.md", "src/backend/main.py", ".gitignore").returncode == 0
    assert _git(repo, "commit", "-m", "initial").returncode == 0
    (src / "main.py").write_text("VALUE = 'unstaged visible working tree'\n", encoding="utf-8")

    exit_code = main([str(src), str(output), "--output-name", "projektpaket.xml"])

    assert exit_code == 0
    archive_path = output / "projektpaket.xml"
    assert zipfile.is_zipfile(archive_path)
    names = _names(archive_path)
    assert "reports/archive-manifest.txt" in names
    assert "reports/full.txt" in names
    assert "reports/ai.txt" in names
    assert "reports/docs.txt" in names
    assert "reports/changed.txt" in names
    assert "reports/source-references.txt" in names
    assert "reports/source-references.md" in names
    assert "reports/source-references.xml" in names
    assert "repositories/projekt/src/backend/main.py" in names
    assert "repositories/projekt/README.md" in names
    assert "repositories/projekt/untracked.txt" not in names
    assert "repositories/projekt/ignored.txt" not in names
    assert not any(name.startswith("repositories/projekt/.git/") for name in names)
    assert all("output/" not in name for name in names)

    assert _text(archive_path, "repositories/projekt/src/backend/main.py") == "VALUE = 'visible working tree'\n"
    report = _text(archive_path, "reports/source-references.txt")
    assert "Source file: src/backend/main.py" in report
    assert "Archive path: ../repositories/projekt/src/backend/main.py" in report
    assert "unstaged visible working tree" not in report
    assert "unstaged visible working tree" in _text(archive_path, "reports/full.txt")
    assert "src/backend/main.py" in _text(archive_path, "reports/ai.txt")
    assert "README.md" in _text(archive_path, "reports/docs.txt")
    assert "unstaged visible working tree" in _text(archive_path, "reports/changed.txt")


def test_end_to_end_archive_cli_supports_multiple_repositories(tmp_path: Path) -> None:
    repo_a = _git_init(tmp_path / "repo-a")
    repo_b = _git_init(tmp_path / "repo-b")
    (repo_a / "a.py").write_text("A = 1\n", encoding="utf-8")
    (repo_b / "b.py").write_text("B = 2\n", encoding="utf-8")
    assert _git(repo_a, "add", "a.py").returncode == 0
    assert _git(repo_b, "add", "b.py").returncode == 0
    assert _git(repo_a, "commit", "-m", "snapshot").returncode == 0
    assert _git(repo_b, "commit", "-m", "snapshot").returncode == 0

    exit_code = main([str(repo_a), str(repo_b), str(tmp_path / "out")])

    assert exit_code == 0
    archive_path = tmp_path / "out" / "repodossier.zip"
    names = _names(archive_path)
    assert "repositories/repo-a/a.py" in names
    assert "repositories/repo-b/b.py" in names
    manifest = _text(archive_path, "reports/archive-manifest.txt")
    assert "Repositories: 2" in manifest


def test_existing_archive_is_not_overwritten_and_no_temp_archive_remains(tmp_path: Path, capsys) -> None:
    repo = _git_init(tmp_path / "repo")
    (repo / "a.py").write_text("A = 1\n", encoding="utf-8")
    assert _git(repo, "add", "a.py").returncode == 0
    output = tmp_path / "out"
    output.mkdir()
    target = output / "already.zip"
    target.write_text("keep me", encoding="utf-8")

    exit_code = main([str(repo), str(output), "--output-name", "already.zip"])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "already exists" in captured.err
    assert target.read_text(encoding="utf-8") == "keep me"
    assert not list(output.glob(".*.tmp-*"))


def test_module_cli_help_and_archive_call_work_from_subprocess(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "repo")
    (repo / "app.py").write_text("print('ok')\n", encoding="utf-8")
    assert _git(repo, "add", "app.py").returncode == 0
    assert _git(repo, "commit", "-m", "snapshot").returncode == 0
    output = tmp_path / "out"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(SRC_ROOT), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)

    help_result = subprocess.run(
        [sys.executable, "-m", "repodossier", "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert help_result.returncode == 0
    assert "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER" in help_result.stdout

    run_result = subprocess.run(
        [sys.executable, "-m", "repodossier", str(repo), str(output), "--output-name", "subprocess.zip"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert run_result.returncode == 0, run_result.stderr
    assert zipfile.is_zipfile(output / "subprocess.zip")
