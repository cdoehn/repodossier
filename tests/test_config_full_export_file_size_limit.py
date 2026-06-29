import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_full_export_skips_source_content_over_max_file_bytes(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "small.py").write_text("SMALL_VALUE = True\n", encoding="utf-8")
    (tmp_path / "large.py").write_text(
        "LARGE_VALUE_SHOULD_NOT_BE_EXPORTED = True\n" * 20,
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
limits:
  max_file_bytes: 30
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "small.py", "large.py"],
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

    assert "small.py" in full
    assert "SMALL_VALUE = True" in full

    assert "large.py" in full
    assert "LARGE_VALUE_SHOULD_NOT_BE_EXPORTED" not in full
    assert "limits.max_file_bytes=30" in full
    assert "content truncated because" in full


def test_full_export_no_config_ignores_max_file_bytes(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "large.py").write_text(
        "LARGE_VALUE_SHOULD_BE_EXPORTED = True\n" * 20,
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
limits:
  max_file_bytes: 30
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
        ["repocontext", "full", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    full = (tmp_path / "full.txt").read_text(encoding="utf-8")
    assert "large.py" in full
    assert "LARGE_VALUE_SHOULD_BE_EXPORTED = True" in full
    assert "limits.max_file_bytes=30" not in full
