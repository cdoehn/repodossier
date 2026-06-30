"""RepoDossier CLI entry point.

Temporary compatibility wrapper while the implementation package is
migrated from repocontext to repodossier.
"""

from repocontext.cli import main as main

__all__ = ["main"]


if __name__ == "__main__":
    main()
