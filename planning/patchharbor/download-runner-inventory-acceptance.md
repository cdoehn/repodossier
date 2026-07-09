# PATCHHARBOR.10a5 – Download Runner Inventory Acceptance

This document accepts the Download Runner Inventory phase.

PATCHHARBOR.10a captured and tested the current RepoDossier download patch runner behavior before any parity migration or PatchHarbor replacement work begins.

## Accepted scope

PATCHHARBOR.10a is accepted when the source repository contains:

- file and artifact inventory for the current download runner
- lifecycle flow documentation for the current download runner
- terminal output contract documentation for the current download runner
- tests that keep those inventory documents aligned with the current runner

## Accepted files

| Area | Path |
| --- | --- |
| file inventory | `planning/patchharbor/download-runner-file-inventory.md` |
| lifecycle flow | `planning/patchharbor/download-runner-lifecycle-flow.md` |
| output contract | `planning/patchharbor/download-runner-output-contract.md` |
| inventory tests | `tests/test_download_runner_inventory_docs.py` |
| current runner | `scripts/dev/run_latest_download_patch.sh` |

## Accepted behavior

The inventory phase documents the current behavior only.

It covers:

- direct `.sh` patch scripts
- `.zip` archives containing one patch script
- metadata validation
- repeat detection
- freshness checks
- Bash syntax checks
- patch preflight linting
- execution handoff
- dry-run behavior
- progress context suppression through patch metadata
- done and failed lifecycle moves
- applied ledger behavior
- terminal output contract
- success and failure completion semantics

## Explicit non-goals

PATCHHARBOR.10a does not introduce:

- PatchHarbor download runner API changes
- source runner replacement
- `c` alias migration
- alias installation
- export runner migration
- deletion of old source scripts
- changes to done or failed lifecycle behavior
- changes to terminal output behavior

## Readiness for PATCHHARBOR.10b

PATCHHARBOR.10b may start parity tests only after this acceptance is green.

The next phase should test current behavior with focused parity tests before any target-side API or source-side replacement is introduced.

Expected next parity test areas:

- metadata validation
- freshness rejection
- repeat rejection
- syntax failure
- success lifecycle
- failure lifecycle
- footer and output semantics

## Acceptance checks

This phase is accepted when the source repository passes:

    python3 -m compileall tests
    python3 -m pytest tests/test_download_runner_inventory_docs.py
    python3 -m pytest tests/test_download_runner_inventory_acceptance.py
    python3 -m pytest tests/test_download_patch_runner.py tests/test_download_runner_inventory_docs.py tests/test_download_runner_inventory_acceptance.py

Manual review should confirm that PATCHHARBOR.10a documented and tested existing behavior only.
