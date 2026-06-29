import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_full_export_respects_max_total_files_limit_deterministically(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "a_keep.py").write_text("A_KEEP = True\n", encoding="utf-8")
    (tmp_path / "b_keep.py").write_text("B_KEEP = True\n", encoding="utf-8")
    (tmp_path / "c_drop.py").write_text("C_DROP = True\n", encoding="utf-8")

    (tmp_path / ".repocontext.yml").write_text(
        """
limits:
  max_total_files: 2
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "a_keep.py", "b_keep.py", "c_drop.py"],
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

    assert "a_keep.py" in full
    assert "A_KEEP = True" in full
    assert "b_keep.py" in full
    assert "B_KEEP = True" in full
    assert "c_drop.py" not in full
    assert "C_DROP = True" not in full


def test_full_export_no_config_ignores_max_total_files_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "a_keep.py").write_text("A_KEEP = True\n", encoding="utf-8")
    (tmp_path / "b_keep.py").write_text("B_KEEP = True\n", encoding="utf-8")
    (tmp_path / "c_drop.py").write_text("C_DROP = True\n", encoding="utf-8")

    (tmp_path / ".repocontext.yml").write_text(
        """
limits:
  max_total_files: 2
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "a_keep.py", "b_keep.py", "c_drop.py"],
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

    assert "a_keep.py" in full
    assert "A_KEEP = True" in full
    assert "b_keep.py" in full
    assert "B_KEEP = True" in full
    assert "c_drop.py" in full
    assert "C_DROP = True" in full
