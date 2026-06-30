from pathlib import Path
import re


def _readme() -> str:
    return Path("README.md").read_text(encoding="utf-8")


def _status_sections(readme: str) -> tuple[str, str]:
    implemented_start = readme.index("Implemented:")
    planned_start = readme.index("Planned but not complete yet:")

    implemented_section = readme[implemented_start:planned_start]

    planned_match = re.search(
        r"(Planned but not complete yet:\n)(?P<body>.*?)(?=\n## |\Z)",
        readme,
        flags=re.DOTALL,
    )
    assert planned_match is not None

    return implemented_section, planned_match.group("body")


def test_readme_lists_configuration_as_implemented():
    implemented_section, _planned_section = _status_sections(_readme())

    assert "- configuration via `.repodossier.yml`" in implemented_section


def test_readme_does_not_list_configuration_as_planned():
    _implemented_section, planned_section = _status_sections(_readme())

    assert ".repodossier.yml" not in planned_section
    assert "configuration" not in planned_section.lower()
    assert "config" not in planned_section.lower()


def test_readme_no_longer_says_configuration_support_is_planned():
    readme = _readme()

    assert "Configuration support is planned" not in readme
    assert "configuration support is planned" not in readme
    assert ".repodossier.yml" in readme
