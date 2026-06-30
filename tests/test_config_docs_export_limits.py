import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_docs_export_respects_max_total_files_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        "# A\n\nFIRST_DOCS_TOTAL_LIMIT_MARKER\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "b.md").write_text(
        "# B\n\nSECOND_DOCS_TOTAL_LIMIT_MARKER\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
limits:
  max_total_files: 1
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/a.md", "docs/b.md"],
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

    assert "FIRST_DOCS_TOTAL_LIMIT_MARKER" in docs
    assert "SECOND_DOCS_TOTAL_LIMIT_MARKER" not in docs


def test_docs_export_no_config_ignores_max_total_files_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        "# A\n\nFIRST_DOCS_TOTAL_LIMIT_MARKER\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "b.md").write_text(
        "# B\n\nSECOND_DOCS_TOTAL_LIMIT_MARKER\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
limits:
  max_total_files: 1
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/a.md", "docs/b.md"],
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

    assert "FIRST_DOCS_TOTAL_LIMIT_MARKER" in docs
    assert "SECOND_DOCS_TOTAL_LIMIT_MARKER" in docs


def test_docs_export_respects_max_file_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "large.md").write_text(
        "# Large\n"
        + ("padding line to exceed the configured byte limit\n" * 8)
        + "DOCS_FILE_BYTES_MARKER_SHOULD_NOT_APPEAR\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
limits:
  max_file_bytes: 40
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/large.md"],
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

    assert "limits.max_file_bytes was reached" in docs
    assert "DOCS_FILE_BYTES_MARKER_SHOULD_NOT_APPEAR" not in docs


def test_docs_export_respects_max_line_count_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "limited.md").write_text(
        "# Kept heading\n"
        "second line\n"
        "DOCS_LINE_COUNT_MARKER_SHOULD_NOT_APPEAR\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
limits:
  max_line_count: 1
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/limited.md"],
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

    assert "# Kept heading" in docs
    assert "limits.max_line_count was reached" in docs
    assert "DOCS_LINE_COUNT_MARKER_SHOULD_NOT_APPEAR" not in docs


def test_docs_export_respects_max_export_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "large.md").write_text(
        "# Large\n\n"
        + ("very long documentation line\n" * 120),
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
limits:
  max_export_bytes: 1000
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/large.md"],
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

    assert docs.startswith("# Documentation Context")
    assert len(docs.encode("utf-8")) <= 1000
    assert "limits.max_export_bytes was reached" in docs


def test_docs_export_no_config_ignores_max_export_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    marker = "DOCS_NO_CONFIG_MAX_EXPORT_BYTES_MARKER"
    (tmp_path / "docs" / "small.md").write_text(
        f"# {marker}\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
limits:
  max_export_bytes: 80
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/small.md"],
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

    assert "limits.max_export_bytes was reached" not in docs
    assert marker in docs
