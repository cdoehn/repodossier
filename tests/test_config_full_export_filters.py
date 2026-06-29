import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_full_export_applies_include_and_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    src_dir = tmp_path / "src"
    private_dir = tmp_path / "private"
    src_dir.mkdir()
    private_dir.mkdir()

    (tmp_path / "README.md").write_text("# Demo\nREADME_SHOULD_BE_FILTERED\n", encoding="utf-8")
    (src_dir / "keep.py").write_text("KEEP_ME = True\n", encoding="utf-8")
    (private_dir / "secret.py").write_text("SECRET_PRIVATE = True\n", encoding="utf-8")

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
        ["git", "add", "README.md", "src/keep.py", "private/secret.py"],
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
    assert "src/keep.py" in full
    assert "KEEP_ME = True" in full
    assert "private/secret.py" not in full
    assert "SECRET_PRIVATE" not in full
    assert "README_SHOULD_BE_FILTERED" not in full


def test_full_export_no_config_ignores_include_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    src_dir = tmp_path / "src"
    private_dir = tmp_path / "private"
    src_dir.mkdir()
    private_dir.mkdir()

    (src_dir / "keep.py").write_text("KEEP_ME = True\n", encoding="utf-8")
    (private_dir / "secret.py").write_text("SECRET_PRIVATE = True\n", encoding="utf-8")

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
        ["git", "add", "src/keep.py", "private/secret.py"],
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
    assert "src/keep.py" in full
    assert "KEEP_ME = True" in full
    assert "private/secret.py" in full
    assert "SECRET_PRIVATE = True" in full
