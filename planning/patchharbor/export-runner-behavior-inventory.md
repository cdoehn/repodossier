# PATCHHARBOR.11a2 – Export Runner Behavior Inventory

This document records the current RepoDossier export runner behavior before any export-runner migration begins.

PATCHHARBOR.11 must preserve the productive `r` workflow. This document describes behavior only; it does not propose a replacement implementation.

## Entry-point flow

Current user-facing flow:

    r
    scripts/dev/r.sh
    scripts/dev/run_repodossier_exports.sh

The wrapper is intentionally thin. The behavior contract is currently implemented in `scripts/dev/run_repodossier_exports.sh`.

## Argument handling

The runner accepts these control flags:

| Flag | Behavior |
| --- | --- |
| `--help` / `-h` | print usage and exit with code `0` |
| `--list-modes` | print supported mode names and exit with code `0` |
| `--dry-run` | print planned commands without creating export artifacts |

Unknown modes are rejected with an `r error` line and exit code `2`.

## Mode normalization

The current mode normalizer maps user input to canonical modes:

| Input | Canonical mode |
| --- | --- |
| `full` | `full` |
| `ai` | `ai` |
| `quick` | `ai` |
| `export-ai` | `ai` |
| `docs` | `docs` |
| `doc` | `docs` |
| `changed` | `changed` |
| `changes` | `changed` |
| `all` | `full ai docs changed` |

Default mode behavior:

- normal run with no mode arguments: `full ai`
- dry-run with no mode arguments: `full ai docs changed`

## Repository and environment setup

The runner resolves the Git repository root with `git rev-parse --show-toplevel` and then changes into that root before running export commands.

The runner reads these environment variables:

| Variable | Behavior |
| --- | --- |
| `REPODOSSIER_BIN` | executable used for RepoDossier commands; default is `repodossier` |
| `PATCH_DOWNLOAD_DIR` | output directory for copied artifacts; default is `$HOME/Downloads` |

The runner checks that `REPODOSSIER_BIN` is available with `command -v` before any mode runs.

## Per-mode command behavior

| Canonical mode | Dry-run output command | Non-dry-run command | Copied artifact |
| --- | --- | --- | --- |
| `full` | `repodossier full` | `repodossier full` | `full.txt` |
| `ai` | `repodossier export-ai` | `repodossier export-ai` | `ai.txt` |
| `docs` | `repodossier export-docs` | `repodossier export-docs` | `docs.txt` |
| `changed` | `repodossier changed` | `repodossier changed` | `changed.txt` |

Dry-run mode logs planned commands and does not copy artifacts.

Non-dry-run mode executes each requested command, checks the exit code, and copies the matching generated artifact only when the artifact exists.

## Patch rules copy behavior

After successful non-dry-run mode execution, the runner attempts to copy `patch-rules.md` to the download directory.

Lookup order:

1. `scripts/dev/patch-rules.md` relative to repository root
2. `patch-rules.md` next to the export runner script

If no file exists, the copy step is skipped without failing.

## Output behavior

Compatibility-sensitive output includes:

- header text `r · RepoDossier Export Runner`
- `Repo:` line
- `Downloads:` line
- `Modi:` line
- per-mode `Exportiere ...` lines
- dry-run `Befehl: ...` lines
- copy `Kopiert:` lines
- dry-run `Dry-run: keine Dateien geschrieben.` line
- final `r abgeschlossen.` line

Output color codes are not semantic, but marker words and phase order are compatibility-sensitive.

## Failure behavior

The runner exits non-zero in these cases:

| Failure | Expected behavior |
| --- | --- |
| not in a Git repository | `r error` and exit code `1` |
| `REPODOSSIER_BIN` not found | `r error` and exit code `1` |
| unknown mode | `r error`, usage output, and exit code `2` |
| export command fails | `r error` and the export command exit code |

A migration patch must not silently weaken these failures.

## Source-specific behavior

These details are RepoDossier-specific and should not be blindly moved into generic PatchHarbor target code:

- exact `repodossier` subcommands
- exact artifact names `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt`
- `REPODOSSIER_BIN` environment variable name
- default normal and dry-run mode lists
- `patch-rules.md` copy behavior
- German output markers used by `r`

## Explicit non-goals for 11a2

PATCHHARBOR.11a2 does not:

- change `scripts/dev/r.sh`
- change `scripts/dev/run_repodossier_exports.sh`
- add target-side PatchHarbor export APIs
- add source-side wrapper candidates
- change export commands
- change output markers
- change alias installation
- switch `r`

## Next step

PATCHHARBOR.11a3 should add tests that pin this behavior inventory before target-side export models are introduced.
