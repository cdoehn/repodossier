from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "dev" / "install_aliases.sh"


def test_alias_installer_dry_run_mentions_aliases(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(INSTALLER), "--repo", str(ROOT), "--rc-file", str(tmp_path / "rc"), "--dry-run"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "alias rdrepo=" in result.stdout
    assert "alias c=" in result.stdout
    assert "alias r=" in result.stdout
    assert "alias patchharbor-patch=" in result.stdout
    assert "scripts/dev/run_patchharbor_patch.sh" in result.stdout
    assert "REPODOSSIER_REPO=" in result.stdout


def test_alias_installer_updates_managed_block_idempotently(tmp_path: Path) -> None:
    rc_file = tmp_path / "bashrc"

    for _ in range(2):
        result = subprocess.run(
            [str(INSTALLER), "--repo", str(ROOT), "--rc-file", str(rc_file)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    text = rc_file.read_text(encoding="utf-8")
    assert text.count("# >>> repodossier dev aliases >>>") == 1
    assert text.count("# <<< repodossier dev aliases <<<") == 1
    assert "scripts/dev/run_latest_download_patch.sh" in text
    assert "scripts/dev/r.sh" in text
    assert "alias c=" in text
    assert "alias r=" in text
    assert "alias patchharbor-patch=" in text
    assert "scripts/dev/run_patchharbor_patch.sh" in text


def test_alias_installer_rejects_non_repo(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(INSTALLER), "--repo", str(tmp_path), "--rc-file", str(tmp_path / "rc")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Not a git repository" in result.stderr


def test_alias_installer_preserves_c_and_r_when_adding_patchharbor_alias(tmp_path: Path) -> None:
    rc_file = tmp_path / "bashrc"
    result = subprocess.run(
        [str(INSTALLER), "--repo", str(ROOT), "--rc-file", str(rc_file)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    text = rc_file.read_text(encoding="utf-8")
    assert "alias c=" in text
    assert "scripts/dev/run_latest_download_patch.sh" in text
    assert "alias r=" in text
    assert "scripts/dev/r.sh" in text
    assert "alias patchharbor-patch=" in text
    assert "scripts/dev/run_patchharbor_patch.sh" in text

def test_alias_installer_help_mentions_patchharbor_alias() -> None:
    result = subprocess.run(
        [str(INSTALLER), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "patchharbor-patch" in result.stdout
    assert "PatchHarbor" in result.stdout


def test_alias_installer_dry_run_does_not_write_shell_rc_file(tmp_path: Path) -> None:
    rc_file = tmp_path / "bashrc"
    result = subprocess.run(
        [str(INSTALLER), "--repo", str(ROOT), "--rc-file", str(rc_file), "--dry-run"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not rc_file.exists()
    assert "alias patchharbor-patch=" in result.stdout
