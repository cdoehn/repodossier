"""Legacy CLI module for the old repocontext package name.

New code should use repodossier.cli instead.
"""

from repodossier.cli import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
