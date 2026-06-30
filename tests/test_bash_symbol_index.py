from __future__ import annotations

import inspect
from pathlib import Path

from repodossier import symbols


EXTRACTOR_NAME = "extract_symbols_from_file"


def _call_symbol_extractor(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

    extractor = getattr(symbols, EXTRACTOR_NAME)
    signature = inspect.signature(extractor)

    args = []
    kwargs = {}
    path_sent = False
    content_sent = False

    for name, parameter in signature.parameters.items():
        lowered = name.lower()

        if name == "self":
            continue

        if (
            lowered in {"path", "file_path", "filepath", "relative_path", "absolute_path", "source_path", "filename", "name"}
            or "path" in lowered
            or "file" in lowered
        ):
            kwargs[name] = path
            path_sent = True
            continue

        if any(marker in lowered for marker in ("content", "text", "source", "data", "body")):
            kwargs[name] = content
            content_sent = True
            continue

        if parameter.default is not inspect._empty:
            continue

        if not path_sent:
            args.append(path)
            path_sent = True
        elif not content_sent:
            args.append(content)
            content_sent = True
        else:
            raise AssertionError(f"Cannot call {EXTRACTOR_NAME} with required parameter {name!r}.")

    return extractor(*args, **kwargs)


def _symbols_from_result(result: object) -> list[object]:
    if isinstance(result, list):
        return result

    for attr in ("symbols", "functions", "items", "entries", "all_symbols"):
        value = getattr(result, attr, None)
        if isinstance(value, list):
            return value

    try:
        return list(result)
    except TypeError:
        return []


def _value(symbol: object, *names: str):
    for name in names:
        if hasattr(symbol, name):
            value = getattr(symbol, name)
            if hasattr(value, "value"):
                return value.value
            if hasattr(value, "name"):
                return value.name
            return value
    return None


def test_symbol_index_includes_bash_functions_from_shell_file(tmp_path):
    script = """deploy_app() {
  echo deploy
}

rollback_app() { echo rollback; }
"""

    result = _call_symbol_extractor(tmp_path / "deploy.sh", script)
    discovered = _symbols_from_result(result)

    names = [_value(symbol, "name") for symbol in discovered]
    assert names == ["deploy_app", "rollback_app"]

    kinds = [str(_value(symbol, "kind", "type", "symbol_type", "category")).lower() for symbol in discovered]
    assert all("function" in kind for kind in kinds)

    # Line numbers are covered by tests/test_bash_symbols.py. This integration
    # test only checks that Bash functions are converted into the existing
    # symbol-index container shape without depending on a specific Symbol field
    # name for source locations.


def test_symbol_index_ignores_bash_functions_for_python_files(tmp_path):
    script = """deploy_app() {
  echo deploy
}
"""

    result = _call_symbol_extractor(tmp_path / "app.py", script)
    discovered = _symbols_from_result(result)

    assert [_value(symbol, "name") for symbol in discovered] == []
