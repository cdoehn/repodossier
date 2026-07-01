"""Regression tests for RepoDossier's central language detection API."""

from __future__ import annotations

from pathlib import Path

import pytest

from repodossier.scanner import (
    detect_language,
    detect_language_from_extension,
    detect_language_from_filename,
    detect_language_from_shebang,
    scan_single_file,
)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("src/example.py", "python"),
        ("scripts/deploy.sh", "bash"),
        ("scripts/deploy.bash", "bash"),
        ("README.md", "markdown"),
        ("notes.txt", "text"),
        ("package.json", "json"),
        ("config.yaml", "yaml"),
        ("config.yml", "yaml"),
        ("pyproject.toml", "toml"),
        ("tox.ini", "ini"),
        ("setup.cfg", "ini"),
    ],
)
def test_detect_language_preserves_existing_extension_labels(
    path: str,
    expected: str,
) -> None:
    assert detect_language(path) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("README", "markdown"),
        ("readme", "markdown"),
        ("LICENSE", "text"),
        ("LICENCE", "text"),
        ("COPYING", "text"),
        ("CHANGELOG", "markdown"),
        ("TODO", "text"),
        ("Makefile", "makefile"),
        ("Dockerfile", "dockerfile"),
    ],
)
def test_detect_language_preserves_existing_extensionless_filename_labels(
    path: str,
    expected: str,
) -> None:
    assert detect_language(path) == expected


def test_detect_language_keeps_unknown_extension_conservative() -> None:
    assert detect_language("archive.zip") is None
    assert detect_language("data.unknown") is None


def test_detect_language_keeps_unknown_extensionless_text_conservative() -> None:
    assert detect_language(Path("notes/overview"), "plain text without strong signals") is None


def test_detect_language_uses_content_sample_for_existing_bash_shebang() -> None:
    assert detect_language("deploy", "#!/usr/bin/env bash\nset -euo pipefail\n") == "bash"
    assert detect_language("run", "#!/bin/sh\necho hello\n") == "bash"


def test_scan_single_file_uses_central_language_detection_for_bash_shebang(
    tmp_path: Path,
) -> None:
    script = tmp_path / "deploy"
    script.write_text("#!/usr/bin/env bash\nset -e\necho deploy\n", encoding="utf-8")

    info = scan_single_file(tmp_path, script.relative_to(tmp_path))

    assert info.is_text is True
    assert info.is_binary is False
    assert info.language == "bash"


def test_compatibility_language_helpers_remain_available() -> None:
    assert detect_language_from_extension("script.py") == "python"
    assert detect_language_from_extension("notes.txt") == "text"
    assert detect_language_from_extension("archive.zip") is None

    assert detect_language_from_filename("README") == "markdown"
    assert detect_language_from_filename("LICENSE") == "text"
    assert detect_language_from_filename("README.md") is None


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("#!/usr/bin/env python\nprint('ok')\n", "python"),
        ("#!/usr/bin/env python3\nprint('ok')\n", "python"),
        ("#!/usr/bin/python\nprint('ok')\n", "python"),
        ("#!/usr/bin/python3\nprint('ok')\n", "python"),
        ("#!/usr/bin/env python3.12\nprint('ok')\n", "python"),
        ("#!/usr/bin/env bash\necho ok\n", "bash"),
        ("#!/bin/bash\necho ok\n", "bash"),
        ("#!/usr/bin/bash\necho ok\n", "bash"),
        ("#!/bin/sh\necho ok\n", "bash"),
        ("#!/usr/bin/env sh\necho ok\n", "bash"),
        ("#!/usr/bin/env node\nconsole.log('ok')\n", "javascript"),
        ("#!/usr/bin/node\nconsole.log('ok')\n", "javascript"),
    ],
)
def test_detect_language_from_shebang_recognizes_supported_interpreters(
    content: str,
    expected: str,
) -> None:
    assert detect_language_from_shebang(content) == expected


def test_detect_language_from_shebang_accepts_bytes() -> None:
    assert detect_language_from_shebang(b"#!/usr/bin/env python3\nprint('ok')\n") == "python"


@pytest.mark.parametrize(
    "content",
    [
        "",
        "print('ok')\n",
        " #!/usr/bin/env python3\nprint('ok')\n",
        "#!/usr/bin/env ruby\nputs 'ok'\n",
        "#!/usr/bin/env\n",
    ],
)
def test_detect_language_from_shebang_stays_conservative_for_unknown_or_invalid_shebangs(
    content: str,
) -> None:
    assert detect_language_from_shebang(content) is None


@pytest.mark.parametrize(
    ("path", "content", "expected"),
    [
        ("bin/tool", "#!/usr/bin/env python3\nprint('ok')\n", "python"),
        ("bin/deploy", "#!/bin/bash\necho ok\n", "bash"),
        ("bin/cli", "#!/usr/bin/env node\nconsole.log('ok')\n", "javascript"),
        ("notes.txt", "#!/usr/bin/env python3\nprint('ok')\n", "python"),
        ("script.sh", "#!/usr/bin/env python3\nprint('ok')\n", "python"),
    ],
)
def test_detect_language_prioritizes_clear_shebang_over_filename_or_extension(
    path: str,
    content: str,
    expected: str,
) -> None:
    assert detect_language(path, content) == expected


@pytest.mark.parametrize(
    ("filename", "content", "expected"),
    [
        ("tool", "#!/usr/bin/env python3\nprint('ok')\n", "python"),
        ("deploy", "#!/usr/bin/env bash\necho ok\n", "bash"),
        ("cli", "#!/usr/bin/env node\nconsole.log('ok')\n", "javascript"),
    ],
)
def test_scan_single_file_uses_central_language_detection_for_supported_shebangs(
    tmp_path: Path,
    filename: str,
    content: str,
    expected: str,
) -> None:
    script = tmp_path / filename
    script.write_text(content, encoding="utf-8")

    info = scan_single_file(tmp_path, script.relative_to(tmp_path))

    assert info.is_text is True
    assert info.is_binary is False
    assert info.language == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("src/app.ts", "typescript"),
        ("src/App.tsx", "tsx"),
        ("src/main.js", "javascript"),
        ("src/Component.jsx", "jsx"),
        ("src/module.mjs", "javascript"),
        ("src/common.cjs", "javascript"),
        ("web/index.html", "html"),
        ("web/index.htm", "html"),
        ("web/styles.css", "css"),
        ("src/App.java", "java"),
        ("src/main.c", "c"),
        ("src/main.cpp", "cpp"),
        ("src/main.cc", "cpp"),
        ("src/main.cxx", "cpp"),
        ("include/app.hpp", "cpp"),
        ("include/app.hh", "cpp"),
        ("include/app.hxx", "cpp"),
        ("src/App.cs", "csharp"),
    ],
)
def test_detect_language_recognizes_new_language_extensions(
    path: str,
    expected: str,
) -> None:
    assert detect_language(path) == expected
    assert detect_language_from_extension(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        "include/ambiguous.h",
        "src/header.h",
    ],
)
def test_detect_language_keeps_plain_h_headers_conservative_until_content_heuristics(
    path: str,
) -> None:
    assert detect_language(path) is None
    assert detect_language_from_extension(path) is None


@pytest.mark.parametrize(
    ("path", "content", "expected"),
    [
        ("src/app.ts", "const value: string = 'ok';\n", "typescript"),
        ("src/App.tsx", "export const App = () => <main />;\n", "tsx"),
        ("src/main.js", "console.log('ok');\n", "javascript"),
        ("src/Component.jsx", "export const Component = () => <div />;\n", "jsx"),
        ("web/index.html", "<!DOCTYPE html>\n<html></html>\n", "html"),
        ("web/styles.css", "body { margin: 0; }\n", "css"),
        ("src/App.java", "public class App {}\n", "java"),
        ("src/main.c", "int main(void) { return 0; }\n", "c"),
        ("src/main.cpp", "#include <iostream>\nint main() { return 0; }\n", "cpp"),
        ("src/App.cs", "namespace Demo { public class App {} }\n", "csharp"),
    ],
)
def test_scan_single_file_recognizes_new_language_extensions(
    tmp_path: Path,
    path: str,
    content: str,
    expected: str,
) -> None:
    source_file = tmp_path / path
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text(content, encoding="utf-8")

    info = scan_single_file(tmp_path, source_file.relative_to(tmp_path))

    assert info.is_text is True
    assert info.is_binary is False
    assert info.language == expected

