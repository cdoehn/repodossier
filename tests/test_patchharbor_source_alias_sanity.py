from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/dev/install_aliases.sh"


def run_installer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(INSTALLER), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_alias_dry_run_prints_all_expected_aliases_without_writing_rc(tmp_path: Path) -> None:
    rc_file = tmp_path / "bashrc"

    result = run_installer("--repo", str(ROOT), "--rc-file", str(rc_file), "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "alias rdrepo=" in result.stdout
    assert "alias c=" in result.stdout
    assert "scripts/dev/run_latest_download_patch.sh" in result.stdout
    assert "alias r=" in result.stdout
    assert "scripts/dev/r.sh" in result.stdout
    assert "alias patchharbor-patch=" in result.stdout
    assert "scripts/dev/run_patchharbor_patch.sh" in result.stdout
    assert "REPODOSSIER_REPO=" in result.stdout
    assert not rc_file.exists()


def test_alias_dry_run_preserves_legacy_c_and_r_targets(tmp_path: Path) -> None:
    rc_file = tmp_path / "bashrc"

    result = run_installer("--repo", str(ROOT), "--rc-file", str(rc_file), "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "run_latest_download_patch.sh" in result.stdout
    assert "run_patchharbor_patch.sh" in result.stdout
    assert result.stdout.find("alias c=") < result.stdout.find("alias patchharbor-patch=")
    assert "scripts/dev/run_repodossier_exports.sh" not in result.stdout


def test_alias_installer_help_mentions_patchharbor_patch_but_not_as_c_replacement() -> None:
    result = run_installer("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "patchharbor-patch" in result.stdout
    assert "run an explicit patch file through PatchHarbor" in result.stdout
    assert "c       run the download patch runner" in result.stdout


def test_alias_sanity_files_have_no_private_values() -> None:
    checked = [
        ROOT / "tests/test_patchharbor_source_alias_sanity.py",
        ROOT / "scripts/dev/install_aliases.sh",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
    forbidden = [
        "/home/" + "christian",
        "christian" + "@",
        "christian.doehn" + "@" + "gmail.com",
        "Think" + "Pad",
        "~/" + "Projekte",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text
