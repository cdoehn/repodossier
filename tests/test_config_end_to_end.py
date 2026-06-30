import subprocess


def _run(repo, *args):
    return subprocess.run(
        list(args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_repocontext(repo, *args):
    return subprocess.run(
        ["repocontext", *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def _init_repo(path):
    _run(path, "git", "init")
    _run(path, "git", "config", "user.email", "repo@example.test")
    _run(path, "git", "config", "user.name", "Repo Tester")


def test_configuration_applies_across_all_export_modes(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()

    (tmp_path / "src" / "app.py").write_text(
        "def visible_config_marker():\n"
        "    return 'VISIBLE_CONFIG_MARKER'\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "hidden.py").write_text(
        "def hidden_config_marker():\n"
        "    return 'HIDDEN_CONFIG_MARKER'\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "guide.md").write_text(
        "# Visible Docs\n\nDOCS_VISIBLE_CONFIG_MARKER\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "hidden.md").write_text(
        "# Hidden Docs\n\nDOCS_HIDDEN_CONFIG_MARKER\n",
        encoding="utf-8",
    )

    (tmp_path / ".repocontext.yml").write_text(
        """
include:
  paths:
    - src
    - docs
exclude:
  paths:
    - src/hidden.py
    - docs/hidden.md
limits:
  max_total_files: 20
  max_file_bytes: 10000
  max_line_count: 50
  max_export_bytes: 50000
""",
        encoding="utf-8",
    )

    _run(
        tmp_path,
        "git",
        "add",
        "src/app.py",
        "src/hidden.py",
        "docs/guide.md",
        "docs/hidden.md",
    )
    _run(tmp_path, "git", "commit", "-m", "Add project files")

    (tmp_path / "src" / "app.py").write_text(
        "def visible_config_marker():\n"
        "    return 'VISIBLE_CONFIG_MARKER'\n\n"
        "CHANGED_VISIBLE_CONFIG_MARKER = 'yes'\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "hidden.py").write_text(
        "def hidden_config_marker():\n"
        "    return 'HIDDEN_CONFIG_MARKER'\n\n"
        "CHANGED_HIDDEN_CONFIG_MARKER = 'no'\n",
        encoding="utf-8",
    )

    full_result = _run_repocontext(tmp_path, "full")
    assert full_result.returncode == 0, full_result.stdout + full_result.stderr
    full = (tmp_path / "full.txt").read_text(encoding="utf-8")

    assert "## RepoContext Configuration" in full
    assert "- Config active: yes" in full
    assert "- Include paths: src, docs" in full
    assert "VISIBLE_CONFIG_MARKER" in full
    assert "HIDDEN_CONFIG_MARKER" not in full
    assert "DOCS_VISIBLE_CONFIG_MARKER" in full
    assert "DOCS_HIDDEN_CONFIG_MARKER" not in full

    ai_result = _run_repocontext(tmp_path, "export-ai")
    assert ai_result.returncode == 0, ai_result.stdout + ai_result.stderr
    ai = (tmp_path / "ai.txt").read_text(encoding="utf-8")

    assert ai.startswith("# AI CONTEXT\n")
    assert "## RepoContext Configuration" in ai
    assert "- Config active: yes" in ai
    assert "visible_config_marker" in ai
    assert "hidden_config_marker" not in ai

    docs_result = _run_repocontext(tmp_path, "export-docs")
    assert docs_result.returncode == 0, docs_result.stdout + docs_result.stderr
    docs = (tmp_path / "docs.txt").read_text(encoding="utf-8")

    assert docs.startswith("# Documentation Context")
    assert "## RepoContext Configuration" in docs
    assert "- Config active: yes" in docs
    assert "DOCS_VISIBLE_CONFIG_MARKER" in docs
    assert "DOCS_HIDDEN_CONFIG_MARKER" not in docs

    changed_result = _run_repocontext(tmp_path, "changed", "--no-diff")
    assert changed_result.returncode == 0, changed_result.stdout + changed_result.stderr
    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert changed.startswith("# Changed Export")
    assert "CHANGED_VISIBLE_CONFIG_MARKER" in changed
    assert "CHANGED_HIDDEN_CONFIG_MARKER" not in changed
