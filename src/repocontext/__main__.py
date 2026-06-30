"""Run the old repocontext module name as a legacy alias."""

from repodossier.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
