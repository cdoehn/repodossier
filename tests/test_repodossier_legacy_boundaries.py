from pathlib import Path
import ast
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".ini",
    ".cfg",
    ".rst",
    ".sh",
}

OLD_NAME_TOKENS = (
    "RepoContext",
    "REPOCONTEXT",
    "repo_context",
    "repo-context",
    "repocontext",
)

ALLOWED_LEGACY_TEXT_PATHS = {
    "README.md",
    "pyproject.toml",
    "scripts/validate_pipx_release.sh",
    "src/repocontext/__init__.py",
    "src/repocontext/__main__.py",
    "src/repocontext/cli.py",
    "src/repodossier/config.py",
    "tests/test_repodossier_cli_alias.py",
    "tests/test_repodossier_cli_output.py",
    "tests/test_repodossier_legacy_boundaries.py",
    "tests/test_repodossier_legacy_config.py",
    "tests/test_repodossier_naming_guard.py",
    "tests/test_repodossier_package_rename.py",
    "tests/test_repodossier_install_docs.py",
}

ALLOWED_REPOCONTEXT_IMPORT_PATHS = {
    "src/repocontext/__init__.py",
    "src/repocontext/__main__.py",
    "src/repocontext/cli.py",
    "tests/test_repodossier_package_rename.py",
}


def _iter_text_files():
    scan_roots = [
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / ".repodossier.example.yml",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "tests",
    ]

    seen = set()

    for scan_root in scan_roots:
        if not scan_root.exists():
            continue

        if scan_root.is_file():
            candidates = [scan_root]
        else:
            candidates = [
                path
                for path in scan_root.rglob("*")
                if path.is_file()
                and path.suffix in TEXT_SUFFIXES
                and ".venv" not in path.parts
                and "__pycache__" not in path.parts
                and not any(part.endswith(".egg-info") for part in path.parts)
            ]

        for candidate in candidates:
            relative = candidate.relative_to(PROJECT_ROOT).as_posix()
            if relative in seen:
                continue
            seen.add(relative)
            yield candidate



def test_setuptools_package_discovery_includes_current_and_legacy_packages():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    include = data["tool"]["setuptools"]["packages"]["find"]["include"]

    assert include == ["repodossier*", "repocontext*"]


def test_setuptools_package_discovery_include_patterns_are_unique():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    include = data["tool"]["setuptools"]["packages"]["find"]["include"]

    assert len(include) == len(set(include))


def test_readme_documents_legacy_cli_alias_for_pipx_verification():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "repocontext --help" in readme
    assert "repocontext --version" in readme
    assert "`repodossier` is the current command." in readme
    assert "`repocontext` is kept as a temporary legacy compatibility alias." in readme

def test_old_name_tokens_only_appear_in_legacy_boundary_files():
    offenders = []

    for path in _iter_text_files():
        relative = path.relative_to(PROJECT_ROOT).as_posix()

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if any(token in text for token in OLD_NAME_TOKENS):
            if relative not in ALLOWED_LEGACY_TEXT_PATHS:
                offenders.append(relative)

    assert offenders == []


def test_productive_source_code_does_not_import_repocontext():
    offenders = []

    for path in (PROJECT_ROOT / "src").rglob("*.py"):
        relative = path.relative_to(PROJECT_ROOT).as_posix()

        if relative in ALLOWED_REPOCONTEXT_IMPORT_PATHS:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "repocontext" or alias.name.startswith("repocontext."):
                        offenders.append(f"{relative}: import {alias.name}")

            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "repocontext" or module.startswith("repocontext."):
                    offenders.append(f"{relative}: from {module} import ...")

    assert offenders == []


def test_packaging_keeps_current_package_primary_and_legacy_alias_explicit():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "repodossier"
    assert data["project"]["scripts"]["repodossier"] == "repodossier.cli:main"
    assert data["project"]["scripts"]["repocontext"] == "repodossier.cli:main"


def test_legacy_package_stays_tiny():
    legacy_files = {
        path.relative_to(PROJECT_ROOT / "src" / "repocontext").as_posix()
        for path in (PROJECT_ROOT / "src" / "repocontext").rglob("*.py")
    }

    assert legacy_files == {"__init__.py", "__main__.py", "cli.py"}
