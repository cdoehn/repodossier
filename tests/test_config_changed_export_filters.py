import subprocess


def _run(command, cwd):
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(path):
    _run(["git", "init"], cwd=path)
    _run(["git", "config", "user.email", "test@example.com"], cwd=path)
    _run(["git", "config", "user.name", "Test User"], cwd=path)


def _commit_baseline(path):
    _run(["git", "add", "."], cwd=path)
    _run(["git", "commit", "-m", "baseline"], cwd=path)


def test_changed_command_respects_include_and_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "private").mkdir()

    (tmp_path / "src" / "public.py").write_text(
        "VALUE = 'before public'\n",
        encoding="utf-8",
    )
    (tmp_path / "private" / "secret.py").write_text(
        "VALUE = 'before private'\n",
        encoding="utf-8",
    )
    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
    - private
exclude:
  paths:
    - private
""",
        encoding="utf-8",
    )

    _commit_baseline(tmp_path)

    (tmp_path / "src" / "public.py").write_text(
        "PUBLIC_CHANGED_EXPORT_VALUE = True\n",
        encoding="utf-8",
    )
    (tmp_path / "private" / "secret.py").write_text(
        "PRIVATE_CHANGED_EXPORT_VALUE_SHOULD_NOT_APPEAR = True\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["repocontext", "changed"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert "PUBLIC_CHANGED_EXPORT_VALUE" in changed
    assert "PRIVATE_CHANGED_EXPORT_VALUE_SHOULD_NOT_APPEAR" not in changed


def test_changed_command_no_config_ignores_include_and_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "private").mkdir()

    (tmp_path / "src" / "public.py").write_text(
        "VALUE = 'before public'\n",
        encoding="utf-8",
    )
    (tmp_path / "private" / "secret.py").write_text(
        "VALUE = 'before private'\n",
        encoding="utf-8",
    )
    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
exclude:
  paths:
    - private
""",
        encoding="utf-8",
    )

    _commit_baseline(tmp_path)

    (tmp_path / "src" / "public.py").write_text(
        "PUBLIC_CHANGED_EXPORT_VALUE = True\n",
        encoding="utf-8",
    )
    (tmp_path / "private" / "secret.py").write_text(
        "PRIVATE_CHANGED_EXPORT_VALUE_SHOULD_APPEAR_WITH_NO_CONFIG = True\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["repocontext", "changed", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert "PUBLIC_CHANGED_EXPORT_VALUE" in changed
    assert "PRIVATE_CHANGED_EXPORT_VALUE_SHOULD_APPEAR_WITH_NO_CONFIG" in changed
