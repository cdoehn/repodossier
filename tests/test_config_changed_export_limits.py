import subprocess


def _run(repo, *args):
    return subprocess.run(
        args,
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(path):
    _run(path, "git", "init")
    _run(path, "git", "config", "user.email", "repo@example.test")
    _run(path, "git", "config", "user.name", "Repo Tester")


def _commit_file(repo, relative_path, content):
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _run(repo, "git", "add", relative_path)
    _run(repo, "git", "commit", "-m", f"Add {relative_path}")


def test_changed_export_respects_max_total_files_limit(tmp_path):
    _init_repo(tmp_path)

    _commit_file(tmp_path, "src/a.txt", "old a\n")
    _commit_file(tmp_path, "src/b.txt", "old b\n")

    (tmp_path / "src" / "a.txt").write_text(
        "FIRST_CHANGED_TOTAL_LIMIT_MARKER\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "b.txt").write_text(
        "SECOND_CHANGED_TOTAL_LIMIT_MARKER\n",
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

    result = subprocess.run(
        ["repocontext", "changed", "--no-diff"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert "FIRST_CHANGED_TOTAL_LIMIT_MARKER" in changed
    assert "SECOND_CHANGED_TOTAL_LIMIT_MARKER" not in changed


def test_changed_export_no_config_ignores_max_total_files_limit(tmp_path):
    _init_repo(tmp_path)

    _commit_file(tmp_path, "src/a.txt", "old a\n")
    _commit_file(tmp_path, "src/b.txt", "old b\n")

    (tmp_path / "src" / "a.txt").write_text(
        "FIRST_CHANGED_TOTAL_LIMIT_MARKER\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "b.txt").write_text(
        "SECOND_CHANGED_TOTAL_LIMIT_MARKER\n",
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

    result = subprocess.run(
        ["repocontext", "changed", "--no-diff", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert "FIRST_CHANGED_TOTAL_LIMIT_MARKER" in changed
    assert "SECOND_CHANGED_TOTAL_LIMIT_MARKER" in changed


def test_changed_export_respects_max_file_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    _commit_file(tmp_path, "src/large.txt", "old\n")

    (tmp_path / "src" / "large.txt").write_text(
        ("padding line to exceed the configured byte limit\n" * 8)
        + "CHANGED_FILE_BYTES_MARKER_SHOULD_NOT_APPEAR\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
limits:
  max_file_bytes: 40
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["repocontext", "changed", "--no-diff"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert "limits.max_file_bytes was reached" in changed
    assert "CHANGED_FILE_BYTES_MARKER_SHOULD_NOT_APPEAR" not in changed


def test_changed_export_respects_max_line_count_limit(tmp_path):
    _init_repo(tmp_path)

    _commit_file(tmp_path, "src/limited.txt", "old\n")

    (tmp_path / "src" / "limited.txt").write_text(
        "kept line\n"
        "second line\n"
        "CHANGED_LINE_COUNT_MARKER_SHOULD_NOT_APPEAR\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
limits:
  max_line_count: 1
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["repocontext", "changed", "--no-diff"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert "kept line" in changed
    assert "limits.max_line_count was reached" in changed
    assert "CHANGED_LINE_COUNT_MARKER_SHOULD_NOT_APPEAR" not in changed


def test_changed_export_respects_max_export_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    _commit_file(tmp_path, "src/large.txt", "old\n")

    (tmp_path / "src" / "large.txt").write_text(
        "very long changed line\n" * 160,
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
limits:
  max_export_bytes: 1000
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["repocontext", "changed", "--no-diff"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert changed.startswith("# Changed Export")
    assert len(changed.encode("utf-8")) <= 1000
    assert "limits.max_export_bytes was reached" in changed


def test_changed_export_no_config_ignores_max_export_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    _commit_file(tmp_path, "src/small.txt", "old\n")

    marker = "CHANGED_NO_CONFIG_MAX_EXPORT_BYTES_MARKER"
    (tmp_path / "src" / "small.txt").write_text(
        marker + "\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
limits:
  max_export_bytes: 80
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["repocontext", "changed", "--no-diff", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert "limits.max_export_bytes was reached" not in changed
    assert marker in changed
