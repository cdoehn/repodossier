from repocontext.exporters.docs import (
    ARCHITECTURE_DOCUMENTATION_CATEGORY,
    CHANGELOG_AND_CONTRIBUTION_CATEGORY,
    DOCUMENTATION_CATEGORY_ORDER,
    LICENSE_CATEGORY,
    OTHER_DOCS_CATEGORY,
    PRIMARY_DOCUMENTATION_CATEGORY,
    SPECIFICATION_DOCUMENTATION_CATEGORY,
    TASKS_AND_ROADMAP_CATEGORY,
    categorize_documentation_file,
    is_documentation_file,
)


def test_documentation_file_detection_accepts_primary_documentation_files():
    assert is_documentation_file("README.md")
    assert is_documentation_file("README.rst")
    assert is_documentation_file("README.txt")
    assert is_documentation_file("README")
    assert categorize_documentation_file("README.md") == PRIMARY_DOCUMENTATION_CATEGORY


def test_documentation_file_detection_accepts_architecture_and_spec_files():
    assert is_documentation_file("ARCHITECTURE.md")
    assert is_documentation_file("REPOCONTEXT_ARCHITECTURE.md")
    assert is_documentation_file("SPEC.md")
    assert is_documentation_file("SPEC.txt")
    assert is_documentation_file("REPOCONTEXT_SPEC_v1.3.txt")

    assert categorize_documentation_file("REPOCONTEXT_ARCHITECTURE.md") == ARCHITECTURE_DOCUMENTATION_CATEGORY
    assert categorize_documentation_file("REPOCONTEXT_SPEC_v1.3.txt") == SPECIFICATION_DOCUMENTATION_CATEGORY


def test_documentation_file_detection_accepts_tasks_roadmap_and_planning_files():
    assert is_documentation_file("TASKS.md")
    assert is_documentation_file("ROADMAP.md")
    assert is_documentation_file("REPOCONTEXT_ROADMAP.md")
    assert is_documentation_file("planning/REPOCONTEXT_ROADMAP.md")
    assert is_documentation_file("planning/MILESTONE9.md")

    assert categorize_documentation_file("TASKS.md") == TASKS_AND_ROADMAP_CATEGORY
    assert categorize_documentation_file("planning/REPOCONTEXT_ROADMAP.md") == TASKS_AND_ROADMAP_CATEGORY


def test_documentation_file_detection_accepts_docs_directory_text_files():
    assert is_documentation_file("docs/usage.md")
    assert is_documentation_file("docs/reference.txt")
    assert is_documentation_file("docs/nested/guide.rst")

    assert categorize_documentation_file("docs/usage.md") == OTHER_DOCS_CATEGORY


def test_documentation_file_detection_accepts_changelog_contributing_and_license():
    assert is_documentation_file("CHANGELOG.md")
    assert is_documentation_file("CONTRIBUTING.md")
    assert is_documentation_file("LICENSE")
    assert is_documentation_file("LICENSE.md")

    assert categorize_documentation_file("CHANGELOG.md") == CHANGELOG_AND_CONTRIBUTION_CATEGORY
    assert categorize_documentation_file("CONTRIBUTING.md") == CHANGELOG_AND_CONTRIBUTION_CATEGORY
    assert categorize_documentation_file("LICENSE") == LICENSE_CATEGORY


def test_documentation_file_detection_rejects_code_tests_and_generated_exports():
    assert not is_documentation_file("src/repocontext/cli.py")
    assert not is_documentation_file("tests/test_cli.py")
    assert not is_documentation_file("pyproject.toml")

    assert not is_documentation_file("full.txt")
    assert not is_documentation_file("ai.txt")
    assert not is_documentation_file("docs.txt")
    assert not is_documentation_file("changed.txt")
    assert not is_documentation_file("docs/docs.txt")


def test_documentation_file_detection_rejects_binary_or_non_text_docs():
    assert not is_documentation_file("docs/manual.pdf")
    assert not is_documentation_file("docs/archive.zip")
    assert not is_documentation_file("README.md", is_binary=True)


def test_documentation_category_order_is_stable():
    assert DOCUMENTATION_CATEGORY_ORDER == (
        "Primary documentation",
        "Architecture documentation",
        "Specification documentation",
        "Tasks and roadmap",
        "Changelog and contribution docs",
        "License",
        "Other docs",
    )


def test_documentation_file_detection_is_case_insensitive():
    assert is_documentation_file("readme.MD")
    assert is_documentation_file("Docs/Usage.MD")
    assert is_documentation_file("planning/milestone9.MD")
    assert categorize_documentation_file("readme.MD") == PRIMARY_DOCUMENTATION_CATEGORY
