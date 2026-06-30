from pathlib import Path
import subprocess
import sys
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

SCAN_ROOTS = (
    Path("pyproject.toml"),
    Path("README.md"),
    Path(".repodossier.example.yml"),
    Path("scripts"),
    Path("src"),
    Path("tests"),
)

OLD_NAME_TOKENS = (
    "RepoContext",
    "REPOCONTEXT",
    "repo_context",
    "repo-context",
    "repocontext",
)

ALLOWED_LEGACY_NAME_PATHS = {
    "README.md",
    "pyproject.toml",
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
}


def _iter_text_files():
    seen = set()

    for scan_root in SCAN_ROOTS:
        path = PROJECT_ROOT / scan_root
        if not path.exists():
            continue

        if path.is_file():
            candidates = [path]
        else:
            candidates = [
                child
                for child in path.rglob("*")
                if child.is_file()
                and child.suffix in TEXT_SUFFIXES
                and ".venv" not in child.parts
                and "__pycache__" not in child.parts
            ]

        for candidate in candidates:
            relative = candidate.relative_to(PROJECT_ROOT).as_posix()
            if relative in seen:
                continue
            seen.add(relative)
            yield candidate


def test_repodossier_is_the_primary_project_name_and_script():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "repodossier"
    assert data["project"]["scripts"]["repodossier"] == "repodossier.cli:main"


def test_repocontext_is_only_declared_as_legacy_cli_alias():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["repocontext"] == "repodossier.cli:main"


def test_primary_package_is_repodossier_and_legacy_package_is_small():
    primary_files = {
        path.relative_to(PROJECT_ROOT / "src" / "repodossier").as_posix()
        for path in (PROJECT_ROOT / "src" / "repodossier").rglob("*.py")
    }
    legacy_files = {
        path.relative_to(PROJECT_ROOT / "src" / "repocontext").as_posix()
        for path in (PROJECT_ROOT / "src" / "repocontext").rglob("*.py")
    }

    assert primary_files
    assert legacy_files == {"__init__.py", "__main__.py", "cli.py"}


def test_repodossier_help_uses_current_branding():
    result = subprocess.run(
        [sys.executable, "-m", "repodossier", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined = result.stdout + result.stderr

    assert "RepoDossier" in combined
    assert "repodossier" in combined
    assert "RepoContext" not in combined


def test_old_project_name_tokens_are_restricted_to_known_legacy_locations():
    offenders = []

    for path in _iter_text_files():
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")

        if any(token in text for token in OLD_NAME_TOKENS):
            if relative not in ALLOWED_LEGACY_NAME_PATHS:
                offenders.append(relative)

    assert offenders == []


def test_repodossier_example_config_is_the_documented_example_config():
    example = PROJECT_ROOT / ".repodossier.example.yml"

    assert example.exists()
    assert not (PROJECT_ROOT / ".repocontext.example.yml").exists()

    text = example.read_text(encoding="utf-8")
    assert "repodossier" in text
