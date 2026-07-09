from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "planning/patchharbor/source-runner-adoption-acceptance.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_source_runner_adoption_acceptance_document_exists() -> None:
    text = read(ACCEPTANCE)

    assert "Source-side runner adoption acceptance" in text
    assert "PATCHHARBOR.09f1" in text
    assert "patchharbor-patch" in text
    assert "not a replacement for `c`" in text
    assert "claim download runner parity" in text
    assert "claim export runner parity" in text


def test_source_runner_adoption_artifacts_exist() -> None:
    required = [
        "scripts/dev/run_patchharbor_patch.sh",
        "tests/test_patchharbor_runner_wrapper.py",
        "tests/test_patchharbor_runner_wrapper_smoke.py",
        "scripts/dev/install_aliases.sh",
        "tests/test_dev_alias_installer.py",
        "planning/patchharbor/c-alias-contract.md",
        "planning/patchharbor/c-alias-switch-criteria.md",
        "tests/test_c_alias_switch_plan.py",
    ]
    for relative in required:
        assert (ROOT / relative).exists(), relative


def test_old_source_runners_are_preserved() -> None:
    required = [
        "scripts/dev/run_latest_download_patch.sh",
        "scripts/dev/r.sh",
        "scripts/dev/run_repodossier_exports.sh",
    ]
    for relative in required:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.read_text(encoding="utf-8").strip(), relative


def test_alias_installer_keeps_patchharbor_patch_additive() -> None:
    installer = read(ROOT / "scripts/dev/install_aliases.sh")

    assert "alias c=" in installer
    assert "scripts/dev/run_latest_download_patch.sh" in installer
    assert "alias r=" in installer
    assert "scripts/dev/r.sh" in installer
    assert "alias patchharbor-patch=" in installer
    assert "scripts/dev/run_patchharbor_patch.sh" in installer


def test_patchharbor_wrapper_is_thin_explicit_path() -> None:
    wrapper = read(ROOT / "scripts/dev/run_patchharbor_patch.sh")

    assert 'exec patchharbor run-script "$@"' in wrapper
    assert "run_latest_download_patch" not in wrapper
    assert "run_repodossier_exports" not in wrapper


def test_c_switch_is_documented_as_future_controlled_step() -> None:
    contract = read(ROOT / "planning/patchharbor/c-alias-contract.md")
    criteria = read(ROOT / "planning/patchharbor/c-alias-switch-criteria.md")

    assert "`c` is not switched yet" in contract
    assert "This patch does not switch `c`" in criteria
    assert "one-command rollback" in criteria
    assert "metadata validation parity is tested" in criteria
    assert "successful patch lifecycle parity is tested" in criteria


def test_source_runner_adoption_acceptance_files_have_no_private_values() -> None:
    checked = [
        ACCEPTANCE,
        ROOT / "tests/test_source_runner_adoption_acceptance.py",
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
