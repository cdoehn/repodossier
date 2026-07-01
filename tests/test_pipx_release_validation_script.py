from pathlib import Path


def _script_text() -> str:
    return Path("scripts/validate_pipx_release.sh").read_text(encoding="utf-8")


def _legacy_command() -> str:
    return "repo" + "context"


def test_pipx_release_validation_script_exists_and_is_executable() -> None:
    script = Path("scripts/validate_pipx_release.sh")

    assert script.exists()
    assert script.stat().st_mode & 0o111


def test_pipx_release_validation_script_uses_isolated_pipx_home() -> None:
    text = _script_text()

    assert "PIPX_HOME" in text
    assert "PIPX_BIN_DIR" in text
    assert "mktemp -d" in text
    assert 'export PATH="$PIPX_BIN_DIR:$PATH"' in text


def test_pipx_release_validation_script_installs_local_checkout_with_python_module_pipx() -> None:
    text = _script_text()

    assert '"$PYTHON_BIN" -m pipx install "$REPO_ROOT"' in text
    assert "pipx install -e" not in text
    assert "python3 -m pipx install -e" not in text


def test_pipx_release_validation_script_checks_both_cli_names() -> None:
    text = _script_text()
    legacy_command = _legacy_command()

    assert "repodossier --help" in text
    assert "repodossier --version" in text
    assert f"{legacy_command} --help" in text
    assert f"{legacy_command} --version" in text


def test_pipx_release_validation_script_covers_release_exports() -> None:
    text = _script_text()

    assert "repodossier full" in text
    assert "repodossier export-ai" in text
    assert "repodossier export-docs" in text
    assert "repodossier changed" in text
    assert "test -s full.txt" in text
    assert "test -s ai.txt" in text
    assert "test -s docs.txt" in text
    assert "test -s changed.txt" in text


def test_pipx_release_validation_script_uses_sample_git_repository() -> None:
    text = _script_text()

    assert "git init" in text
    assert "sample_repo" in text
    assert "git commit -m" in text


def test_pipx_release_validation_script_checks_legacy_alias_export() -> None:
    text = _script_text()
    legacy_command = _legacy_command()

    assert f"{legacy_command} export-ai" in text
