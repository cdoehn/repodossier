import pytest

from repodossier.export_model import FileEntry
from repodossier.export_model_configuration import make_export_configuration_summary
from repodossier.export_model_factory import make_repository_export
from repodossier.export_model_modes import export_mode_default_sections
from repodossier.export_model_reports import make_dependency_report
from repodossier.export_model_sections import (
    export_mode_sections,
    export_section_title,
    known_export_sections,
    normalize_export_section,
    repository_export_has_section,
    repository_export_populated_sections,
    repository_export_section_presence,
    repository_export_sections,
)
from repodossier.export_model_warnings import make_export_warning


def make_section_export():
    return make_repository_export(
        mode="full",
        root_path="/repo",
        root_name="repo",
        configuration=make_export_configuration_summary(
            config_active=True,
            include_paths=("src",),
        ),
        files=(
            FileEntry(
                path="src/app.py",
                language="python",
                status="included",
                content="print(1)\n",
            ),
        ),
        warnings=(
            make_export_warning(
                "Example warning",
                path="src/app.py",
                code="example",
            ),
        ),
        dependencies=make_dependency_report(
            ({"package": "pytest", "source": "pyproject.toml"},)
        ),
    )


def test_normalize_export_section_accepts_common_spellings():
    assert normalize_export_section(" Source Export ") == "source_export"
    assert normalize_export_section("git-diff") == "git_diff"
    assert normalize_export_section("repository  metadata") == "repository_metadata"

    with pytest.raises(ValueError, match="must not be empty"):
        normalize_export_section("  ---  ")


def test_export_section_title_uses_known_and_fallback_titles():
    assert export_section_title("source_export") == "Source Export"
    assert export_section_title("git-diff") == "Git Diff"
    assert export_section_title("custom_section") == "Custom Section"


def test_known_export_sections_includes_mode_sections_and_titles():
    sections = known_export_sections()

    assert sections == tuple(sorted(sections))
    assert "repository_metadata" in sections
    assert "summary" in sections
    assert "source_export" in sections


def test_export_mode_sections_matches_mode_defaults():
    assert export_mode_sections(" FULL ") == export_mode_default_sections("full")
    assert export_mode_sections("ai") == export_mode_default_sections("ai")
    assert export_mode_sections("docs") == export_mode_default_sections("docs")
    assert export_mode_sections("changed") == export_mode_default_sections("changed")


def test_repository_export_sections_uses_export_mode():
    export = make_section_export()

    assert repository_export_sections(export) == export_mode_default_sections("full")


def test_repository_export_section_presence_marks_populated_sections():
    export = make_section_export()

    presence = repository_export_section_presence(export)

    assert tuple(presence) == repository_export_sections(export)
    assert presence["repository_metadata"] is True
    assert presence["summary"] is True

    if "configuration" in presence:
        assert presence["configuration"] is True

    if "repository_tree" in presence:
        assert presence["repository_tree"] is True

    if "dependencies" in presence:
        assert presence["dependencies"] is True

    if "warnings" in presence:
        assert presence["warnings"] is True

    if "source_export" in presence:
        assert presence["source_export"] is True

    if "database_schema" in presence:
        assert presence["database_schema"] is False


def test_repository_export_populated_sections_preserves_mode_order():
    export = make_section_export()

    populated = repository_export_populated_sections(export)
    defaults = repository_export_sections(export)

    assert populated
    assert populated == tuple(section for section in defaults if section in populated)
    assert "repository_metadata" in populated
    assert "summary" in populated

    if "database_schema" in defaults:
        assert "database_schema" not in populated


def test_repository_export_has_section_can_require_presence_or_only_definition():
    export = make_section_export()

    assert repository_export_has_section(export, "repository-metadata")
    assert repository_export_has_section(
        export,
        "repository-metadata",
        require_populated=False,
    )

    if "database_schema" in repository_export_sections(export):
        assert not repository_export_has_section(export, "database_schema")
        assert repository_export_has_section(
            export,
            "database_schema",
            require_populated=False,
        )

    assert not repository_export_has_section(export, "not_a_section")
