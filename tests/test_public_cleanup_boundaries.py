from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_METADATA_FILES = [
    "README.md",
    "pyproject.toml",
    ".github/ISSUE_TEMPLATE/config.yml",
    "docs/public-cleanup-boundaries.md",
]

TEST_PRIVATE_FIXTURE_ALLOWLIST = {
    "tests/test_private_data_cleanup.py",
    "tests/test_check_dev_environment.py",
}

def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")

def test_public_metadata_uses_neutral_project_github_namespace() -> None:
    readme = _read("README.md")
    pyproject = _read("pyproject.toml")
    issue_config = _read(".github/ISSUE_TEMPLATE/config.yml")
    expected = "https://github.com/repodossier/repodossier"
    assert expected in readme
    assert expected in pyproject
    assert expected in issue_config

def test_public_metadata_does_not_store_previous_private_identity_fragments() -> None:
    combined = "\n".join(_read(path) for path in PUBLIC_METADATA_FILES)
    forbidden = [
        "c" + "do" + "ehn",
        "do" + "ehn",
        "D" + "\u00f6hn",
        "/home/" + "exampleuser",
        "example.user" + "@" + "example.invalid",
        "Example" + "Laptop",
        "Example" + "Machine",
        "~/" + "Projects",
    ]
    for value in forbidden:
        assert value not in combined


def test_private_fixture_boundary_is_documented() -> None:
    text = _read("docs/public-cleanup-boundaries.md")
    assert "Dedicated tests may contain reconstructed private-like fixtures" in text
    assert "must not depend on unrelated sibling repositories" in text

def test_private_fixture_allowlist_is_limited_to_tests() -> None:
    for relative in TEST_PRIVATE_FIXTURE_ALLOWLIST:
        assert relative.startswith("tests/")
        assert (ROOT / relative).is_file()
