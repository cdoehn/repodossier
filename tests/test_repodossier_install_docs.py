from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
INSTALL_DOC = ROOT / "docs" / "installation.md"
ALIASES_DOC = ROOT / "docs" / "dev-aliases.md"
WORKFLOW_DOC = ROOT / "planning" / "patchharbor" / "repodossier-developer-workflow.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def readme_install_section() -> str:
    readme = read(README)
    return readme.split("## Installation", 1)[1].split("## Secret Detection", 1)[0]


def test_readme_installation_section_points_to_current_install_doc() -> None:
    section = readme_install_section()

    required = [
        "docs/installation.md",
        "Install the CLI with pipx from a local checkout",
        "python3 -m pipx uninstall repodossier 2>/dev/null || true",
        'python3 -m pipx install "$PWD"',
        'export PATH="$HOME/.local/bin:$PATH"',
        "repodossier --help",
        "repodossier --version",
        "repocontext --help",
        "repocontext --version",
        "Editable development install",
        'python3 -m pip install -e ".[dev]"',
        "Optional developer aliases",
        "scripts/dev/install_aliases.sh",
        "docs/dev-aliases.md",
    ]
    missing = [marker for marker in required if marker not in section]
    assert not missing, missing


def test_installation_doc_separates_user_install_development_install_and_aliases() -> None:
    text = read(INSTALL_DOC)

    required = [
        "# RepoDossier installation",
        "Recommended user install: pipx",
        "Reinstall from the current checkout",
        "Editable development install",
        "Optional developer aliases",
        "PatchHarbor during development",
        "python3 -m pipx uninstall repodossier 2>/dev/null || true",
        'python3 -m pipx install "$PWD"',
        'python3 -m pip install -e ".[dev]"',
        "scripts/dev/install_aliases.sh --dry-run",
        "patchharbor lint-script",
        "PATCHHARBOR.14c3",
    ]
    missing = [marker for marker in required if marker not in text]
    assert not missing, missing


def test_install_docs_do_not_recommend_old_pipx_editable_patterns() -> None:
    combined = "\n".join(read(path) for path in [README, INSTALL_DOC])

    forbidden = [
        "pipx install -e .",
        "python3 -m pipx install -e .",
        "\npipx install .\n",
    ]
    for marker in forbidden:
        assert marker not in combined


def test_alias_and_workflow_docs_reference_installation_doc_after_14c2() -> None:
    aliases = read(ALIASES_DOC)
    workflow = read(WORKFLOW_DOC)

    assert "See also: `docs/installation.md`." in aliases
    assert "PATCHHARBOR.14c2 applied" in workflow
    assert "README.md` and `docs/installation.md`" in workflow
    assert "pipx` user install" in workflow
    assert "editable development install" in workflow


def test_install_docs_keep_removed_legacy_helpers_out_of_install_instructions() -> None:
    combined = "\n".join(read(path) for path in [README, INSTALL_DOC])

    removed = [
        "scripts/dev/validate_patch_metadata.py",
        "scripts/dev/lint_patch_script.py",
        "scripts/dev/run_latest_download_patch_patchharbor_candidate.sh",
    ]
    for marker in removed:
        assert marker not in combined


def test_install_docs_do_not_introduce_private_local_values_or_fences() -> None:
    checked = [INSTALL_DOC, Path(__file__).resolve()]
    install_text = "\n".join(read(path) for path in checked)
    readme_section = readme_install_section()

    private_forbidden = [
        "/home/" + "exampleuser",
        "user" + "@",
        "example.user" + "@" + "example.invalid",
        "Example" + "Laptop",
        "Example" + "Machine",
        "~/" + "Projects",
    ]

    for value in private_forbidden:
        assert value not in install_text
        assert value not in readme_section

    assert chr(96) * 3 not in install_text
    assert chr(96) * 3 not in readme_section
