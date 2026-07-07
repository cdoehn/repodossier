from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_repodossier_exports.sh"


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def _write_fake_repodossier(bin_dir: Path) -> None:
    fake = bin_dir / "repodossier"
    fake.write_text(
        """#!/usr/bin/env bash
set -u

case "${1:-}" in
  full)
    echo "fake full export"
    printf 'new full from %s\\n' "$(pwd)" > full.txt
    ;;
  export-ai)
    echo "fake ai export"
    printf 'new ai from %s\\n' "$(pwd)" > ai.txt
    ;;
  *)
    echo "unexpected command: ${1:-}" >&2
    exit 9
    ;;
esac
""",
        encoding="utf-8",
    )
    fake.chmod(0o755)


def _run_r_runner(target_repo: Path, download_dir: Path, fake_bin_dir: Path):
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env["PATH"] = f"{fake_bin_dir}:{env['PATH']}"

    return subprocess.run(
        [str(RUNNER)],
        cwd=target_repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_r_runner_runs_repodossier_in_current_repo_and_copies_exports(tmp_path: Path) -> None:
    target_repo = tmp_path / "target_repo"
    target_repo.mkdir()
    _git_init(target_repo)

    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    _write_fake_repodossier(fake_bin_dir)

    result = _run_r_runner(target_repo, download_dir, fake_bin_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (target_repo / "full.txt").exists()
    assert (target_repo / "ai.txt").exists()
    assert (download_dir / "full.txt").read_text(encoding="utf-8").startswith("new full")
    assert (download_dir / "ai.txt").read_text(encoding="utf-8").startswith("new ai")
    assert str(target_repo) in (download_dir / "full.txt").read_text(encoding="utf-8")
    assert "r · RepoDossier Export Runner" in result.stdout
    assert "Kopiert" in result.stdout


def test_r_runner_overwrites_existing_download_exports(tmp_path: Path) -> None:
    target_repo = tmp_path / "target_repo"
    target_repo.mkdir()
    _git_init(target_repo)

    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    (download_dir / "full.txt").write_text("old full\n", encoding="utf-8")
    (download_dir / "ai.txt").write_text("old ai\n", encoding="utf-8")

    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    _write_fake_repodossier(fake_bin_dir)

    result = _run_r_runner(target_repo, download_dir, fake_bin_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "old full" not in (download_dir / "full.txt").read_text(encoding="utf-8")
    assert "old ai" not in (download_dir / "ai.txt").read_text(encoding="utf-8")
    assert "new full" in (download_dir / "full.txt").read_text(encoding="utf-8")
    assert "new ai" in (download_dir / "ai.txt").read_text(encoding="utf-8")


def test_r_runner_fails_outside_git_repo(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    _write_fake_repodossier(fake_bin_dir)

    result = _run_r_runner(tmp_path, download_dir, fake_bin_dir)

    assert result.returncode == 1
    assert "nicht in einem Git-Repository" in result.stdout


def test_r_runner_fails_when_repodossier_command_is_missing(tmp_path: Path) -> None:
    target_repo = tmp_path / "target_repo"
    target_repo.mkdir()
    _git_init(target_repo)

    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env["REPODOSSIER_BIN"] = "definitely-missing-repodossier-command"

    result = subprocess.run(
        [str(RUNNER)],
        cwd=target_repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "RepoDossier-Befehl nicht gefunden" in result.stdout
