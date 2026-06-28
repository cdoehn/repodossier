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


def test_extract_symbols_from_valid_python_file_with_one_function(tmp_path):
    path = tmp_path / "valid.py"
    path.write_text(
        "def hello():\n"
        "    return 'world'\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(path)

    assert index.file_path == str(path)
    assert index.errors == []
    assert len(index.symbols) == 1
    assert index.symbols[0].name == "hello"
    assert index.symbols[0].kind == "function"
    assert index.symbols[0].file_path == str(path)
    assert index.symbols[0].line_start == 1
    assert index.symbols[0].line_end == 2
    assert index.symbols[0].parent is None


def test_extract_symbols_from_multiple_top_level_functions(tmp_path):
    path = tmp_path / "multiple.py"
    path.write_text(
        "def first():\n"
        "    return 1\n"
        "\n"
        "def second():\n"
        "    return 2\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(path)

    assert index.errors == []
    assert [symbol.name for symbol in index.symbols] == ["first", "second"]
    assert [symbol.kind for symbol in index.symbols] == ["function", "function"]
    assert [symbol.line_start for symbol in index.symbols] == [1, 4]


def test_extract_symbols_from_async_top_level_function(tmp_path):
    path = tmp_path / "async_example.py"
    path.write_text(
        "async def fetch_data():\n"
        "    return 42\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(path)

    assert index.errors == []
    assert len(index.symbols) == 1
    assert index.symbols[0].name == "fetch_data"
    assert index.symbols[0].kind == "function"
    assert index.symbols[0].line_start == 1
    assert index.symbols[0].line_end == 2
    assert index.symbols[0].parent is None


def test_extract_symbols_does_not_count_methods_as_top_level_functions(tmp_path):
    path = tmp_path / "class_with_method.py"
    path.write_text(
        "class Example:\n"
        "    def method(self):\n"
        "        return 'method'\n"
        "\n"
        "def top_level():\n"
        "    return 'function'\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(path)

    assert index.errors == []
    assert [symbol.name for symbol in index.symbols] == ["top_level"]
    assert index.symbols[0].kind == "function"
    assert index.symbols[0].parent is None


def test_extract_symbols_ignores_nested_functions_for_mvp(tmp_path):
    path = tmp_path / "nested.py"
    path.write_text(
        "def outer():\n"
        "    def inner():\n"
        "        return 'inner'\n"
        "    return inner()\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(path)

    assert index.errors == []
    assert [symbol.name for symbol in index.symbols] == ["outer"]


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
