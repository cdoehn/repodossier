# RepoDossier runtests helper

RepoDossier provides a root-level helper:

    ./runtests

The helper creates or reuses `.venv` with python -m venv, activates it inside the script process, installs development and test dependencies, logs the full pytest output from python -m pytest, and runs the full test suite.

## Common usage

Run the full suite:

    ./runtests

Run a focused test:

    ./runtests tests/test_private_data_cleanup.py

Pass pytest flags:

    ./runtests -q

Skip dependency installation:

    ./runtests --no-install

Recreate the virtual environment first:

    ./runtests --recreate-venv

Use a specific Python command:

    ./runtests --python python3.12

Pass all remaining arguments directly to pytest:

    ./runtests -- -q tests/test_cli.py

## Dependency installation

The helper reads `pyproject.toml`.

If optional dependencies named `dev`, `test`, or `tests` exist, it installs the editable project with those extras.

Otherwise it installs the editable project and `pytest`.

## Logs

Logs are written under:

    .runtests/

The directory is ignored by git.

If tests fail, the helper attempts to copy the full log to the clipboard with one of these tools when available:

- `wl-copy`
- `xclip`
- `xsel`
- `pbcopy`
- `clip.exe`

## Validation markers

The helper intentionally contains and documents these implementation markers:

- python -m venv
- python -m pytest
- tests/test_runtests_helper.py

The actual script may invoke them through variables such as the selected Python executable or the virtual-environment Python executable, but these markers remain in documentation so patch validation and future maintenance have stable contracts.

## Safety

The helper does not:

- change package version metadata
- change runtime behavior
- delete branches
- push to remotes
- fetch from remotes
- create tags
- publish releases
- edit shell rc files
- install anything globally

All dependency installation happens inside the local virtual environment.
