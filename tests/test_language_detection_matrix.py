from __future__ import annotations

from pathlib import Path

import pytest

from repodossier.scanner import detect_language


@pytest.mark.parametrize(
    ("path", "expected_language"),
    [
        ("src/app.ts", "typescript"),
        ("src/App.tsx", "tsx"),
        ("src/main.js", "javascript"),
        ("src/main.mjs", "javascript"),
        ("src/main.cjs", "javascript"),
        ("src/App.jsx", "jsx"),
        ("web/index.html", "html"),
        ("web/index.htm", "html"),
        ("web/styles.css", "css"),
        ("src/App.java", "java"),
        ("src/main.c", "c"),
        ("src/main.cpp", "cpp"),
        ("src/main.cc", "cpp"),
        ("src/main.cxx", "cpp"),
        ("include/App.hpp", "cpp"),
        ("include/App.hh", "cpp"),
        ("include/App.hxx", "cpp"),
        ("src/App.cs", "csharp"),
    ],
)
def test_new_language_extensions_are_classified_consistently(
    path: str,
    expected_language: str,
) -> None:
    assert detect_language(Path(path), "not enough content to classify") == expected_language


@pytest.mark.parametrize(
    ("content", "expected_language"),
    [
        ("#!/usr/bin/env python3\nprint('ok')\n", "python"),
        ("#!/bin/bash\necho ok\n", "bash"),
        ("#!/usr/bin/env node\nconsole.log('ok');\n", "javascript"),
    ],
)
def test_shebangs_win_for_extensionless_files(
    content: str,
    expected_language: str,
) -> None:
    assert detect_language("tool", content) == expected_language


@pytest.mark.parametrize(
    ("content", "expected_language"),
    [
        ("interface User {\n  id: string;\n}\n", "typescript"),
        ("const fs = require(\"fs\");\nfunction run() {\n  console.log(fs);\n}\nmodule.exports = { run };\n", "javascript"),
        ("<!DOCTYPE html>\n<html><body>Ok</body></html>\n", "html"),
        ("body {\n  margin: 0;\n  color: black;\n}\n", "css"),
        ("public class App {\n  public static void main(String[] args) {}\n}\n", "java"),
        ("#include <stdio.h>\nint main(void) { return 0; }\n", "c"),
        ("namespace demo {\nclass App {};\n}\n", "cpp"),
        ("using System;\nnamespace Demo { public class App {} }\n", "csharp"),
        ("[project]\nname = \"demo\"\n", "toml"),
        ("{ \"name\": \"demo\", \"version\": 1 }\n", "json"),
    ],
)
def test_content_heuristics_classify_strong_unknown_file_signals(
    content: str,
    expected_language: str,
) -> None:
    assert detect_language("unknown-file", content) == expected_language


def test_markdown_document_with_embedded_code_stays_markdown() -> None:
    fence = chr(96) * 3
    content = (
        "# Developer Notes\n\n"
        "Example code follows.\n\n"
        f"{fence}typescript\n"
        "export const value: string = 'ok';\n"
        f"{fence}\n"
    )

    assert detect_language("notes", content) == "markdown"


@pytest.mark.parametrize(
    "content",
    [
        "{ \"import\": \"not JavaScript\", \"export\": \"not JavaScript\" }\n",
        "name: string\nage: number\nactive: boolean\n",
        "Use <html> as an inline example tag in prose.\n",
    ],
)
def test_common_false_positive_shapes_stay_conservative(content: str) -> None:
    detected_language = detect_language("ambiguous", content)

    assert detected_language != "javascript"
    assert detected_language != "typescript"
    assert detected_language != "html"


def test_ambiguous_h_header_is_not_classified_by_extension_alone() -> None:
    assert detect_language("include/example.h", None) is None


@pytest.mark.parametrize(
    ("content", "expected_language"),
    [
        ("#include <stdio.h>\nstruct user { int id; };\n", "c"),
        ("namespace demo { class User {}; }\n", "cpp"),
    ],
)
def test_h_header_content_can_classify_clear_c_or_cpp_signals(
    content: str,
    expected_language: str,
) -> None:
    assert detect_language("include/example.h", content) == expected_language


def test_plain_include_guard_header_stays_unknown() -> None:
    content = "#ifndef EXAMPLE_H\n#define EXAMPLE_H\n#endif\n"

    assert detect_language("include/example.h", content) is None
