# PATCHHARBOR.11c1 – Export Source Wrapper Draft

This document drafts the controlled source-side export runner migration after the PATCHHARBOR.11a inventory and PATCHHARBOR.11b target export model work.

The current productive entry points remain:

    scripts/dev/r.sh
    scripts/dev/run_repodossier_exports.sh

The goal of the 11c series is to migrate export-runner internals toward PatchHarbor while keeping the user-facing `r` workflow stable.

## Preconditions

This draft assumes the following are already green and committed:

- PATCHHARBOR.11a1 export runner file inventory
- PATCHHARBOR.11a2 export runner behavior inventory
- PATCHHARBOR.11a3 export runner inventory tests
- PATCHHARBOR.11b1 export job model
- PATCHHARBOR.11b2 export plan model
- PATCHHARBOR.11b3 export display helpers

The old source runner must remain available until smoke tests prove the replacement shape.

## Current source-side flow

The current flow is:

    r
    scripts/dev/r.sh
    scripts/dev/run_repodossier_exports.sh
    repodossier full
    repodossier export-ai
    repodossier export-docs
    repodossier changed

The current source-specific behavior includes:

- German terminal markers such as `r · RepoDossier Export Runner`
- default no-argument modes `full ai`
- dry-run no-argument modes `full ai docs changed`
- mode aliases such as `quick`, `doc`, `changes`, and `export-ai`
- `REPODOSSIER_BIN` override
- `PATCH_DOWNLOAD_DIR` output directory override
- artifact names `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt`
- optional `patch-rules.md` copy behavior

## Target-side building blocks

PATCHHARBOR.11b introduced generic target-side building blocks:

- `src/patchharbor/export_model.py`
- `src/patchharbor/export_planning.py`
- `src/patchharbor/export_display.py`

These target-side pieces are generic. They must not hard-code RepoDossier defaults such as command names, artifact names, German output markers, or environment variable names.

## Proposed 11c direction

The 11c source-side migration should be additive and test-first.

Recommended order:

1. Add source wrapper smoke tests for the current `r` behavior.
2. Add a candidate source wrapper or internal adapter that maps RepoDossier export modes to PatchHarbor generic export models.
3. Compare candidate behavior against the existing source runner.
4. Only then switch implementation behind the existing source entry point if tests prove compatibility.

## Compatibility contract to preserve

A future implementation must preserve:

- `r` as the user-facing command
- `scripts/dev/r.sh` as a stable source-side wrapper path
- current default mode expansion
- current dry-run mode expansion
- current mode aliases
- current unknown-mode rejection
- current Git repository preflight
- current `REPODOSSIER_BIN` lookup behavior
- current `PATCH_DOWNLOAD_DIR` behavior
- current generated artifacts
- current optional `patch-rules.md` copy behavior
- current visible output markers
- current exit-code behavior

Any intentional behavior change must be documented explicitly and tested in its own patch.

## Non-goals for PATCHHARBOR.11c1

This patch does not:

- edit `scripts/dev/r.sh`
- edit `scripts/dev/run_repodossier_exports.sh`
- edit `scripts/dev/install_aliases.sh`
- change aliases
- change export modes
- change RepoDossier CLI commands
- add PatchHarbor CLI commands
- change PatchHarbor target code
- remove source-side export logic
- switch `r`

## Risk controls

Before any source implementation switch:

- `tests/test_export_runner_inventory_docs.py` must stay green
- source wrapper smoke tests must be added and green
- PatchHarbor target export tests must stay green
- PatchHarbor doctor must stay green
- target repository must remain clean during source-only patches
- rollback must be a plain Git revert of the source wrapper implementation commit

## Next step

PATCHHARBOR.11c2 should add source export wrapper smoke tests without changing productive source behavior.
