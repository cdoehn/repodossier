# PATCHHARBOR.10a1 – Download Runner File Inventory

This inventory records the source-side files that currently implement and support the RepoDossier `c` download patch runner.

This document is descriptive only. It does not change runner behavior.

## Primary runner

| File | Current role |
| --- | --- |
| `scripts/dev/run_latest_download_patch.sh` | Main `c` runner. Selects or receives patch scripts, validates metadata, checks repeat/freshness/syntax/lint, executes scripts, logs output, moves successful or failed inputs, and prints terminal status. |

## Runner validation helpers

| File | Current role |
| --- | --- |
| `scripts/dev/validate_patch_metadata.py` | Validates `repodossier-meta` records before patch execution. |
| `scripts/dev/lint_patch_script.py` | Performs patch preflight/lint checks before execution. |
| `scripts/dev/show_progress_context.py` | Renders roadmap and milestone context when enabled. |
| `scripts/dev/patch-rules.md` | Documents patch rules used by the lint/preflight workflow if present. |

## Source adoption and alias files

| File | Current role |
| --- | --- |
| `scripts/dev/install_aliases.sh` | Installs developer aliases such as `rdrepo`, `c`, `r`, and `patchharbor-patch`. |
| `scripts/dev/run_patchharbor_patch.sh` | Thin explicit wrapper for running a selected patch through PatchHarbor. |
| `scripts/dev/r.sh` | Existing export wrapper. It is not part of the download runner migration. |
| `scripts/dev/run_repodossier_exports.sh` | Existing export runner. It is not part of the download runner migration. |

## Download workflow locations

The current runner uses a download workflow with these logical locations:

| Location | Meaning |
| --- | --- |
| download directory | Input directory for `.sh` and `.zip` patch files. |
| done directory | Destination for successfully applied patch inputs. |
| failed directory | Destination for failed patch inputs. |
| run log | Log file kept in the download directory. |
| applied ledger | Ledger used to avoid accidentally reapplying the same patch input. |
| temporary zip extraction directory | Temporary directory used when the selected input is a `.zip` archive. |

The actual absolute paths are runtime-local and must not be stored in tracked files.

## Accepted input forms

The current runner accepts:

- a direct `.sh` patch script
- a `.zip` archive containing exactly one `.sh` patch script

The `.zip` archive itself is treated as the input artifact for repeat/freshness/move lifecycle behavior.

## Important current behavior

The download runner currently owns these behaviors:

- choose the latest eligible patch input when no explicit path is provided
- support explicit patch input paths
- validate metadata before running
- run repeat detection
- run freshness checks
- run Bash syntax checks
- run patch preflight linting
- execute the patch when all preflight checks pass
- skip execution in dry-run mode
- move successful inputs to the done workflow
- move failed inputs to the failed workflow
- keep logs in the download directory
- print a final success or failure band
- optionally show or suppress progress context

## Non-goals for this inventory

This inventory does not:

- change `c`
- switch `c` to PatchHarbor
- remove the old runner
- migrate export behavior
- claim parity with PatchHarbor download runner APIs
- define the full lifecycle flow

The lifecycle flow is documented in the next planned step.
