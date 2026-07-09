# PATCHHARBOR.09e1 – Current `c` alias contract

This document records the current RepoDossier `c` alias contract before any controlled switch plan is discussed.

This patch does not change aliases. It only documents the current behavior.

## Current state

RepoDossier currently keeps three relevant developer aliases in its alias installer:

| Alias | Current purpose | Current target |
| --- | --- | --- |
| `rdrepo` | jump to the RepoDossier repository | repository root |
| `c` | run the existing local download patch runner | `scripts/dev/run_latest_download_patch.sh` |
| `r` | run the existing export wrapper | `scripts/dev/r.sh` |

PATCHHARBOR.09d added one optional additive alias:

| Alias | Purpose | Target |
| --- | --- | --- |
| `patchharbor-patch` | run an explicit patch file through the new thin PatchHarbor wrapper | `scripts/dev/run_patchharbor_patch.sh` |

## `c` is not switched yet

The `c` alias still belongs to the existing local download patch runner.

It must not be silently changed to `patchharbor-patch` or to `patchharbor run-script`.

Any future switch of `c` requires a separate plan, parity checks, rollback notes, and focused tests.

## Current `c` behavior to preserve

The current `c` workflow is expected to preserve these user-facing behaviors until a later explicit migration changes them:

- select the patch script from the downloads workflow
- validate patch metadata before execution
- prevent accidental repeated application
- reject stale patch scripts when configured
- run Bash syntax checks before execution
- execute the patch script
- keep a log file available
- move successful scripts into the done workflow
- move failed scripts into the failed workflow
- show done/current/next/problem context in the footer

The new `patchharbor-patch` alias does not replace this workflow. It only gives an explicit path for running a chosen patch file through PatchHarbor.

## Things this contract forbids for now

Future patches must not do any of these without a dedicated switch plan:

- repoint `c` to `patchharbor-patch`
- repoint `c` directly to `patchharbor run-script`
- remove `scripts/dev/run_latest_download_patch.sh`
- remove the old download lifecycle behavior
- change `r` while working on `c`
- change export scripts while working on `c`
- install aliases during a patch run
- write shell rc files outside explicit installer execution

## Acceptance for this document

This contract is accepted when:

- the document exists
- it names the current `c` target
- it names the additive `patchharbor-patch` alias
- it states that `c` is not switched yet
- it lists the preserved behavior
- it states that a later switch needs a separate plan and tests
