from pathlib import Path


def test_readme_documents_repodossier_yml():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert ".repodossier.yml" in readme
    assert "include.paths" in readme
    assert "include.globs" in readme
    assert "exclude.paths" in readme
    assert "exclude.globs" in readme
    assert "limits.max_file_bytes" in readme
    assert "limits.max_total_files" in readme
    assert "limits.max_export_bytes" in readme
    assert "limits.max_line_count" in readme


def test_readme_documents_exclude_wins_over_include():
    readme = Path("README.md").read_text(encoding="utf-8").lower()

    assert "exclude rules always win over include rules" in readme


def test_example_repodossier_config_exists_and_documents_supported_keys():
    example = Path(".repodossier.example.yml")

    assert example.exists()

    text = example.read_text(encoding="utf-8")
    assert "include:" in text
    assert "paths:" in text
    assert "globs:" in text
    assert "exclude:" in text
    assert "limits:" in text
    assert "max_file_bytes:" in text
    assert "max_total_files:" in text
    assert "max_export_bytes:" in text
    assert "max_line_count:" in text
