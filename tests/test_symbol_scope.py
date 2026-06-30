from pathlib import Path
import tomllib

from repodossier.symbols import (
    build_symbol_index,
    extract_symbols_from_file,
    format_symbol_index,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "repodossier"


def _package_source_files():
    return sorted(PACKAGE_ROOT.rglob("*.py"))


def test_symbol_helpers_remain_internal_and_importable_for_future_exports():
    assert callable(extract_symbols_from_file)
    assert callable(build_symbol_index)
    assert callable(format_symbol_index)


def test_symbol_extraction_does_not_create_standalone_export_filename():
    offenders = []

    for path in _package_source_files():
        text = path.read_text(encoding="utf-8")
        if "symbols.txt" in text:
            offenders.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert offenders == []


def test_symbol_extraction_is_only_wired_into_expected_export_pipelines():
    """Milestone 8 wires build_symbol_index into ai.txt while full export still uses it for call graph generation."""

    still_forbidden_tokens = (
        "extract_symbols_from_file(",
        "format_symbol_index(",
    )
    offenders = []

    for path in _package_source_files():
        if path.name == "symbols.py":
            continue

        text = path.read_text(encoding="utf-8")
        for token in still_forbidden_tokens:
            if token in text:
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT).as_posix()} contains {token}"
                )

    assert offenders == []

    build_symbol_index_users = []
    for path in _package_source_files():
        if path.name == "symbols.py":
            continue

        text = path.read_text(encoding="utf-8")
        if "build_symbol_index(" in text:
            build_symbol_index_users.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert build_symbol_index_users == [
        "src/repodossier/exporters/ai.py",
        "src/repodossier/exporters/full.py",
    ]


def test_project_scripts_do_not_add_symbol_specific_cli_entrypoints():
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    scripts = pyproject.get("project", {}).get("scripts", {})

    symbol_scripts = [
        name
        for name in scripts
        if "symbol" in name.lower() or "symbols" in name.lower()
    ]

    assert symbol_scripts == []


def test_full_export_filenames_are_not_extended_with_symbols_export():
    known_export_names = {"full.txt", "ai.txt", "docs.txt", "changed.txt"}
    package_text = "\n".join(
        path.read_text(encoding="utf-8") for path in _package_source_files()
    )

    assert "symbols.txt" not in package_text
    assert known_export_names == {"full.txt", "ai.txt", "docs.txt", "changed.txt"}
