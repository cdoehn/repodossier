from pathlib import Path

import pytest

from repocontext.import_graph import (
    ImportAnalysisError,
    ImportEdge,
    ImportReference,
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
