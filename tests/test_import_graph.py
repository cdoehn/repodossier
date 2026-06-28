from pathlib import Path

import pytest

from repocontext.import_graph import (
    ImportAnalysisError,
    ImportEdge,
    ImportReference,
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
