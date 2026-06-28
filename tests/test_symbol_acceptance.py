"""Acceptance tests for Milestone 5 symbol extraction."""

from pathlib import Path
import tomllib

from repocontext.symbols import (
    build_symbol_index,
    extract_symbols_from_file,
    format_symbol_index,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "repocontext"


def _package_source_files():
    return sorted(PACKAGE_ROOT.rglob("*.py"))


def test_milestone_5_acceptance_function_discovery(tmp_path):
    module = tmp_path / "functions.py"
    module.write_text(
        "def sync_function():\n"
        "    return 1\n"
        "\n"
        "async def async_function():\n"
        "    return 2\n"
        "\n"
        "def outer():\n"
        "    def inner():\n"
        "        return 3\n"
        "    return inner()\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(module)

    assert index.errors == []
    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in index.symbols
    ] == [
        ("function", "sync_function", None),
        ("function", "async_function", None),
        ("function", "outer", None),
    ]


def test_milestone_5_acceptance_class_discovery(tmp_path):
    module = tmp_path / "classes.py"
    module.write_text(
        "class Base:\n"
        "    pass\n"
        "\n"
        "class Child(Base):\n"
        "    pass\n"
        "\n"
        "class WithMeta(Base, metaclass=type):\n"
        "    pass\n"
        "\n"
        "class Outer:\n"
        "    class Inner:\n"
        "        pass\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(module)

    assert index.errors == []
    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in index.symbols
    ] == [
        ("class", "Base", None),
        ("class", "Child", None),
        ("class", "WithMeta", None),
        ("class", "Outer", None),
    ]


def test_milestone_5_acceptance_method_discovery(tmp_path):
    module = tmp_path / "methods.py"
    module.write_text(
        "class Service:\n"
        "    def __init__(self):\n"
        "        self.ready = True\n"
        "\n"
        "    def start(self):\n"
        "        return 'started'\n"
        "\n"
        "    async def stop(self):\n"
        "        return 'stopped'\n"
        "\n"
        "def top_level():\n"
        "    return Service()\n",
        encoding="utf-8",
    )

    index = extract_symbols_from_file(module)

    assert index.errors == []
    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in index.symbols
    ] == [
        ("class", "Service", None),
        ("method", "__init__", "Service"),
        ("method", "start", "Service"),
        ("method", "stop", "Service"),
        ("function", "top_level", None),
    ]


def test_milestone_5_acceptance_repository_symbol_index(tmp_path):
    repo = tmp_path / "repo"
    package = repo / "src" / "demo"
    docs = repo / "docs"
    package.mkdir(parents=True)
    docs.mkdir(parents=True)

    app_module = package / "app.py"
    app_module.write_text(
        "class App:\n"
        "    def run(self):\n"
        "        return True\n"
        "\n"
        "def main():\n"
        "    return App().run()\n",
        encoding="utf-8",
    )

    worker_module = package / "worker.py"
    worker_module.write_text(
        "async def work():\n"
        "    return 'done'\n",
        encoding="utf-8",
    )

    broken_module = package / "broken.py"
    broken_module.write_text(
        "def broken(:\n"
        "    pass\n",
        encoding="utf-8",
    )

    readme = docs / "README.md"
    readme.write_text("# ignored\n", encoding="utf-8")

    indexes = build_symbol_index(
        [readme, worker_module, broken_module, app_module],
        base_path=repo,
    )

    assert [index.file_path for index in indexes] == [
        "src/demo/app.py",
        "src/demo/broken.py",
        "src/demo/worker.py",
    ]

    by_path = {index.file_path: index for index in indexes}

    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in by_path["src/demo/app.py"].symbols
    ] == [
        ("class", "App", None),
        ("method", "run", "App"),
        ("function", "main", None),
    ]

    assert by_path["src/demo/broken.py"].symbols == []
    assert len(by_path["src/demo/broken.py"].errors) == 1
    assert by_path["src/demo/broken.py"].errors[0].startswith("SyntaxError")

    assert [
        (symbol.kind, symbol.name, symbol.parent)
        for symbol in by_path["src/demo/worker.py"].symbols
    ] == [
        ("function", "work", None),
    ]


def test_milestone_5_acceptance_formatting_for_future_ai_export(tmp_path):
    repo = tmp_path / "repo"
    package = repo / "src" / "demo"
    package.mkdir(parents=True)

    module = package / "app.py"
    module.write_text(
        "class App:\n"
        "    def run(self):\n"
        "        return True\n"
        "\n"
        "def main():\n"
        "    return App().run()\n",
        encoding="utf-8",
    )

    empty_module = package / "empty.py"
    empty_module.write_text("", encoding="utf-8")

    indexes = build_symbol_index([empty_module, module], base_path=repo)

    assert format_symbol_index(indexes) == (
        "src/demo/app.py\n"
        "  class App:1\n"
        "  method App.run:2\n"
        "  function main:5"
    )


def test_milestone_5_acceptance_no_symbol_export_file_is_added():
    offenders = []

    for path in _package_source_files():
        text = path.read_text(encoding="utf-8")
        if "symbols.txt" in text:
            offenders.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert offenders == []


def test_milestone_5_acceptance_no_symbol_cli_entrypoint_is_added():
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    scripts = pyproject.get("project", {}).get("scripts", {})

    assert [
        name
        for name in scripts
        if "symbol" in name.lower()
    ] == []


def test_milestone_5_acceptance_symbol_module_is_only_wired_where_expected():
    """Milestone 7 may use the symbol index for Call Graph export integration."""

    still_forbidden_tokens = (
        "format_symbol_index(",
        "extract_symbols_from_file(",
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

    assert build_symbol_index_users == ["src/repocontext/exporters/full.py"]
