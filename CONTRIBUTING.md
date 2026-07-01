# Contributing to RepoDossier

Thank you for your interest in improving RepoDossier.

RepoDossier is a Python CLI tool that creates AI-friendly repository exports such as full.txt, ai.txt, docs.txt, and changed.txt.

## Development setup

Create and activate a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -e ".[dev]"

Run the test suite:

    python3 -m pytest --color=yes

Run a focused test file when working on one area:

    python3 -m pytest --color=yes tests/test_ai_exporter.py

## Local CLI checks

After changes, verify the CLI still works:

    repodossier --version
    repodossier --help
    repodossier full
    repodossier export-ai
    repodossier export-docs
    repodossier changed

The legacy repocontext command is kept only as a temporary compatibility alias.
New documentation, examples, and user-facing workflows should prefer repodossier.

## Generated files

Do not commit generated export files:

    full.txt
    ai.txt
    docs.txt
    changed.txt

These files are local working artifacts and are ignored by .gitignore.

## Code style

RepoDossier favors:

- deterministic output
- static analysis instead of executing project code
- explicit tests for exporter behavior
- small, focused changes
- clear documentation for user-facing behavior

When adding tests, place them in the semantically closest existing test file or create a focused new test file. Avoid appending unrelated tests to the end of a large file.

## Security and privacy

Do not include real credentials, API keys, tokens, private database contents, or personal data in issues, pull requests, fixtures, screenshots, or generated exports.

RepoDossier includes best-effort secret masking, but contributors should still review generated files manually before sharing them.

## Pull requests

A good pull request should include:

- a short explanation of the problem
- a focused implementation
- tests for changed behavior
- documentation updates when user-facing behavior changes

Before opening a pull request, run:

    python3 -m pytest --color=yes
