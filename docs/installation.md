# RepoDossier installation

## Standard pip install

Use this when installing into the currently active Python environment:

    python3 -m pip install .
    repodossier --help
    repodossier --version

## Recommended user install: pipx

From the repository root:

    python3 -m pipx uninstall repodossier 2>/dev/null || true
    python3 -m pipx install "$PWD"
    export PATH="$HOME/.local/bin:$PATH"

Verify the supported command:

    repodossier --help
    repodossier --version

The temporary compatibility command can be checked with:

    repocontext --help
    repocontext --version

`repodossier` is the supported command name. `repocontext` exists only for compatibility.

## Reinstall from the current checkout

    python3 -m pipx uninstall repodossier 2>/dev/null || true
    python3 -m pipx install "$PWD"
    repodossier --version

## Editable development install

    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -e ".[dev]"
    python3 -m pytest --color=yes

## Optional developer aliases

    scripts/dev/install_aliases.sh

Preview without editing a shell rc file:

    scripts/dev/install_aliases.sh --dry-run

The installer defines `rdrepo`, `c`, and `r`. Details are in `docs/dev-aliases.md`.

## Archive CLI workflow

The last positional argument is the output folder. All earlier positional arguments are source folders:

    repodossier ./projekt ./output
    repodossier ./projekt/backend ./projekt/frontend ./output
    repodossier ./projekt ./output --output-name projektpaket.zip

The archive contains reports under `reports/` and committed `HEAD` snapshots under `repositories/`. Snapshot creation uses Git's native `git archive --format=zip --output=repodossier.zip HEAD` semantics. Git internals and local working-tree changes are excluded.

Additional archive examples:

    repodossier ./projekt/src/backend ./output
    repodossier ./repo-a ./repo-b ./output
    repodossier ./projekt ./output --output-name projektpaket.xml

Ubuntu 26.04 is the required functional verification platform. The implementation is also expected to work on Ubuntu 24.04.

Git internals, staged changes, unstaged changes, untracked files, ignored files, and temporary archive files are excluded from repository snapshots.
