from pathlib import Path

import pytest

from repocontext.import_graph import (
    ImportAnalysisError,
    ImportEdge,
    ImportReference,
    build_python_module_map,
    module_name_from_python_path,
    resolve_absolute_import_reference,
    resolve_absolute_imports,
    parse_imports_from_file,
    parse_imports_from_source,
)


def test_import_reference_stores_basic_import_metadata() -> None:
    reference = ImportReference(
        source_path=Path("src/repocontext/cli.py"),
        source_module="repocontext.cli",
        imported_module="argparse",
        import_type="import",
        line_number=3,
    )

    assert reference.source_path == Path("src/repocontext/cli.py")
    assert reference.source_module == "repocontext.cli"
    assert reference.imported_module == "argparse"
    assert reference.imported_name is None
    assert reference.alias is None
    assert reference.import_type == "import"
    assert reference.level == 0
    assert reference.line_number == 3
    assert reference.is_relative is False
    assert reference.is_local is None
    assert reference.resolved_module is None
    assert reference.resolved_path is None


def test_import_reference_stores_from_import_alias_and_relative_level() -> None:
    reference = ImportReference(
        source_path="src/repocontext/exporter.py",
        source_module="repocontext.exporter",
        imported_module="scanner",
        imported_name="scan_files",
        alias="scan",
        import_type="from",
        level=1,
        line_number=8,
        is_relative=True,
        is_local=True,
        resolved_module="repocontext.scanner",
        resolved_path="src/repocontext/scanner.py",
    )

    assert reference.source_path == Path("src/repocontext/exporter.py")
    assert reference.imported_module == "scanner"
    assert reference.imported_name == "scan_files"
    assert reference.alias == "scan"
    assert reference.import_type == "from"
    assert reference.level == 1
    assert reference.line_number == 8
    assert reference.is_relative is True
    assert reference.is_local is True
    assert reference.resolved_module == "repocontext.scanner"
    assert reference.resolved_path == Path("src/repocontext/scanner.py")


def test_import_edge_stores_local_dependency_metadata() -> None:
    edge = ImportEdge(
        source_module="repocontext.exporter",
        target_module="repocontext.scanner",
        source_path="src/repocontext/exporter.py",
        target_path="src/repocontext/scanner.py",
        import_type="from",
        imported_name="scan_files",
        line_number=12,
    )

    assert edge.source_module == "repocontext.exporter"
    assert edge.target_module == "repocontext.scanner"
    assert edge.source_path == Path("src/repocontext/exporter.py")
    assert edge.target_path == Path("src/repocontext/scanner.py")
    assert edge.import_type == "from"
    assert edge.imported_name == "scan_files"
    assert edge.line_number == 12


def test_import_analysis_error_stores_non_fatal_error_details() -> None:
    error = ImportAnalysisError(
        source_path="src/repocontext/broken.py",
        message="invalid syntax",
        error_type="SyntaxError",
        line_number=4,
    )

    assert error.source_path == Path("src/repocontext/broken.py")
    assert error.message == "invalid syntax"
    assert error.error_type == "SyntaxError"
    assert error.line_number == 4


@pytest.mark.parametrize("model", [ImportReference, ImportEdge])
def test_import_type_must_be_supported(model) -> None:
    kwargs = {
        "import_type": "dynamic",
        "line_number": 1,
    }

    if model is ImportReference:
        kwargs.update(
            {
                "source_path": Path("src/repocontext/cli.py"),
                "source_module": "repocontext.cli",
                "imported_module": "argparse",
            }
        )
    else:
        kwargs.update(
            {
                "source_module": "repocontext.cli",
                "target_module": "repocontext.exporter",
                "source_path": Path("src/repocontext/cli.py"),
                "target_path": Path("src/repocontext/exporter.py"),
            }
        )

    with pytest.raises(ValueError, match="import_type"):
        model(**kwargs)


def test_import_reference_rejects_negative_level() -> None:
    with pytest.raises(ValueError, match="level"):
        ImportReference(
            source_path=Path("src/repocontext/cli.py"),
            source_module="repocontext.cli",
            imported_module="argparse",
            level=-1,
        )


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ImportReference(
            source_path=Path("src/repocontext/cli.py"),
            source_module="repocontext.cli",
            imported_module="argparse",
            line_number=-1,
        ),
        lambda: ImportEdge(
            source_module="repocontext.cli",
            target_module="repocontext.exporter",
            source_path=Path("src/repocontext/cli.py"),
            target_path=Path("src/repocontext/exporter.py"),
            import_type="import",
            line_number=-1,
        ),
        lambda: ImportAnalysisError(
            source_path=Path("src/repocontext/broken.py"),
            message="invalid syntax",
            line_number=-1,
        ),
    ],
)
def test_line_numbers_must_not_be_negative(factory) -> None:
    with pytest.raises(ValueError, match="line_number"):
        factory()




def test_module_name_from_python_path_handles_src_layout_modules() -> None:
    assert (
        module_name_from_python_path("src/repocontext/scanner.py")
        == "repocontext.scanner"
    )
    assert (
        module_name_from_python_path("src/repocontext/nested/helper.py")
        == "repocontext.nested.helper"
    )


def test_module_name_from_python_path_handles_src_layout_package_init() -> None:
    assert (
        module_name_from_python_path("src/repocontext/__init__.py")
        == "repocontext"
    )
    assert (
        module_name_from_python_path("src/repocontext/nested/__init__.py")
        == "repocontext.nested"
    )


def test_module_name_from_python_path_handles_root_layout_and_tests() -> None:
    assert (
        module_name_from_python_path("repocontext/scanner.py")
        == "repocontext.scanner"
    )
    assert (
        module_name_from_python_path("tests/test_scanner.py")
        == "tests.test_scanner"
    )


def test_module_name_from_python_path_respects_repo_root(tmp_path: Path) -> None:
    source_path = tmp_path / "src" / "repocontext" / "scanner.py"

    assert (
        module_name_from_python_path(source_path, repo_root=tmp_path)
        == "repocontext.scanner"
    )


def test_module_name_from_python_path_ignores_non_python_and_invalid_paths() -> None:
    assert module_name_from_python_path("README.md") is None
    assert module_name_from_python_path("src/example-data/module.py") is None
    assert module_name_from_python_path("src/repocontext/__init__.py.md") is None


def test_build_python_module_map_returns_deterministic_module_to_path_mapping() -> None:
    module_map = build_python_module_map(
        [
            "README.md",
            "src/repocontext/scanner.py",
            "src/repocontext/__init__.py",
            "tests/test_scanner.py",
            "src/repocontext/scanner.py",
        ]
    )

    assert module_map == {
        "repocontext": Path("src/repocontext/__init__.py"),
        "repocontext.scanner": Path("src/repocontext/scanner.py"),
        "tests.test_scanner": Path("tests/test_scanner.py"),
    }




def test_resolve_absolute_import_reference_marks_exact_local_import() -> None:
    reference = ImportReference(
        source_path="src/repocontext/cli.py",
        source_module="repocontext.cli",
        imported_module="repocontext.scanner",
        import_type="import",
        line_number=5,
    )

    resolved = resolve_absolute_import_reference(
        reference,
        {
            "repocontext": Path("src/repocontext/__init__.py"),
            "repocontext.scanner": Path("src/repocontext/scanner.py"),
        },
    )

    assert resolved.is_local is True
    assert resolved.resolved_module == "repocontext.scanner"
    assert resolved.resolved_path == Path("src/repocontext/scanner.py")


def test_resolve_absolute_import_reference_marks_from_import_module_as_local() -> None:
    reference = ImportReference(
        source_path="src/repocontext/exporter.py",
        source_module="repocontext.exporter",
        imported_module="repocontext.git",
        imported_name="discover_repo",
        import_type="from",
        line_number=7,
    )

    resolved = resolve_absolute_import_reference(
        reference,
        {
            "repocontext.git": Path("src/repocontext/git.py"),
        },
    )

    assert resolved.is_local is True
    assert resolved.resolved_module == "repocontext.git"
    assert resolved.resolved_path == Path("src/repocontext/git.py")


def test_resolve_absolute_import_reference_prefers_imported_submodule_from_package() -> None:
    reference = ImportReference(
        source_path="src/repocontext/cli.py",
        source_module="repocontext.cli",
        imported_module="repocontext",
        imported_name="scanner",
        import_type="from",
        line_number=9,
    )

    resolved = resolve_absolute_import_reference(
        reference,
        {
            "repocontext": Path("src/repocontext/__init__.py"),
            "repocontext.scanner": Path("src/repocontext/scanner.py"),
        },
    )

    assert resolved.is_local is True
    assert resolved.resolved_module == "repocontext.scanner"
    assert resolved.resolved_path == Path("src/repocontext/scanner.py")


def test_resolve_absolute_import_reference_marks_external_import_as_not_local() -> None:
    reference = ImportReference(
        source_path="src/repocontext/cli.py",
        source_module="repocontext.cli",
        imported_module="pathlib",
        imported_name="Path",
        import_type="from",
        line_number=3,
    )

    resolved = resolve_absolute_import_reference(
        reference,
        {
            "repocontext.cli": Path("src/repocontext/cli.py"),
        },
    )

    assert resolved.is_local is False
    assert resolved.resolved_module is None
    assert resolved.resolved_path is None


def test_resolve_absolute_import_reference_leaves_relative_imports_for_later_step() -> None:
    reference = ImportReference(
        source_path="src/repocontext/exporter.py",
        source_module="repocontext.exporter",
        imported_module="scanner",
        imported_name="scan_files",
        import_type="from",
        level=1,
        line_number=11,
        is_relative=True,
    )

    resolved = resolve_absolute_import_reference(
        reference,
        {
            "repocontext.scanner": Path("src/repocontext/scanner.py"),
        },
    )

    assert resolved == reference
    assert resolved.is_local is None
    assert resolved.resolved_module is None
    assert resolved.resolved_path is None


def test_resolve_absolute_imports_resolves_multiple_references() -> None:
    references = [
        ImportReference(
            source_path="src/repocontext/cli.py",
            source_module="repocontext.cli",
            imported_module="repocontext.exporter",
            import_type="import",
            line_number=1,
        ),
        ImportReference(
            source_path="src/repocontext/cli.py",
            source_module="repocontext.cli",
            imported_module="argparse",
            import_type="import",
            line_number=2,
        ),
    ]

    resolved = resolve_absolute_imports(
        references,
        {
            "repocontext.exporter": Path("src/repocontext/exporter.py"),
        },
    )

    assert [reference.is_local for reference in resolved] == [True, False]
    assert resolved[0].resolved_module == "repocontext.exporter"
    assert resolved[1].resolved_module is None


def test_parse_imports_from_source_detects_plain_imports() -> None:
    references, errors = parse_imports_from_source(
        """
import os
import pathlib as p
import package.module
""",
        source_path="src/repocontext/example.py",
        source_module="repocontext.example",
    )

    assert errors == []
    assert [
        (ref.import_type, ref.imported_module, ref.imported_name, ref.alias, ref.line_number)
        for ref in references
    ] == [
        ("import", "os", None, None, 2),
        ("import", "pathlib", None, "p", 3),
        ("import", "package.module", None, None, 4),
    ]


def test_parse_imports_from_source_detects_from_imports() -> None:
    references, errors = parse_imports_from_source(
        """
from pathlib import Path, PurePath as PP
from repocontext.scanner import scan_files
""",
        source_path="src/repocontext/example.py",
        source_module="repocontext.example",
    )

    assert errors == []
    assert [
        (ref.import_type, ref.imported_module, ref.imported_name, ref.alias, ref.line_number)
        for ref in references
    ] == [
        ("from", "pathlib", "Path", None, 2),
        ("from", "pathlib", "PurePath", "PP", 2),
        ("from", "repocontext.scanner", "scan_files", None, 3),
    ]


def test_parse_imports_from_source_detects_relative_and_wildcard_imports() -> None:
    references, errors = parse_imports_from_source(
        """
from .scanner import scan_files
from ..git import discover_repo as discover
from . import symbols
from repocontext.symbols import *
""",
        source_path="src/repocontext/exporter.py",
        source_module="repocontext.exporter",
    )

    assert errors == []
    assert [
        (
            ref.imported_module,
            ref.imported_name,
            ref.alias,
            ref.level,
            ref.is_relative,
            ref.line_number,
        )
        for ref in references
    ] == [
        ("scanner", "scan_files", None, 1, True, 2),
        ("git", "discover_repo", "discover", 2, True, 3),
        (None, "symbols", None, 1, True, 4),
        ("repocontext.symbols", "*", None, 0, False, 5),
    ]




def test_parse_imports_from_source_detects_multiple_plain_imports_in_one_statement() -> None:
    references, errors = parse_imports_from_source(
        """
import os, sys as system
""",
        source_path="src/repocontext/example.py",
        source_module="repocontext.example",
    )

    assert errors == []
    assert [
        (ref.import_type, ref.imported_module, ref.imported_name, ref.alias, ref.line_number)
        for ref in references
    ] == [
        ("import", "os", None, None, 2),
        ("import", "sys", None, "system", 2),
    ]


def test_parse_imports_from_source_detects_multiline_from_imports() -> None:
    references, errors = parse_imports_from_source(
        """
from repocontext.symbols import (
    Symbol,
    SymbolKind as Kind,
)
""",
        source_path="src/repocontext/example.py",
        source_module="repocontext.example",
    )

    assert errors == []
    assert [
        (ref.import_type, ref.imported_module, ref.imported_name, ref.alias, ref.line_number)
        for ref in references
    ] == [
        ("from", "repocontext.symbols", "Symbol", None, 2),
        ("from", "repocontext.symbols", "SymbolKind", "Kind", 2),
    ]


def test_parse_imports_from_source_detects_imports_inside_scopes() -> None:
    references, errors = parse_imports_from_source(
        """
class Loader:
    import json as json_module

    def load(self):
        from pathlib import Path

def helper():
    import collections.abc
""",
        source_path="src/repocontext/example.py",
        source_module="repocontext.example",
    )

    assert errors == []
    assert [
        (ref.import_type, ref.imported_module, ref.imported_name, ref.alias, ref.line_number)
        for ref in references
    ] == [
        ("import", "json", None, "json_module", 3),
        ("from", "pathlib", "Path", None, 6),
        ("import", "collections.abc", None, None, 9),
    ]


def test_parse_imports_from_source_detects_conditional_imports() -> None:
    references, errors = parse_imports_from_source(
        """
if TYPE_CHECKING:
    from repocontext.scanner import ScannedFile

try:
    import tomllib
except ImportError:
    import tomli as tomllib
""",
        source_path="src/repocontext/example.py",
        source_module="repocontext.example",
    )

    assert errors == []
    assert [
        (ref.import_type, ref.imported_module, ref.imported_name, ref.alias, ref.line_number)
        for ref in references
    ] == [
        ("from", "repocontext.scanner", "ScannedFile", None, 3),
        ("import", "tomllib", None, None, 6),
        ("import", "tomli", None, "tomllib", 8),
    ]


def test_parse_imports_from_source_detects_relative_package_import_aliases() -> None:
    references, errors = parse_imports_from_source(
        """
from .. import git as repo_git
from . import scanner, symbols as symbol_module
from .scanner import *
""",
        source_path="src/repocontext/subpkg/example.py",
        source_module="repocontext.subpkg.example",
    )

    assert errors == []
    assert [
        (
            ref.imported_module,
            ref.imported_name,
            ref.alias,
            ref.level,
            ref.is_relative,
            ref.line_number,
        )
        for ref in references
    ] == [
        (None, "git", "repo_git", 2, True, 2),
        (None, "scanner", None, 1, True, 3),
        (None, "symbols", "symbol_module", 1, True, 3),
        ("scanner", "*", None, 1, True, 4),
    ]


def test_parse_imports_from_source_collects_syntax_errors_without_raising() -> None:
    references, errors = parse_imports_from_source(
        "from import broken\n",
        source_path="src/repocontext/broken.py",
        source_module="repocontext.broken",
    )

    assert references == []
    assert len(errors) == 1
    assert errors[0].source_path == Path("src/repocontext/broken.py")
    assert errors[0].error_type == "SyntaxError"
    assert errors[0].line_number == 1


def test_parse_imports_from_file_reads_python_file(tmp_path: Path) -> None:
    source_path = tmp_path / "module.py"
    source_path.write_text("import os\nfrom pathlib import Path\n", encoding="utf-8")

    references, errors = parse_imports_from_file(
        source_path,
        source_module="module",
    )

    assert errors == []
    assert [
        (ref.import_type, ref.imported_module, ref.imported_name)
        for ref in references
    ] == [
        ("import", "os", None),
        ("from", "pathlib", "Path"),
    ]


def test_parse_imports_from_file_collects_read_errors(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.py"

    references, errors = parse_imports_from_file(
        missing_path,
        source_module="missing",
    )

    assert references == []
    assert len(errors) == 1
    assert errors[0].source_path == missing_path
    assert errors[0].error_type in {"FileNotFoundError", "OSError"}
