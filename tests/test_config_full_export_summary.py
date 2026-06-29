import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_full_export_contains_inactive_configuration_summary_by_default(tmp_path):
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
        ["repocontext", "full"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    full = (tmp_path / "full.txt").read_text(encoding="utf-8")

    assert "## RepoContext Configuration" in full
    assert "- Config active: no" in full
    assert "- Include paths: none" in full
    assert "- Exclude paths: none" in full
    assert "- Limit max_file_bytes: none" in full


def test_full_export_contains_active_configuration_summary(tmp_path):
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
        ["repocontext", "full"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    full = (tmp_path / "full.txt").read_text(encoding="utf-8")

    assert "## RepoContext Configuration" in full
    assert "- Config active: yes" in full
    assert "- Config path:" in full
    assert ".repocontext.yml" in full
    assert "- Include paths: src" in full
    assert "- Include globs: *.md" in full
    assert "- Exclude paths: build" in full
    assert "- Exclude globs: *.log" in full
    assert "- Limit max_file_bytes: 100" in full
    assert "- Limit max_total_files: 20" in full
    assert "- Limit max_export_bytes: 5000" in full
    assert "- Limit max_line_count: 30" in full


def test_full_export_summary_is_preserved_with_max_export_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "large.py").write_text(
        "\\n".join(f"VALUE_{index:03d} = True" for index in range(150)) + "\\n",
        encoding="utf-8",
    )
    (tmp_path / ".repocontext.yml").write_text(
        """
limits:
  max_export_bytes: 1200
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "large.py"],
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

    full = (tmp_path / "full.txt").read_text(encoding="utf-8")

    assert len(full.encode("utf-8")) <= 1200
    assert "## RepoContext Configuration" in full
    assert "- Config active: yes" in full
    assert "- Limit max_export_bytes: 1200" in full
    assert "limits.max_export_bytes was reached" in full
