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


def test_explicit_configuration_file_applies_to_all_export_modes(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()

    (tmp_path / "src" / "visible.py").write_text(
        "def visible_acceptance_marker():\n"
        "    return 'VISIBLE_ACCEPTANCE_CONTENT'\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "hidden.py").write_text(
        "def hidden_acceptance_marker():\n"
        "    return 'HIDDEN_ACCEPTANCE_CONTENT'\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "visible.md").write_text(
        "# Visible Docs\n\nDOCS_VISIBLE_ACCEPTANCE_MARKER\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "hidden.md").write_text(
        "# Hidden Docs\n\nDOCS_HIDDEN_ACCEPTANCE_MARKER\n",
        encoding="utf-8",
    )

    (tmp_path / "custom-repocontext.yml").write_text(
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
        "src/visible.py",
        "src/hidden.py",
        "docs/visible.md",
        "docs/hidden.md",
    )
    _run(tmp_path, "git", "commit", "-m", "Add acceptance files")

    (tmp_path / "src" / "visible.py").write_text(
        "def visible_acceptance_marker():\n"
        "    return 'VISIBLE_ACCEPTANCE_CONTENT'\n\n"
        "CHANGED_VISIBLE_ACCEPTANCE_MARKER = 'yes'\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "hidden.py").write_text(
        "def hidden_acceptance_marker():\n"
        "    return 'HIDDEN_ACCEPTANCE_CONTENT'\n\n"
        "CHANGED_HIDDEN_ACCEPTANCE_MARKER = 'no'\n",
        encoding="utf-8",
    )

    full_result = _run_repocontext(
        tmp_path,
        "full",
        "--config",
        "custom-repocontext.yml",
    )
    assert full_result.returncode == 0, full_result.stdout + full_result.stderr
    full = (tmp_path / "full.txt").read_text(encoding="utf-8")

    assert "## RepoContext Configuration" in full
    assert "- Config active: yes" in full
    assert "VISIBLE_ACCEPTANCE_CONTENT" in full
    assert "HIDDEN_ACCEPTANCE_CONTENT" not in full
    assert "DOCS_VISIBLE_ACCEPTANCE_MARKER" in full
    assert "DOCS_HIDDEN_ACCEPTANCE_MARKER" not in full

    ai_result = _run_repocontext(
        tmp_path,
        "export-ai",
        "--config",
        "custom-repocontext.yml",
    )
    assert ai_result.returncode == 0, ai_result.stdout + ai_result.stderr
    ai = (tmp_path / "ai.txt").read_text(encoding="utf-8")

    assert ai.startswith("# AI CONTEXT\n")
    assert "## RepoContext Configuration" in ai
    assert "- Config active: yes" in ai
    assert "visible_acceptance_marker" in ai
    assert "hidden_acceptance_marker" not in ai

    docs_result = _run_repocontext(
        tmp_path,
        "export-docs",
        "--config",
        "custom-repocontext.yml",
    )
    assert docs_result.returncode == 0, docs_result.stdout + docs_result.stderr
    docs = (tmp_path / "docs.txt").read_text(encoding="utf-8")

    assert docs.startswith("# Documentation Context")
    assert "## RepoContext Configuration" in docs
    assert "- Config active: yes" in docs
    assert "DOCS_VISIBLE_ACCEPTANCE_MARKER" in docs
    assert "DOCS_HIDDEN_ACCEPTANCE_MARKER" not in docs

    changed_result = _run_repocontext(
        tmp_path,
        "changed",
        "--no-diff",
        "--config",
        "custom-repocontext.yml",
    )
    assert changed_result.returncode == 0, changed_result.stdout + changed_result.stderr
    changed = (tmp_path / "changed.txt").read_text(encoding="utf-8")

    assert changed.startswith("# Changed Export")
    assert "CHANGED_VISIBLE_ACCEPTANCE_MARKER" in changed
    assert "CHANGED_HIDDEN_ACCEPTANCE_MARKER" not in changed
