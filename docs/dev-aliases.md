# RepoDossier development aliases

RepoDossier does not require machine-specific shell aliases, but the repository ships a small installer for local development convenience.

## Install local aliases

See also: `docs/installation.md`.


From the RepoDossier repository root:

    scripts/dev/install_aliases.sh

Then reload the shell rc file printed by the installer, for example:

    source ~/.bashrc

Preview the managed shell block without editing a shell rc file:

    scripts/dev/install_aliases.sh --dry-run

Use a custom rc file for testing:

    scripts/dev/install_aliases.sh --rc-file /tmp/repodossier-aliases.rc

## Installed aliases

### `rdrepo`

Change into the current RepoDossier checkout.

### `c`

Run the RepoDossier Download patch runner:

    bash "$REPODOSSIER_REPO/scripts/dev/run_latest_download_patch.sh"

The `c` runner accepts downloaded patch scripts and patch ZIP archives. It validates patch metadata internally, runs syntax checks, uses PatchHarbor `lint-script` for dry-run preflight linting, writes a log file, and moves successful or failed patch archives into the matching Downloads subdirectory.

A concrete script or ZIP can be passed explicitly:

    c /tmp/example_patch.sh
    c /tmp/example_patch.zip

### `r`

Run the RepoDossier export runner:

    bash "$REPODOSSIER_REPO/scripts/dev/r.sh"

By default, `r` runs:

    full ai

Additional modes can be selected explicitly:

    r docs
    r changed
    r full ai docs

The export runner also supports mode aliases:

    quick   -> ai
    doc     -> docs
    changes -> changed

Use this to print canonical modes:

    r --list-modes

Use this to preview commands without writing export files:

    r --dry-run

## Current PatchHarbor relationship

RepoDossier keeps source-side wrappers for user workflows, while generic patch infrastructure lives in PatchHarbor.

Current active source commands:

    scripts/dev/run_latest_download_patch.sh
    scripts/dev/run_patchharbor_patch.sh
    scripts/dev/r.sh
    scripts/dev/run_repodossier_exports.sh

Current generic PatchHarbor commands used by the source workflow:

    patchharbor lint-script
    patchharbor run-script
    patchharbor audit-public
    patchharbor check-env

Removed legacy helper paths are not active commands:

    scripts/dev/validate_patch_metadata.py
    scripts/dev/lint_patch_script.py
    scripts/dev/run_latest_download_patch_patchharbor_candidate.sh

## Public repository note

The installer writes local paths only into the user's shell rc file. The repository itself must not store a contributor-specific home path, user name, email address, workstation name, or private checkout path.
