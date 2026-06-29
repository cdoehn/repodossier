import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_ai_export_respects_include_and_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "private").mkdir()
    (tmp_path / "logs").mkdir()

    (tmp_path / "src" / "public.py").write_text(
        "PUBLIC_AI_EXPORT_VALUE = True\n",
        encoding="utf-8",
    )
    (tmp_path / "private" / "secret.py").write_text(
        "PRIVATE_AI_EXPORT_VALUE_SHOULD_NOT_APPEAR = True\n",
        encoding="utf-8",
    )
    (tmp_path / "logs" / "debug.log").write_text(
        "LOG_AI_EXPORT_VALUE_SHOULD_NOT_APPEAR\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
    - private
    - logs
exclude:
  paths:
    - private
  globs:
    - "*.log"
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "src/public.py", "private/secret.py", "logs/debug.log"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repocontext", "export-ai"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    ai = (tmp_path / "ai.txt").read_text(encoding="utf-8")

    assert "## RepoContext Configuration" in ai
    assert "- Config active: yes" in ai

    # ai.txt is a compact AI context, not a complete source dump.
    # The stable contract is that the repository counters use the filtered context.
    assert "Tracked files: 3" in ai
    assert "Scanned files: 1" in ai

    assert "PRIVATE_AI_EXPORT_VALUE_SHOULD_NOT_APPEAR" not in ai
    assert "LOG_AI_EXPORT_VALUE_SHOULD_NOT_APPEAR" not in ai


def test_ai_export_no_config_ignores_include_and_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "private").mkdir()

    (tmp_path / "src" / "public.py").write_text(
        "PUBLIC_AI_EXPORT_VALUE = True\n",
        encoding="utf-8",
    )
    (tmp_path / "private" / "secret.py").write_text(
        "PRIVATE_AI_EXPORT_VALUE_SHOULD_APPEAR_WITH_NO_CONFIG = True\n",
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

    subprocess.run(
        ["git", "add", "src/public.py", "private/secret.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repocontext", "export-ai", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    ai = (tmp_path / "ai.txt").read_text(encoding="utf-8")

    assert "- Config active: no" in ai
    assert "Tracked files: 2" in ai
    assert "Scanned files: 2" in ai


def test_full_command_ai_export_respects_include_and_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "private").mkdir()

    (tmp_path / "src" / "public.py").write_text(
        "PUBLIC_FULL_AI_EXPORT_VALUE = True\n",
        encoding="utf-8",
    )
    (tmp_path / "private" / "secret.py").write_text(
        "PRIVATE_FULL_AI_EXPORT_VALUE_SHOULD_NOT_APPEAR = True\n",
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

    subprocess.run(
        ["git", "add", "src/public.py", "private/secret.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repocontext", "full"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    ai = (tmp_path / "ai.txt").read_text(encoding="utf-8")

    assert "## RepoContext Configuration" in ai
    assert "- Config active: yes" in ai
    assert "Tracked files: 2" in ai
    assert "Scanned files: 1" in ai
    assert "PRIVATE_FULL_AI_EXPORT_VALUE_SHOULD_NOT_APPEAR" not in ai
