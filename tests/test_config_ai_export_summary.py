import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_ai_export_contains_inactive_configuration_summary_by_default(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "main.py").write_text("VALUE = True\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "main.py"],
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
    assert "- Config active: no" in ai
    assert "- Include paths: none" in ai
    assert "- Exclude paths: none" in ai
    assert "- Limit max_file_bytes: none" in ai


def test_ai_export_contains_active_configuration_summary(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("VALUE = True\n", encoding="utf-8")
    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
  globs:
    - "*.md"
exclude:
  paths:
    - build
  globs:
    - "*.log"
limits:
  max_file_bytes: 100
  max_total_files: 20
  max_export_bytes: 5000
  max_line_count: 30
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "src/main.py"],
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
    assert "- Config path:" in ai
    assert ".repocontext.yml" in ai
    assert "- Include paths: src" in ai
    assert "- Include globs: *.md" in ai
    assert "- Exclude paths: build" in ai
    assert "- Exclude globs: *.log" in ai
    assert "- Limit max_file_bytes: 100" in ai
    assert "- Limit max_total_files: 20" in ai
    assert "- Limit max_export_bytes: 5000" in ai
    assert "- Limit max_line_count: 30" in ai


def test_ai_export_config_summary_is_written_by_full_command_too(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "main.py").write_text("VALUE = True\n", encoding="utf-8")
    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - .
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "main.py"],
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
    assert "- Include paths: ." in ai
