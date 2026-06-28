from __future__ import annotations

from pathlib import Path

from repocontext.exporters.full import create_full_export_context, render_full_export
from repocontext.git import RepositoryInfo, TrackedFile
from repocontext.models import FileInfo


def make_repository_info(tmp_path: Path) -> RepositoryInfo:
    return RepositoryInfo(
        name="example",
        root_path=tmp_path,
        is_current_directory_root=True,
        branch="main",
        commit_hash="a" * 40,
        short_commit_hash="aaaaaaa",
        remote_url=None,
        is_dirty=False,
        tracked_files=[
            TrackedFile(path=Path("pyproject.toml")),
        ],
        commit_metadata=None,
    )


def test_full_export_contains_real_dependency_section_before_source_dump(
    tmp_path: Path,
) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_content = """
[project]
dependencies = ["click>=8"]

[project.optional-dependencies]
dev = ["pytest>=7.4"]
""".strip()
    pyproject_path.write_text(pyproject_content, encoding="utf-8")

    context = create_full_export_context(
        make_repository_info(tmp_path),
        [
            FileInfo(
                relative_path=Path("pyproject.toml"),
                absolute_path=pyproject_path,
                is_text=True,
                is_binary=False,
                language="toml",
                line_count=5,
                estimated_tokens=20,
                content=pyproject_content,
            )
        ],
    )

    rendered = render_full_export(context)

    assert rendered.index("# Dependencies") < rendered.index("# Complete Source Export")
    assert "Runtime dependencies: 1" in rendered
    assert "Optional dependencies: 1" in rendered
    assert "- pyproject.toml" in rendered
    assert "- click>=8 (pyproject.toml, project.dependencies)" in rendered
    assert "- dev: pytest>=7.4 (pyproject.toml, project.optional-dependencies.dev)" in rendered
