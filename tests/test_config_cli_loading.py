import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    (path / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True)


def test_full_command_rejects_missing_explicit_config_file(tmp_path):
    _init_repo(tmp_path)

    result = subprocess.run(
        ["repocontext", "full", "--config", "missing.yml"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Configuration error" in output
    assert "Configuration file not found" in output


def test_full_command_rejects_config_and_no_config_together(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".repocontext.yml").write_text("", encoding="utf-8")

    result = subprocess.run(
        ["repocontext", "full", "--config", ".repocontext.yml", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Configuration error" in output
    assert "--config and --no-config cannot be used together" in output


def test_full_command_no_config_ignores_invalid_repocontext_yml(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".repocontext.yml").write_text("include: [unterminated", encoding="utf-8")

    result = subprocess.run(
        ["repocontext", "full", "--no-config"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "full.txt").exists()


def test_full_command_accepts_valid_explicit_config_file(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "custom.yml").write_text(
        """
include:
  paths:
    - .
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["repocontext", "full", "--config", "custom.yml"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "full.txt").exists()
