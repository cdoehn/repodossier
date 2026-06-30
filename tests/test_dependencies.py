from __future__ import annotations

import pytest

from repodossier.dependencies import (
    Dependency,
    DependencyReport,
    analyze_dependencies,
    normalize_dependency_name,
)


def test_normalize_dependency_name_canonicalizes_case_and_separators() -> None:
    assert normalize_dependency_name("Google_Auth") == "google-auth"
    assert normalize_dependency_name("my.package") == "my-package"
    assert normalize_dependency_name("My__Package") == "my-package"


def test_normalize_dependency_name_ignores_extras() -> None:
    assert normalize_dependency_name("requests[security]") == "requests"


def test_dependency_fills_normalized_name_and_raw_value() -> None:
    dependency = Dependency(
        name="Click",
        version_constraint=">=8",
        dependency_type="runtime",
        source_file="pyproject.toml",
        source_section="project.dependencies",
    )

    assert dependency.name == "Click"
    assert dependency.normalized_name == "click"
    assert dependency.raw_value == "Click"
    assert dependency.dependency_type == "runtime"


def test_dependency_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        Dependency(name="   ")


def test_dependency_rejects_unknown_dependency_type_value() -> None:
    with pytest.raises(ValueError, match="Unsupported dependency type"):
        Dependency(name="click", dependency_type="production")


def test_dependency_report_sorts_dependencies_deterministically() -> None:
    report = DependencyReport(
        dependencies=(
            Dependency(
                name="ruff",
                dependency_type="development",
                source_file="requirements-dev.txt",
                raw_value="ruff",
            ),
            Dependency(
                name="requests",
                dependency_type="runtime",
                source_file="requirements.txt",
                raw_value="requests>=2.31",
            ),
            Dependency(
                name="click",
                dependency_type="runtime",
                source_file="pyproject.toml",
                raw_value="click>=8",
            ),
            Dependency(
                name="mkdocs",
                dependency_type="optional",
                source_file="pyproject.toml",
                raw_value="mkdocs",
            ),
        ),
        dependency_files=("requirements.txt", "pyproject.toml", "requirements.txt"),
    )

    assert [dependency.normalized_name for dependency in report.dependencies] == [
        "click",
        "requests",
        "ruff",
        "mkdocs",
    ]
    assert report.dependency_files == ("pyproject.toml", "requirements.txt")


def test_dependency_report_filters_and_counts_by_type() -> None:
    report = DependencyReport(
        dependencies=(
            Dependency(name="pytest", dependency_type="development"),
            Dependency(name="click", dependency_type="runtime"),
            Dependency(name="mkdocs", dependency_type="optional"),
            Dependency(name="unknown-package", dependency_type="unknown"),
        )
    )

    assert [dependency.name for dependency in report.dependencies_by_type("runtime")] == [
        "click"
    ]
    assert report.counts_by_type() == {
        "runtime": 1,
        "development": 1,
        "optional": 1,
        "unknown": 1,
    }


def test_dependency_report_rejects_invalid_filter_type() -> None:
    report = DependencyReport()

    with pytest.raises(ValueError, match="Unsupported dependency type"):
        report.dependencies_by_type("prod")


def test_analyze_dependencies_reads_pep621_runtime_dependencies(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = [
  "click>=8",
  "requests>=2.31",
]
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    runtime_dependencies = report.dependencies_by_type("runtime")
    assert [dependency.normalized_name for dependency in runtime_dependencies] == [
        "click",
        "requests",
    ]
    assert [dependency.version_constraint for dependency in runtime_dependencies] == [
        ">=8",
        ">=2.31",
    ]
    assert {dependency.source_section for dependency in runtime_dependencies} == {
        "project.dependencies"
    }
    assert report.dependency_files == ("pyproject.toml",)


def test_analyze_dependencies_reads_pep621_optional_dependencies(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project.optional-dependencies]
dev = ["pytest>=8"]
docs = ["mkdocs"]
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    optional_dependencies = report.dependencies_by_type("optional")
    assert [
        (dependency.normalized_name, dependency.group, dependency.source_section)
        for dependency in optional_dependencies
    ] == [
        ("mkdocs", "docs", "project.optional-dependencies.docs"),
        ("pytest", "dev", "project.optional-dependencies.dev"),
    ]


def test_analyze_dependencies_reads_poetry_dependencies(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.poetry.dependencies]
python = "^3.12"
click = "^8.1"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    assert [
        (dependency.normalized_name, dependency.version_constraint)
        for dependency in report.dependencies_by_type("runtime")
    ] == [("click", "^8.1")]
    assert [
        (dependency.normalized_name, dependency.version_constraint)
        for dependency in report.dependencies_by_type("development")
    ] == [("pytest", "^8.0")]
    assert "python" not in {
        dependency.normalized_name
        for dependency in report.dependencies
    }


def test_analyze_dependencies_reads_legacy_poetry_dev_dependencies(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.poetry.dev-dependencies]
pytest = "^8.0"
ruff = "^0.6"
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    assert [
        dependency.normalized_name
        for dependency in report.dependencies_by_type("development")
    ] == ["pytest", "ruff"]


def test_analyze_dependencies_classifies_poetry_groups(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.poetry.group.docs.dependencies]
mkdocs = "^1.6"

[tool.poetry.group.lint.dependencies]
ruff = "^0.6"

[tool.poetry.group.extra.dependencies]
rich = "^13"
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    assert [
        (dependency.normalized_name, dependency.group)
        for dependency in report.dependencies_by_type("development")
    ] == [
        ("mkdocs", "docs"),
        ("ruff", "lint"),
    ]
    assert [
        (dependency.normalized_name, dependency.group)
        for dependency in report.dependencies_by_type("optional")
    ] == [("rich", "extra")]


def test_analyze_dependencies_handles_invalid_pyproject_toml(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project
dependencies = ["click"]
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    assert report.dependencies == ()
    assert report.dependency_files == ("pyproject.toml",)
    assert report.warnings
    assert "invalid pyproject.toml" in report.warnings[0]


def test_analyze_dependencies_returns_empty_report_without_dependency_files(
    tmp_path,
) -> None:
    report = analyze_dependencies(tmp_path, files=[])

    assert isinstance(report, DependencyReport)
    assert report.is_empty()
    assert report.counts_by_type() == {
        "runtime": 0,
        "development": 0,
        "optional": 0,
        "unknown": 0,
    }



def test_analyze_dependencies_reads_simple_requirements_txt(tmp_path) -> None:
    (tmp_path / "requirements.txt").write_text(
        """
requests>=2.31
click==8.1.7
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    runtime_dependencies = report.dependencies_by_type("runtime")
    assert [
        (dependency.normalized_name, dependency.version_constraint, dependency.source_file)
        for dependency in runtime_dependencies
    ] == [
        ("click", "==8.1.7", "requirements.txt"),
        ("requests", ">=2.31", "requirements.txt"),
    ]
    assert report.dependency_files == ("requirements.txt",)


def test_analyze_dependencies_reads_requirements_dev_txt_as_development(
    tmp_path,
) -> None:
    (tmp_path / "requirements-dev.txt").write_text(
        """
pytest>=8
ruff
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    development_dependencies = report.dependencies_by_type("development")
    assert [
        (dependency.normalized_name, dependency.version_constraint, dependency.source_file)
        for dependency in development_dependencies
    ] == [
        ("pytest", ">=8", "requirements-dev.txt"),
        ("ruff", "", "requirements-dev.txt"),
    ]


def test_analyze_dependencies_ignores_requirements_comments_and_blank_lines(
    tmp_path,
) -> None:
    (tmp_path / "requirements.txt").write_text(
        """
# comment
requests>=2

click # inline comment
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    assert [
        dependency.normalized_name
        for dependency in report.dependencies_by_type("runtime")
    ] == [
        "click",
        "requests",
    ]


def test_analyze_dependencies_tracks_unsupported_requirements_lines(tmp_path) -> None:
    (tmp_path / "requirements.txt").write_text(
        """
-r base.txt
--index-url https://example.com/simple
-e .
git+https://example.com/example.git
""".strip(),
        encoding="utf-8",
    )

    report = analyze_dependencies(tmp_path)

    assert report.dependencies == ()
    assert len(report.unsupported_lines) == 4
    assert any("-r base.txt" in line for line in report.unsupported_lines)
    assert any("--index-url" in line for line in report.unsupported_lines)
    assert report.warnings


def test_analyze_dependencies_discovers_requirements_subdirectory_files(
    tmp_path,
) -> None:
    requirements_dir = tmp_path / "requirements"
    requirements_dir.mkdir()
    (requirements_dir / "base.txt").write_text("basepkg>=1\n", encoding="utf-8")
    (requirements_dir / "dev.txt").write_text("pytest>=8\n", encoding="utf-8")
    (requirements_dir / "docs.txt").write_text("mkdocs\n", encoding="utf-8")

    report = analyze_dependencies(tmp_path)

    assert report.dependency_files == (
        "requirements/base.txt",
        "requirements/dev.txt",
        "requirements/docs.txt",
    )
    assert [
        dependency.normalized_name
        for dependency in report.dependencies_by_type("development")
    ] == [
        "mkdocs",
        "pytest",
    ]
    assert [
        dependency.normalized_name
        for dependency in report.dependencies_by_type("unknown")
    ] == [
        "basepkg",
    ]


def test_analyze_dependencies_uses_passed_file_list_for_requirements_discovery(
    tmp_path,
) -> None:
    (tmp_path / "requirements.txt").write_text("requests>=2\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("pytest>=8\n", encoding="utf-8")

    report = analyze_dependencies(tmp_path, files=["requirements-dev.txt"])

    assert report.dependency_files == ("requirements-dev.txt",)
    assert report.dependencies_by_type("runtime") == ()
    assert [
        dependency.normalized_name
        for dependency in report.dependencies_by_type("development")
    ] == ["pytest"]


def test_render_dependency_full_section_includes_summary_and_dependency_groups() -> None:
    from repodossier.dependencies import render_dependency_full_section

    report = DependencyReport(
        dependencies=(
            Dependency(
                name="click",
                version_constraint=">=8",
                dependency_type="runtime",
                source_file="pyproject.toml",
                source_section="project.dependencies",
                raw_value="click>=8",
            ),
            Dependency(
                name="pytest",
                version_constraint=">=8",
                dependency_type="development",
                source_file="requirements-dev.txt",
                source_section="requirements-dev.txt",
                raw_value="pytest>=8",
            ),
            Dependency(
                name="mkdocs",
                dependency_type="optional",
                source_file="pyproject.toml",
                source_section="project.optional-dependencies.docs",
                raw_value="mkdocs",
                group="docs",
            ),
        ),
        dependency_files=("pyproject.toml", "requirements-dev.txt"),
    )

    rendered = render_dependency_full_section(report)

    assert "# Dependencies" in rendered
    assert "Runtime dependencies: 1" in rendered
    assert "Development dependencies: 1" in rendered
    assert "Optional dependencies: 1" in rendered
    assert "- pyproject.toml" in rendered
    assert "- requirements-dev.txt" in rendered
    assert "- click>=8 (pyproject.toml, project.dependencies)" in rendered
    assert "- pytest>=8 (requirements-dev.txt)" in rendered
    assert "- docs: mkdocs (pyproject.toml, project.optional-dependencies.docs)" in rendered


def test_insert_dependency_full_section_before_complete_source_dump() -> None:
    from repodossier.dependencies import insert_dependency_full_section

    report = DependencyReport(
        dependencies=(
            Dependency(
                name="click",
                dependency_type="runtime",
                source_file="pyproject.toml",
                source_section="project.dependencies",
                raw_value="click>=8",
            ),
        ),
        dependency_files=("pyproject.toml",),
    )

    full_text = "# RepoDossier Full Export\n\n# Complete Source Dump\n\ncontent\n"
    rendered = insert_dependency_full_section(full_text, report)

    assert rendered.index("# Dependencies") < rendered.index("# Complete Source Dump")
    assert "Runtime dependencies: 1" in rendered
    assert "click>=8" in rendered


def test_insert_dependency_full_section_is_idempotent() -> None:
    from repodossier.dependencies import insert_dependency_full_section

    report = DependencyReport()
    full_text = "# RepoDossier Full Export\n\n# Dependencies\n\nalready here\n"

    assert insert_dependency_full_section(full_text, report) == full_text


def test_render_dependency_ai_section_is_compact_and_sorted() -> None:
    from repodossier.dependencies import render_dependency_ai_section

    report = DependencyReport(
        dependencies=(
            Dependency(
                name="ruff",
                dependency_type="development",
                source_file="requirements-dev.txt",
                raw_value="ruff",
            ),
            Dependency(
                name="click",
                dependency_type="runtime",
                source_file="pyproject.toml",
                raw_value="click>=8",
            ),
            Dependency(
                name="mkdocs",
                dependency_type="optional",
                source_file="pyproject.toml",
                raw_value="mkdocs",
                group="docs",
            ),
        ),
        dependency_files=("requirements-dev.txt", "pyproject.toml"),
    )

    rendered = render_dependency_ai_section(report)

    assert rendered.startswith("## Dependencies")
    assert "Runtime:\n\n- click>=8 (pyproject.toml)" in rendered
    assert "Development:\n\n- ruff (requirements-dev.txt)" in rendered
    assert "Optional:\n\n- docs: mkdocs (pyproject.toml)" in rendered
    assert "Detected files:\n\n- pyproject.toml\n- requirements-dev.txt" in rendered


def test_insert_dependency_ai_section_before_graph_sections() -> None:
    from repodossier.dependencies import insert_dependency_ai_section

    report = DependencyReport(
        dependencies=(
            Dependency(
                name="click",
                dependency_type="runtime",
                source_file="pyproject.toml",
                raw_value="click>=8",
            ),
        ),
        dependency_files=("pyproject.toml",),
    )

    ai_text = "# RepoDossier AI Export\n\n## Symbol Index\n\ncontent\n"
    rendered = insert_dependency_ai_section(ai_text, report)

    assert rendered.index("## Dependencies") < rendered.index("## Symbol Index")
    assert "click>=8" in rendered


def test_insert_dependency_ai_section_is_idempotent() -> None:
    from repodossier.dependencies import insert_dependency_ai_section

    report = DependencyReport()
    ai_text = "# RepoDossier AI Export\n\n## Dependencies\n\nalready here\n"

    assert insert_dependency_ai_section(ai_text, report) == ai_text

