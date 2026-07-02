import pytest

from repodossier.export_model import RepositoryExport, RepositoryMetadata
from repodossier.export_model_modes import (
    MODE_DEFAULT_SECTIONS,
    VALID_EXPORT_MODES,
    export_mode_default_sections,
    export_mode_includes_source_content,
    export_mode_is_review_focused,
    export_mode_title,
    is_valid_export_mode,
    normalize_export_mode,
    repository_export_default_sections,
    repository_export_title,
)


def test_valid_export_modes_are_stable():
    assert VALID_EXPORT_MODES == (
        "full",
        "ai",
        "docs",
        "changed",
    )


def test_normalize_export_mode_accepts_whitespace_case_and_hyphens():
    assert normalize_export_mode(" FULL ") == "full"
    assert normalize_export_mode("Ai") == "ai"
    assert normalize_export_mode("docs") == "docs"
    assert normalize_export_mode("changed") == "changed"


def test_normalize_export_mode_rejects_unknown_mode():
    with pytest.raises(ValueError, match="unknown export mode"):
        normalize_export_mode("xml")


def test_is_valid_export_mode_returns_boolean():
    assert is_valid_export_mode("full")
    assert is_valid_export_mode(" AI ")
    assert not is_valid_export_mode("xml")


def test_export_mode_title_returns_human_readable_titles():
    assert export_mode_title("full") == "Full Repository Export"
    assert export_mode_title("ai") == "AI Repository Export"
    assert export_mode_title("docs") == "Documentation Export"
    assert export_mode_title("changed") == "Changed Files Export"


def test_export_mode_default_sections_are_mode_specific_and_stable():
    assert export_mode_default_sections("full") == MODE_DEFAULT_SECTIONS["full"]
    assert "source_export" in export_mode_default_sections("full")
    assert "important_files" in export_mode_default_sections("ai")
    assert "document_export" in export_mode_default_sections("docs")
    assert "git_diff" in export_mode_default_sections("changed")


def test_export_mode_includes_source_content_is_conservative():
    assert export_mode_includes_source_content("full")
    assert not export_mode_includes_source_content("ai")
    assert export_mode_includes_source_content("docs")
    assert export_mode_includes_source_content("changed")


def test_export_mode_is_review_focused_only_for_changed_mode():
    assert not export_mode_is_review_focused("full")
    assert not export_mode_is_review_focused("ai")
    assert not export_mode_is_review_focused("docs")
    assert export_mode_is_review_focused("changed")


def test_repository_export_mode_helpers_use_export_mode():
    export = RepositoryExport(
        mode="ai",
        repository=RepositoryMetadata(root_path="/repo", root_name="repo"),
    )

    assert repository_export_title(export) == "AI Repository Export"
    assert repository_export_default_sections(export) == MODE_DEFAULT_SECTIONS["ai"]
