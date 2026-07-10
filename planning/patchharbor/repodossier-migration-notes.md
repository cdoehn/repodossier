# PATCHHARBOR.14c3 – RepoDossier migration notes

These notes summarize the current RepoDossier source state after the PatchHarbor migration cleanup.

`planning/milestones_migration.md` remains the operative migration plan. This document is a historical and maintenance summary.

## Current source state

RepoDossier keeps the product-specific source workflows in the source repository:

| Workflow | Current path | Status |
| --- | --- | --- |
| Download patch runner | `scripts/dev/run_latest_download_patch.sh` | active |
| RepoDossier export runner | `scripts/dev/r.sh` | active |
| RepoDossier export wrapper | `scripts/dev/run_repodossier_exports.sh` | active |
| PatchHarbor source wrapper | `scripts/dev/run_patchharbor_patch.sh` | active |
| Developer alias installer | `scripts/dev/install_aliases.sh` | active |

The current user-facing source aliases remain:

| Alias | Purpose |
| --- | --- |
| `rdrepo` | change into the RepoDossier checkout |
| `c` | run the Download patch workflow |
| `r` | run RepoDossier export modes |
| `patchharbor-patch` | explicit source wrapper for PatchHarbor patch execution |

## Current target relationship

PatchHarbor owns generic development infrastructure:

| PatchHarbor command | RepoDossier use |
| --- | --- |
| `patchharbor lint-script` | dry-run patch preflight from `c` |
| `patchharbor run-script` | generic patch execution behavior |
| `patchharbor audit-public` | public/private value audit behavior |
| `patchharbor check-env` | development environment checks |

RepoDossier should not duplicate generic PatchHarbor implementation details when a PatchHarbor command already exists.

## Source cleanup history

### PATCHHARBOR.14b1

Removed obsolete metadata-helper wrapper:

    scripts/dev/validate_patch_metadata.py

Current replacement:

    internal metadata validation inside scripts/dev/run_latest_download_patch.sh

Reason:

- `c` must keep the Download patch metadata contract.
- The source helper wrapper was no longer the authoritative implementation.
- The active runner should not import or execute the removed helper.

### PATCHHARBOR.14b2

Removed obsolete source-side lint wrapper:

    scripts/dev/lint_patch_script.py

Current replacement:

    patchharbor lint-script

Reason:

- Patch-script linting is generic PatchHarbor infrastructure.
- The source wrapper duplicated target behavior.
- `c` now calls PatchHarbor for dry-run preflight linting.

### PATCHHARBOR.14b3

Removed historical candidate runner artifact:

    scripts/dev/run_latest_download_patch_patchharbor_candidate.sh

Current replacement:

    scripts/dev/run_latest_download_patch.sh

Reason:

- The candidate artifact was only an adoption bridge.
- The productive `c` runner remains the single active Download patch runner.
- Candidate-runner behavior is now either in the productive source runner or PatchHarbor target implementation.

### PATCHHARBOR.14b4

Removed duplicate runner self-copy bootstrap from the productive `c` runner.

Current state:

- `scripts/dev/run_latest_download_patch.sh` remains active.
- It has one self-copy bootstrap.
- It still handles Downloads, ZIP archives, logs, `done`, `failed`, dry-run, ledger, and lifecycle output.
- It still uses internal metadata validation and PatchHarbor `lint-script`.

## Documentation updates

### PATCHHARBOR.14c1

Developer workflow documentation now lives in:

    planning/patchharbor/repodossier-developer-workflow.md
    docs/dev-aliases.md

That documentation records the active source commands and the removed helper state.

### PATCHHARBOR.14c2

Installation documentation now lives in:

    README.md
    docs/installation.md

That documentation separates:

- pipx user installation
- editable development installation
- optional developer aliases
- PatchHarbor usage during development

## Current command contract

Use this for normal CLI installation from a local checkout:

    python3 -m pipx uninstall repodossier 2>/dev/null || true
    python3 -m pipx install "$PWD"
    repodossier --version

Use this for development:

    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -e ".[dev]"
    python3 -m pytest --color=yes

Use this for optional development aliases:

    scripts/dev/install_aliases.sh --dry-run
    scripts/dev/install_aliases.sh

## Maintenance rules

Future migration patches must follow these rules:

1. Do not recreate removed source helper wrappers.
2. Do not point active workflow files back to removed helper paths.
3. Treat exact removed helper paths as historical migration facts and keep them in migration notes or historical planning documents only.
4. Keep `c` active until a later milestone explicitly replaces the user-facing workflow.
5. Keep `r` active until a later milestone explicitly replaces RepoDossier export workflow.
6. Keep source-only documentation patches from changing PatchHarbor target files.
7. Use PatchHarbor for generic patch infrastructure.
8. Keep RepoDossier source wrappers for product-specific workflows.
9. Keep installation documentation separate from developer-alias documentation.
10. Keep private local paths, user names, email addresses, and workstation names out of tracked files.

## Non-goals for PATCHHARBOR.14c3

This patch does not:

- change `c`
- change `r`
- change aliases
- change package metadata
- change PatchHarbor target files
- remove additional source files
- change installation commands
- change export behavior

Final source cleanup acceptance is handled by PATCHHARBOR.14c4.
