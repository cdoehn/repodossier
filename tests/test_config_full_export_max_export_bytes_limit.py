import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_full_export_respects_max_export_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "large.py").write_text(
        "VALUE_000 = True\n"
        + "\n".join(f"VALUE_{index:03d}_SHOULD_BE_TRUNCATED = True" for index in range(1, 200))
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
limits:
  max_export_bytes: 900
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
    assert len(full.encode("utf-8")) <= 900
    assert "limits.max_export_bytes was reached" in full
    assert "VALUE_199_SHOULD_BE_TRUNCATED" not in full


def test_full_export_no_config_ignores_max_export_bytes_limit(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "large.py").write_text(
        "VALUE_000 = True\n"
        + "\n".join(f"VALUE_{index:03d}_SHOULD_BE_EXPORTED = True" for index in range(1, 60))
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
limits:
  max_export_bytes: 900
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
    assert "VALUE_059_SHOULD_BE_EXPORTED = True" in full
    assert "limits.max_export_bytes was reached" not in full
