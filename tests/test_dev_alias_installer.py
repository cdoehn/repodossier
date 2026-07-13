from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "dev" / "install_aliases.sh"


def run_installer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(INSTALLER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_alias_installer_dry_run_mentions_supported_aliases(tmp_path: Path) -> None:
    result = run_installer("--repo", str(ROOT), "--rc-file", str(tmp_path / "rc"), "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "alias rdrepo=" in result.stdout
    assert "alias c=" in result.stdout
    assert "alias r=" in result.stdout
    assert "REPODOSSIER_REPO=" in result.stdout


def test_alias_installer_updates_managed_block_idempotently(tmp_path: Path) -> None:
    rc_file = tmp_path / "bashrc"
    for _ in range(2):
        result = run_installer("--repo", str(ROOT), "--rc-file", str(rc_file))
        assert result.returncode == 0, result.stdout + result.stderr

    text = rc_file.read_text(encoding="utf-8")
    assert text.count("# >>> repodossier dev aliases >>>") == 1
    assert text.count("# <<< repodossier dev aliases <<<") == 1
    assert "scripts/dev/run_latest_download_patch.sh" in text
    assert "scripts/dev/r.sh" in text


def test_alias_installer_rejects_non_repo(tmp_path: Path) -> None:
    result = run_installer("--repo", str(tmp_path), "--rc-file", str(tmp_path / "rc"))

    assert result.returncode == 1
    assert "Not a git repository" in result.stderr


def test_alias_installer_help_lists_supported_aliases_only() -> None:
    result = run_installer("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "rdrepo" in result.stdout
    assert "c       run the download patch runner" in result.stdout
    assert "r       run the export runner" in result.stdout


def test_alias_installer_dry_run_does_not_write_shell_rc_file(tmp_path: Path) -> None:
    rc_file = tmp_path / "bashrc"
    result = run_installer("--repo", str(ROOT), "--rc-file", str(rc_file), "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not rc_file.exists()
