# RepoDossier development aliases

RepoDossier does not require shell aliases. The repository includes an optional installer for local development convenience.

## Install local aliases

See also: `docs/installation.md`.

From the repository root:

    scripts/dev/install_aliases.sh

Reload the shell rc file printed by the installer, for example:

    source ~/.bashrc

Preview the managed shell block without editing a shell rc file:

    scripts/dev/install_aliases.sh --dry-run

## Installed aliases

### `rdrepo`

Change into the current RepoDossier checkout.

### `c`

Run the RepoDossier download patch runner:

    bash "$REPODOSSIER_REPO/scripts/dev/run_latest_download_patch.sh"

The runner accepts patch scripts and ZIP archives. It validates RepoDossier metadata and Bash syntax internally, writes a log file, and moves successful or failed patch artifacts into the matching Downloads subdirectory.

### `r`

Run the RepoDossier export runner:

    bash "$REPODOSSIER_REPO/scripts/dev/r.sh"

By default, `r` runs the `full` and `ai` exports. Additional modes are `docs` and `changed`. Use `r --list-modes` to print the canonical modes and `r --dry-run` to preview commands without writing export files.

## Public repository note

The installer writes local paths only into the user's shell rc file. The repository itself must not store contributor-specific local values.
