import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_full_export_truncates_source_content_by_max_line_count(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "limited.py").write_text(
        "LINE_1 = True\n"
        "LINE_2 = True\n"
        "LINE_3_SHOULD_NOT_BE_EXPORTED = True\n"
        "LINE_4_SHOULD_NOT_BE_EXPORTED = True\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
limits:
  max_line_count: 2
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "limited.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repodossier", "full"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    full = (tmp_path / "full.txt").read_text(encoding="utf-8")

    assert "limited.py" in full
    assert "LINE_1 = True" in full
    assert "LINE_2 = True" in full
    assert "LINE_3_SHOULD_NOT_BE_EXPORTED" not in full
    assert "LINE_4_SHOULD_NOT_BE_EXPORTED" not in full
    assert "limits.max_line_count was reached" in full
    assert "Omitted: 2" in full


def test_full_export_no_config_ignores_max_line_count(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "limited.py").write_text(
        "LINE_1 = True\n"
        "LINE_2 = True\n"
        "LINE_3_SHOULD_BE_EXPORTED = True\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
limits:
  max_line_count: 2
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "limited.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["repodossier", "full", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    full = (tmp_path / "full.txt").read_text(encoding="utf-8")

    assert "limited.py" in full
    assert "LINE_1 = True" in full
    assert "LINE_2 = True" in full
    assert "LINE_3_SHOULD_BE_EXPORTED = True" in full
    assert "limits.max_line_count was reached" not in full
