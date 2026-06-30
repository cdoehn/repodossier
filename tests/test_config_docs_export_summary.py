import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_docs_export_contains_inactive_configuration_summary_by_default(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "README.md").write_text(
        "# Project\n\nDocumentation body.\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "README.md"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repodossier", "export-docs"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    docs = (tmp_path / "docs.txt").read_text(encoding="utf-8")

    assert docs.startswith("# Documentation Context\n")
    assert "## RepoDossier Configuration" in docs
    assert "- Config active: no" in docs
    assert "- Include paths: none" in docs
    assert "- Limit max_total_files: none" in docs


def test_docs_export_contains_active_configuration_summary(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text(
        "# Docs\n\nVisible documentation.\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
exclude:
  globs:
    - "*.tmp"
limits:
  max_total_files: 10
  max_line_count: 20
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/README.md"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repodossier", "export-docs"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    docs = (tmp_path / "docs.txt").read_text(encoding="utf-8")

    assert docs.startswith("# Documentation Context\n")
    assert "## RepoDossier Configuration" in docs
    assert "- Config active: yes" in docs
    assert "- Include paths: docs" in docs
    assert "- Exclude globs: *.tmp" in docs
    assert "- Limit max_total_files: 10" in docs
    assert "- Limit max_line_count: 20" in docs
    assert "# Docs" in docs


def test_docs_export_no_config_reports_inactive_configuration_summary(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text(
        "# Docs\n\nVisible documentation.\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - not-used
limits:
  max_total_files: 1
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/README.md"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repodossier", "export-docs", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    docs = (tmp_path / "docs.txt").read_text(encoding="utf-8")

    assert "## RepoDossier Configuration" in docs
    assert "- Config active: no" in docs
    assert "- Include paths: none" in docs
    assert "# Docs" in docs
