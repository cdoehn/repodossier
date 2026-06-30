import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_ai_export_respects_max_total_files_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "aaa_first.py").write_text(
        "FIRST_AI_LIMIT_VALUE = True\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "zzz_second.py").write_text(
        "SECOND_AI_LIMIT_VALUE = True\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
limits:
  max_total_files: 1
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "src/aaa_first.py", "src/zzz_second.py"],
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

    # ai.txt is compact, so this checks the stable repository counters.
    assert "Tracked files: 2" in ai
    assert "Scanned files: 1" in ai


def test_ai_export_no_config_ignores_max_total_files_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "aaa_first.py").write_text(
        "FIRST_AI_LIMIT_VALUE = True\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "zzz_second.py").write_text(
        "SECOND_AI_LIMIT_VALUE = True\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
limits:
  max_total_files: 1
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "src/aaa_first.py", "src/zzz_second.py"],
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
