# RepoDossier development aliases

RepoDossier does not require machine-specific shell aliases, but the repository ships a small installer for local development convenience.

## Install

From the repository root:

    scripts/dev/install_aliases.sh

Then reload your shell rc file as printed by the installer, for example:

    source ~/.bashrc

## Installed aliases

    rdrepo

Change into the current RepoDossier clone.

    c

Run the download patch runner:

    bash "$REPODOSSIER_REPO/scripts/dev/run_latest_download_patch.sh"

    r

Run the export runner:

    bash "$REPODOSSIER_REPO/scripts/dev/r.sh"

## Dry-run

To preview the managed shell block without editing a shell rc file:

    scripts/dev/install_aliases.sh --dry-run

## Custom rc file

    scripts/dev/install_aliases.sh --rc-file /tmp/repodossier-aliases.rc

## Public repository note

The installer writes local paths only into the user's shell rc file. The repository itself must not store a contributor-specific home path, user name, email address, or workstation name.


## Export runner defaults

By default, `r` runs `full ai`.

Additional modes can be selected explicitly:

    r docs
    r changed
    r full ai docs


## Patch rules copy

The export runner copies `patch-rules.md` from its own installed script directory when the target Git repository does not contain RepoDossier development rules.


## Export runner mode aliases

The export runner also supports mode aliases for convenience:

    quick  -> ai
    doc    -> docs
    changes -> changed

Use `r --list-modes` to print canonical modes.


## Dry-run command preview

`r --dry-run` prints the concrete RepoDossier commands without writing export files.
The `all` mode expands to `full ai docs changed`.
