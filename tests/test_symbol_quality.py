from repocontext.symbols import (
    build_symbol_index,
    extract_symbols_from_file,
    format_symbol_index,
)


def test_symbol_extraction_does_not_execute_python_code(tmp_path):
    marker = tmp_path / "should_not_exist.txt"
    module = tmp_path / "dangerous.py"
    module.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n"
        "\n"
        "def safe_symbol():\n"
        "    return True\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(module)

    assert index.errors == []
    assert [symbol.name for symbol in index.symbols] == ["safe_symbol"]
    assert not marker.exists()


def test_extract_symbols_reports_invalid_utf8_without_crashing(tmp_path):
    module = tmp_path / "invalid_encoding.py"
    module.write_bytes(b"def ok():\n    return '\xff'\n")

    index = extract_symbols_from_file(module)

    assert index.file_path == str(module)
    assert index.symbols == []
    assert len(index.errors) == 1
    assert index.errors[0].startswith("UnicodeDecodeError")


def test_build_symbol_index_handles_mixed_mini_repo(tmp_path):
    repo = tmp_path / "repo"
    package = repo / "src" / "demo"
    docs = repo / "docs"
    package.mkdir(parents=True)
    docs.mkdir(parents=True)

    valid_module = package / "valid.py"
    valid_module.write_text(
        "class Service:\n"
        "    def start(self):\n"
        "        return 'started'\n"
        "\n"
        "async def load():\n"
        "    return Service()\n",
        encoding="utf-8",
    )

    empty_module = package / "empty.py"
    empty_module.write_text("", encoding="utf-8")

    broken_module = package / "broken.py"
    broken_module.write_text(
        "class Broken(:\n"
        "    pass\n",
        encoding="utf-8",
    )

    readme = docs / "README.md"
    readme.write_text("# Demo\n", encoding="utf-8")

    missing_module = package / "missing.py"

    indexes = build_symbol_index(
        [
            readme,
            valid_module,
            broken_module,
            empty_module,
            missing_module,
        ],
        base_path=repo,
    )

    assert [index.file_path for index in indexes] == [
        "src/demo/broken.py",
        "src/demo/empty.py",
        "src/demo/missing.py",
        "src/demo/valid.py",
    ]

    by_path = {index.file_path: index for index in indexes}

    assert by_path["src/demo/broken.py"].symbols == []
    assert len(by_path["src/demo/broken.py"].errors) == 1
    assert by_path["src/demo/broken.py"].errors[0].startswith("SyntaxError")

    assert by_path["src/demo/empty.py"].symbols == []
    assert by_path["src/demo/empty.py"].errors == []

    assert by_path["src/demo/missing.py"].symbols == []
    assert len(by_path["src/demo/missing.py"].errors) == 1
    assert by_path["src/demo/missing.py"].errors[0].startswith("FileNotFoundError")

    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in by_path["src/demo/valid.py"].symbols
    ] == [
        ("class", "Service", None),
        ("method", "start", "Service"),
        ("function", "load", None),
    ]


def test_format_symbol_index_for_mixed_mini_repo_omits_empty_and_error_only_files(tmp_path):
    repo = tmp_path / "repo"
    package = repo / "src" / "demo"
    package.mkdir(parents=True)

    valid_module = package / "valid.py"
    valid_module.write_text(
        "class Service:\n"
        "    def start(self):\n"
        "        return 'started'\n",
        encoding="utf-8",
    )

    empty_module = package / "empty.py"
    empty_module.write_text("", encoding="utf-8")

    broken_module = package / "broken.py"
    broken_module.write_text(
        "def broken(:\n"
        "    pass\n",
        encoding="utf-8",
    )

    indexes = build_symbol_index(
        [broken_module, empty_module, valid_module],
        base_path=repo,
    )

    assert format_symbol_index(indexes) == (
        "src/demo/valid.py\n"
        "  class Service:1\n"
        "  method Service.start:2"
    )


def test_symbol_extraction_handles_decorated_functions_classes_and_methods(tmp_path):
    module = tmp_path / "decorated.py"
    module.write_text(
        "def decorator(value):\n"
        "    return value\n"
        "\n"
        "@decorator\n"
        "def decorated_function():\n"
        "    return True\n"
        "\n"
        "@decorator\n"
        "class DecoratedClass:\n"
        "    @decorator\n"
        "    def decorated_method(self):\n"
        "        return True\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(module)

    assert index.errors == []
    assert [
        (symbol.kind, symbol.name, symbol.parent, symbol.line_start)
        for symbol in index.symbols
    ] == [
        ("function", "decorator", None, 1),
        ("function", "decorated_function", None, 5),
        ("class", "DecoratedClass", None, 9),
        ("method", "decorated_method", "DecoratedClass", 11),
    ]


def test_build_symbol_index_skips_uppercase_non_python_suffix(tmp_path):
    python_module = tmp_path / "real.py"
    python_module.write_text(
        "def real():\n"
        "    return True\n",
        encoding="utf-8",
    )

    non_python_module = tmp_path / "not_python.PY"
    non_python_module.write_text(
        "def ignored():\n"
        "    return False\n",
        encoding="utf-8",
    )

    indexes = build_symbol_index([non_python_module, python_module])

    assert [index.file_path for index in indexes] == [str(python_module)]
    assert [symbol.name for symbol in indexes[0].symbols] == ["real"]


def test_full_symbol_quality_regression_with_duplicate_names_and_errors(tmp_path):
    repo = tmp_path / "repo"
    package = repo / "pkg"
    package.mkdir(parents=True)

    first = package / "first.py"
    first.write_text(
        "class Worker:\n"
        "    def run(self):\n"
        "        return 'first'\n"
        "\n"
        "def main():\n"
        "    return Worker()\n",
        encoding="utf-8",
    )

    second = package / "second.py"
    second.write_text(
        "class Worker:\n"
        "    async def run(self):\n"
        "        return 'second'\n"
        "\n"
        "def main():\n"
        "    return Worker()\n",
        encoding="utf-8",
    )

    broken = package / "broken.py"
    broken.write_text(
        "async def nope(:\n"
        "    pass\n",
        encoding="utf-8",
    )

    indexes = build_symbol_index([second, broken, first], base_path=repo)

    assert [index.file_path for index in indexes] == [
        "pkg/broken.py",
        "pkg/first.py",
        "pkg/second.py",
    ]

    assert indexes[0].symbols == []
    assert len(indexes[0].errors) == 1

    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in indexes[1].symbols
    ] == [
        ("class", "Worker", None),
        ("method", "run", "Worker"),
        ("function", "main", None),
    ]

    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in indexes[2].symbols
    ] == [
        ("class", "Worker", None),
        ("method", "run", "Worker"),
        ("function", "main", None),
    ]

    assert format_symbol_index(indexes) == (
        "pkg/first.py\n"
        "  class Worker:1\n"
        "  method Worker.run:2\n"
        "  function main:5\n"
        "pkg/second.py\n"
        "  class Worker:1\n"
        "  method Worker.run:2\n"
        "  function main:5"
    )
