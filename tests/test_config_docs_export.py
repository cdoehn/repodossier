from pathlib import Path
import subprocess


def test_docs_export_includes_repodossier_configuration_documentation(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        """
# Demo Project

## Configuration with `.repodossier.yml`

RepoDossier can read an optional `.repodossier.yml` file from the repository root.

Supported sections:

- `include.paths`: repository-relative files or directories to include.
- `include.globs`: repository-relative glob patterns to include.
- `exclude.paths`: repository-relative files or directories to exclude.
- `exclude.globs`: repository-relative glob patterns to exclude.
- `limits.max_file_bytes`: skip full file content when a single file is larger than this many bytes.
- `limits.max_total_files`: limit the number of files considered for export after filtering.
- `limits.max_export_bytes`: limit the generated export size.
- `limits.max_line_count`: limit the number of exported lines per file.

Exclude rules always win over include rules.
""",
        encoding="utf-8",
    )

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True, text=True)

    result = subprocess.run(
        ["repodossier", "export-docs"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    docs_path = tmp_path / "docs.txt"
    assert docs_path.exists(), result.stdout + result.stderr

    docs = docs_path.read_text(encoding="utf-8")
    assert ".repodossier.yml" in docs
    assert "include.paths" in docs
    assert "include.globs" in docs
    assert "exclude.paths" in docs
    assert "exclude.globs" in docs
    assert "limits.max_file_bytes" in docs
    assert "limits.max_total_files" in docs
    assert "limits.max_export_bytes" in docs
    assert "limits.max_line_count" in docs
    assert "Exclude rules always win over include rules" in docs
