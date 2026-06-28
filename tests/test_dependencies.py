from __future__ import annotations

import pytest

from repocontext.dependencies import (
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


def test_analyze_dependencies_returns_empty_report_for_initial_scaffold(tmp_path) -> None:
    report = analyze_dependencies(tmp_path, files=[])

    assert isinstance(report, DependencyReport)
    assert report.is_empty()
    assert report.counts_by_type() == {
        "runtime": 0,
        "development": 0,
        "optional": 0,
        "unknown": 0,
    }
