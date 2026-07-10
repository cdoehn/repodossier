# PATCHHARBOR.10d1 – Source Download Runner Wrapper Draft

This document drafts the controlled source-side wrapper migration for the RepoDossier download patch runner.

The current productive source entry point remains:

    scripts/dev/run_latest_download_patch.sh

The goal of the 10d series is to make that old entry point thinner while keeping the user-facing `c` workflow stable.

## Preconditions

This draft assumes the following are already green:

- PATCHHARBOR.10a inventory and acceptance
- PATCHHARBOR.10b parity tests and parity acceptance
- PATCHHARBOR.10c target-side download runner selection and lifecycle plan APIs
- PATCHHARBOR.10c4 lifecycle plan acceptance

The old runner must remain available until the wrapper harness proves parity.

## Current source contract to preserve

The wrapper must preserve the current source-side contract protected by 10b:

- same input selection behavior
- same direct `.sh` artifact behavior
- same `.zip` archive behavior
- same metadata preflight behavior
- same `progress_context=false` behavior
- same freshness confirmation behavior
- same repeat detection behavior
- same syntax failure behavior
- same success lifecycle behavior
- same failure lifecycle behavior
- same final footer behavior
- same done / failed moves
- same log-file behavior
- same applied-ledger behavior
- same exit-code behavior

If any behavior changes intentionally, the change must be explicit and covered by tests.

## Target APIs available after 10c

The target-side PatchHarbor APIs available after 10c are:

- `select_download_artifact(...)`
- `create_lifecycle_plan(...)`
- `DownloadArtifactSelection.to_mapping()`
- `DownloadLifecyclePlan.to_mapping()`

These APIs are planning primitives only. They do not execute scripts, validate metadata, move files, or write ledgers.

## Proposed wrapper direction

The eventual implementation should keep the old filename and route through PatchHarbor behavior behind it.

Minimal target shape:

    #!/usr/bin/env bash
    set -euo pipefail
    exec patchharbor run-script "$@"

This is a direction, not the implementation for this patch.

## Scope of the 10d series

### PATCHHARBOR.10d1

Document this wrapper draft only.

### PATCHHARBOR.10d2

Add a source-side wrapper test harness that can compare old-runner behavior against a wrapper candidate.

### PATCHHARBOR.10d3

Only after the harness is green, switch the implementation behind the old filename.

### PATCHHARBOR.10d4

Document adoption acceptance and rollback instructions.

## Non-goals for 10d1

This patch does not:

- edit `scripts/dev/run_latest_download_patch.sh`
- edit alias installers
- change `c`
- change export scripts
- change PatchHarbor target code
- remove the old runner
- commit any target-repository file

## Risk controls

Before any implementation switch, the following must remain true:

- all 10b parity tests pass
- source wrapper harness passes
- PatchHarbor target tests pass
- PatchHarbor doctor passes
- PatchHarbor target repository remains clean during source-only changes
- rollback is a plain Git revert of the wrapper implementation commit

## Next step

PATCHHARBOR.10d2 should add the wrapper test harness without changing the productive runner.
