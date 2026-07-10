# PATCHHARBOR.14c1 – RepoDossier Developer Workflow

This document is the current developer workflow for the RepoDossier source repository after PATCHHARBOR.14b cleanup.

`planning/milestones_migration.md` is still the operative migration plan.

## Current command surface

RepoDossier developers use these source-side entry points:

| Command | Source path | Current role |
| --- | --- | --- |
| `rdrepo` | installed by `scripts/dev/install_aliases.sh` | change into the RepoDossier checkout |
| `c` | `scripts/dev/run_latest_download_patch.sh` | run downloaded patch scripts and ZIP patch archives |
| `r` | `scripts/dev/r.sh` | run RepoDossier export modes |
| `scripts/dev/run_patchharbor_patch.sh` | source wrapper | explicit bridge to PatchHarbor runner behavior |
| `scripts/dev/run_repodossier_exports.sh` | source wrapper | RepoDossier-specific export command wrapper |

## `c` workflow after cleanup

The productive `c` workflow remains source-side in:

    scripts/dev/run_latest_download_patch.sh

`c` is still the user-facing command for Download patch execution.

Current behavior:

1. Find or accept a patch script or patch ZIP.
2. Extract ZIP patch archives into a temporary directory.
3. Validate `repodossier-meta` metadata internally before execution.
4. Run Bash syntax checks.
5. Use PatchHarbor `lint-script` for dry-run preflight linting.
6. Execute the patch script when not in dry-run mode.
7. Write a log file in the Downloads directory.
8. Move successful scripts or ZIP files to `done`.
9. Move failed scripts or ZIP files to `failed`.
10. Record successful patch application in the source-side ledger.

The runner intentionally keeps internal metadata validation so `c` does not depend on a removed source metadata helper.

The runner intentionally delegates lint preflight to PatchHarbor:

    patchharbor lint-script

When running from a sibling checkout, `c` discovers the PatchHarbor source checkout through `PATCHHARBOR_REPO` or the sibling `patch-harbor` directory.

## `r` export workflow

The `r` alias remains a RepoDossier source workflow because the exports are RepoDossier-specific.

The source-side entry points are:

    scripts/dev/r.sh
    scripts/dev/run_repodossier_exports.sh

Default behavior remains:

    r

The default export modes are:

    full ai

Additional examples:

    r docs
    r changed
    r full ai docs
    r --list-modes
    r --dry-run

PatchHarbor export planning is used additively by the source wrapper. The RepoDossier source wrapper remains responsible for source-specific export paths, modes, and product semantics.

## PatchHarbor target commands used by RepoDossier workflow

RepoDossier developer workflow may call PatchHarbor for generic development infrastructure:

| PatchHarbor command | Used for |
| --- | --- |
| `patchharbor lint-script` | patch-script preflight linting |
| `patchharbor run-script` | generic patch runner behavior through source wrappers |
| `patchharbor audit-public` | public/private value audit behavior |
| `patchharbor check-env` | environment checks |
| `patchharbor --help` | CLI availability check |
| `patchharbor --version` | packaging smoke check |

RepoDossier should keep source wrappers where the behavior remains source-specific.

## Removed legacy helpers

These paths were removed during PATCHHARBOR.14b cleanup and must not be used as active workflow commands:

| Removed path | Replacement |
| --- | --- |
| `scripts/dev/validate_patch_metadata.py` | internal `c` metadata validation |
| `scripts/dev/lint_patch_script.py` | PatchHarbor `lint-script` |
| `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` | productive `scripts/dev/run_latest_download_patch.sh` |

The removed paths may remain mentioned in historical migration notes, but current workflow docs must not instruct users to run them.

## Developer rules for future patches

Future RepoDossier development patches should follow these rules:

1. Keep `c` as the user-facing Download patch runner unless a later milestone explicitly changes it.
2. Keep `r` as the user-facing RepoDossier export runner unless a later milestone explicitly changes it.
3. Use PatchHarbor commands for generic patch infrastructure.
4. Do not recreate removed source helper wrappers.
5. Do not write contributor-specific local paths into tracked files.
6. Do not make display-only formatting tests block functional cleanup.
7. Keep target PatchHarbor files unchanged for source-only docs patches.
8. Update tests when documentation changes the active command contract.

## Non-goals for PATCHHARBOR.14c1

This patch does not:

- change aliases
- change `c`
- change `r`
- change PatchHarbor target files
- change install instructions
- remove additional scripts
- change package metadata
- change export behavior
- change runner behavior

Install documentation is handled by PATCHHARBOR.14c2.

Migration-note cleanup is handled by PATCHHARBOR.14c3.
