from pathlib import Path


def test_readme_documents_content_aware_language_detection() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Language Detection" in readme
    assert "central, deterministic language detector" in readme
    assert "shebangs, known filenames, extension mapping, and conservative content heuristics" in readme
    assert "Clear shebangs win first" in readme
    assert "Known extensions and known filenames stay stable" in readme
    assert "Ambiguous files stay unknown instead of guessing" in readme


def test_readme_documents_new_language_extension_support() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    for language in [
        "TypeScript",
        "TSX",
        "JavaScript",
        "JSX",
        "HTML",
        "CSS",
        "Java",
        "C",
        "C++",
        "C#",
    ]:
        assert language in readme

    for extension in [
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".html",
        ".htm",
        ".css",
        ".java",
        ".c",
        ".cpp",
        ".cc",
        ".cxx",
        ".hpp",
        ".hh",
        ".hxx",
        ".cs",
    ]:
        assert extension in readme


def test_readme_documents_conservative_h_header_behavior() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert ".hpp, .hh, and .hxx map to C++" in readme
    assert "The ambiguous .h extension is not mapped by extension alone" in readme
    assert "content heuristics may classify it as C or C++ only when the file has a clear signal" in readme


def test_readme_documents_export_language_label_behavior() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "full.txt groups files by readable language names" in readme
    assert "full.txt source sections use language-aware Markdown code fences" in readme
    assert "changed.txt uses language-aware Markdown code fences" in readme
    assert "ai.txt and docs.txt keep their existing scope" in readme
