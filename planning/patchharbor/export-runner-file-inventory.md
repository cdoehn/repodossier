# PATCHHARBOR.11a1 – Export Runner File Inventory

This document records the current RepoDossier export runner files before any export-runner migration begins.

PATCHHARBOR.11 must keep the productive `r` workflow stable while separating generic export-runner pieces from RepoDossier-specific export defaults.

## Current source-side entry points

| Area | Path | Current role |
| --- | --- | --- |
| user-facing wrapper | `scripts/dev/r.sh` | small Bash wrapper that executes the RepoDossier export runner |
| productive export runner | `scripts/dev/run_repodossier_exports.sh` | current implementation of the `r` workflow |
| patch rules copied by exports | `scripts/dev/patch-rules.md` | copied to Downloads after non-dry-run exports when present |
| alias installer | `scripts/dev/install_aliases.sh` | installs shell aliases for local development helpers |

## Current generated export artifacts

The current export runner copies these repository-root artifacts to the download directory when the matching mode is run successfully:

| Mode | RepoDossier command | Source artifact | Download artifact |
| --- | --- | --- | --- |
| `full` | `repodossier full` | `full.txt` | `full.txt` |
| `ai` | `repodossier export-ai` | `ai.txt` | `ai.txt` |
| `docs` | `repodossier export-docs` | `docs.txt` | `docs.txt` |
| `changed` | `repodossier changed` | `changed.txt` | `changed.txt` |

## Current mode contract

The current runner supports these mode names and aliases:

| User input | Normalized mode |
| --- | --- |
| `all` | `full ai docs changed` |
| `full` | `full` |
| `ai` | `ai` |
| `quick` | `ai` |
| `export-ai` | `ai` |
| `docs` | `docs` |
| `doc` | `docs` |
| `changed` | `changed` |
| `changes` | `changed` |

Default behavior:

- normal run default: `full ai`
- dry-run default: `full ai docs changed`
- `--list-modes` prints the available modes and exits
- `--help` prints usage and exits

## Current environment contract

| Variable | Meaning |
| --- | --- |
| `REPODOSSIER_BIN` | RepoDossier executable, default `repodossier` |
| `PATCH_DOWNLOAD_DIR` | download directory, default `$HOME/Downloads` |

## Current output contract

The current export runner prints a compact `r · RepoDossier Export Runner` header and structured `r info`, `r do`, `r ok`, and `r error` lines.

Compatibility-sensitive output includes:

- `Repo:` line
- `Downloads:` line
- `Modi:` line
- per-mode `Exportiere ...` lines
- dry-run `Befehl: ...` lines
- `Kopiert:` lines
- final `r abgeschlossen.` line

## Current failure contract

The current runner exits non-zero when:

- it is not executed inside a Git repository
- `REPODOSSIER_BIN` is not available
- an unknown mode is supplied
- an invoked RepoDossier command exits non-zero

No export migration patch may weaken those failures silently.

## RepoDossier-specific parts

These parts are source-repository specific and should not be blindly moved into generic PatchHarbor target code:

- exact RepoDossier CLI commands
- exact generated artifact names
- `patch-rules.md` copy behavior
- default normal mode list
- default dry-run mode list
- `REPODOSSIER_BIN` variable name

## Candidate generic parts

These parts may be candidates for generic PatchHarbor modeling later:

- export job model
- export plan model
- command execution result model
- copy-if-exists artifact lifecycle
- dry-run planning display
- mode alias normalization shape
- structured terminal line helpers

## Explicit non-goals for 11a1

PATCHHARBOR.11a1 does not:

- change `scripts/dev/r.sh`
- change `scripts/dev/run_repodossier_exports.sh`
- change aliases
- change export modes
- change RepoDossier CLI commands
- add PatchHarbor target export code
- remove source-side export logic
- switch `r`

## Next step

PATCHHARBOR.11a2 should document the current export runner behavior in more detail before any target-side export model is added.
