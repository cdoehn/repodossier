import subprocess


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_docs_export_respects_include_and_exclude_filters(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "private").mkdir()

    (tmp_path / "docs" / "public.md").write_text(
        "# Public docs\n\nPUBLIC_DOCS_EXPORT_VALUE\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "private" / "secret.md").write_text(
        "# Secret docs\n\nPRIVATE_DOCS_EXPORT_VALUE_SHOULD_NOT_APPEAR\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
exclude:
  paths:
    - docs/private
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/public.md", "docs/private/secret.md"],
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

    assert "PUBLIC_DOCS_EXPORT_VALUE" in docs
    assert "PRIVATE_DOCS_EXPORT_VALUE_SHOULD_NOT_APPEAR" not in docs


def test_docs_export_no_config_ignores_include_and_exclude_filters_inside_docs_tree(tmp_path):
    _init_repo(tmp_path)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "private").mkdir()

    (tmp_path / "docs" / "public.md").write_text(
        "# Public docs\n\nPUBLIC_DOCS_EXPORT_VALUE\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "private" / "secret.md").write_text(
        "# Secret docs\n\nPRIVATE_DOCS_EXPORT_VALUE_SHOULD_APPEAR_WITH_NO_CONFIG\n",
        encoding="utf-8",
    )

    (tmp_path / ".repodossier.yml").write_text(
        """
include:
  paths:
    - docs
exclude:
  paths:
    - docs/private
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "docs/public.md", "docs/private/secret.md"],
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

    assert "PUBLIC_DOCS_EXPORT_VALUE" in docs
    assert "PRIVATE_DOCS_EXPORT_VALUE_SHOULD_APPEAR_WITH_NO_CONFIG" in docs
