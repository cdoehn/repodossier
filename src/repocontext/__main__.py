"""Execute RepoContext as a module."""

from .cli import main


def _repocontext_export_safety_root() -> object:
    """Return the nearest Git repository root or current directory."""

    from pathlib import Path

    current = Path.cwd()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate

    return current


def _repocontext_mask_known_export_files() -> None:
    """Apply final secret masking to known generated export files."""

    from pathlib import Path

    from repocontext.secrets import mask_export_file

    root = Path(_repocontext_export_safety_root())

    targets = [
        (
            "full.txt",
            "Potential secrets were masked before full export was written.",
        ),
        (
            "ai.txt",
            "Potential secrets were masked before AI export was written.",
        ),
        (
            "docs.txt",
            "Potential secrets were masked before documentation export was written.",
        ),
        (
            "changed.txt",
            "Potential secrets masked in changed export.",
        ),
    ]

    for filename, summary in targets:
        mask_export_file(root / filename, filename, summary)

if __name__ == "__main__":
    result = main()
    _repocontext_mask_known_export_files()
    raise SystemExit(result)
