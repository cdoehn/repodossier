from repocontext.symbols import (
    FileSymbolIndex,
    SymbolInfo,
    extract_symbols_from_file,
)


def test_symbol_info_model_stores_basic_fields():
    symbol = SymbolInfo(
        name="main",
        kind="function",
        file_path="src/example.py",
        line_start=10,
        line_end=12,
        parent=None,
    )

    assert symbol.name == "main"
    assert symbol.kind == "function"
    assert symbol.file_path == "src/example.py"
    assert symbol.line_start == 10
    assert symbol.line_end == 12
    assert symbol.parent is None


def test_file_symbol_index_defaults_to_empty_symbols_and_errors():
    index = FileSymbolIndex(file_path="src/example.py")

    assert index.file_path == "src/example.py"
    assert index.symbols == []
    assert index.errors == []


def test_extract_symbols_from_empty_python_file(tmp_path):
    path = tmp_path / "empty.py"
    path.write_text("", encoding="utf-8")

    index = extract_symbols_from_file(path)

    assert index.file_path == str(path)
    assert index.symbols == []
    assert index.errors == []


def test_extract_symbols_from_valid_python_file(tmp_path):
    path = tmp_path / "valid.py"
    path.write_text(
        "def hello():\n"
        "    return 'world'\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(path)

    assert index.file_path == str(path)
    assert index.symbols == []
    assert index.errors == []


def test_extract_symbols_from_syntax_error_file(tmp_path):
    path = tmp_path / "broken.py"
    path.write_text(
        "def broken(:\n"
        "    pass\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(path)

    assert index.file_path == str(path)
    assert index.symbols == []
    assert len(index.errors) == 1
    assert index.errors[0].startswith("SyntaxError")
    assert "line 1" in index.errors[0]


def test_extract_symbols_from_missing_file(tmp_path):
    path = tmp_path / "missing.py"

    index = extract_symbols_from_file(path)

    assert index.file_path == str(path)
    assert index.symbols == []
    assert len(index.errors) == 1
    assert index.errors[0].startswith("FileNotFoundError")
