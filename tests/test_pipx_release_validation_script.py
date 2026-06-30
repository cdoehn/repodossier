from pathlib import Path


def test_pipx_release_validation_script_exists_and_is_executable() -> None:
    script = Path("scripts/validate_pipx_release.sh")

    assert script.exists()
    assert script.stat().st_mode & 0o111


def test_pipx_release_validation_script_uses_isolated_pipx_home() -> None:
    text = Path("scripts/validate_pipx_release.sh").read_text(encoding="utf-8")

    assert "PIPX_HOME" in text
    assert "PIPX_BIN_DIR" in text
    assert "mktemp -d" in text
    assert "pipx install" in text or "-m pipx" in text


def test_pipx_release_validation_script_covers_release_exports() -> None:
    text = Path("scripts/validate_pipx_release.sh").read_text(encoding="utf-8")

    assert '"$CLI" full' in text
    assert '"$CLI" export-ai' in text
    assert '"$CLI" export-docs' in text
    assert '"$CLI" changed' in text
    assert "test -s full.txt" in text
    assert "test -s ai.txt" in text
    assert "test -s docs.txt" in text
    assert "test -s changed.txt" in text


def test_pipx_release_validation_script_checks_reinstall() -> None:
    text = Path("scripts/validate_pipx_release.sh").read_text(encoding="utf-8")

    assert "uninstall repodossier" in text
    assert "install \"$ROOT_DIR\"" in text
