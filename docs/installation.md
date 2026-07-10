# RepoDossier installation

This document describes current RepoDossier installation paths after PATCHHARBOR.14c2.

## Recommended user install: pipx

Use `pipx` when you want the command-line application available on your normal shell path.

From the repository root:

    python3 -m pipx uninstall repodossier 2>/dev/null || true
    python3 -m pipx install "$PWD"
    export PATH="$HOME/.local/bin:$PATH"

Verify the current command:

    repodossier --help
    repodossier --version

Verify the temporary legacy compatibility command while it still exists:

    repocontext --help
    repocontext --version

`repodossier` is the supported command name.

`repocontext` is a temporary compatibility command and should not be used in new documentation or scripts except when compatibility is being tested.

## Reinstall from the current checkout

Use this when the local checkout changed and the installed command should reflect the current repository state:

    python3 -m pipx uninstall repodossier 2>/dev/null || true
    python3 -m pipx install "$PWD"
    repodossier --version

This reinstall flow intentionally uses the current checkout through `$PWD`.

## Editable development install

Use an editable virtual environment for development, tests, and local source changes:

    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -e ".[dev]"
    python3 -m pytest --color=yes

Editable development installs are separate from the pipx user install.

Do not document editable pipx installation mode as the normal install path.

## Optional developer aliases

Local developer aliases are optional. They are installed by:

    scripts/dev/install_aliases.sh

Preview without editing a shell rc file:

    scripts/dev/install_aliases.sh --dry-run

The installer writes a managed shell block into the selected shell rc file.

It defines:

| Alias | Purpose |
| --- | --- |
| `rdrepo` | change into the RepoDossier checkout |
| `c` | run the RepoDossier Download patch runner |
| `r` | run RepoDossier exports |
| `patchharbor-patch` | run the source-side PatchHarbor wrapper |

The alias details live in `docs/dev-aliases.md`.

## PatchHarbor during development

Normal RepoDossier CLI installation does not require installing PatchHarbor.

RepoDossier development workflows may use PatchHarbor for generic patch infrastructure:

    patchharbor lint-script
    patchharbor run-script
    patchharbor audit-public
    patchharbor check-env

When a sibling PatchHarbor checkout is used for development, the source-side `c` runner can discover it through `PATCHHARBOR_REPO` or the sibling `patch-harbor` directory.

## What this installation document does not change

PATCHHARBOR.14c2 does not:

- change `c`
- change `r`
- change aliases
- change package metadata
- change PatchHarbor target files
- remove compatibility commands
- change export behavior

Migration-note cleanup is handled by PATCHHARBOR.14c3.
