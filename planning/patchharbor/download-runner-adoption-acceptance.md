# PATCHHARBOR.10d4 – Download Runner Adoption Acceptance Documentation

This document accepts the current PATCHHARBOR.10d download runner adoption state.

The accepted state is deliberately conservative: the PatchHarbor-backed download runner candidate exists and is covered by a source-side harness, but the productive RepoDossier download runner entry point has not been replaced in this step.

## Accepted source files

| Area | Path |
| --- | --- |
| productive download runner | `scripts/dev/run_latest_download_patch.sh` |
| historical historical historical PatchHarbor-backed candidate runner | `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` |
| wrapper draft | `planning/patchharbor/source-download-runner-wrapper-draft.md` |
| wrapper harness tests | `tests/test_download_runner_wrapper_harness.py` |
| wrapper candidate tests | `tests/test_download_runner_wrapper_candidate.py` |

## Accepted target prerequisites

The source-side candidate depends on the accepted PATCHHARBOR.10c target planning APIs:

- `src/patchharbor/download_selection.py`
- `src/patchharbor/download_plan.py`
- `src/patchharbor/cli.py`
- `docs/download-runner-lifecycle-plan-acceptance.md`

## Accepted behavior

PATCHHARBOR.10d accepts the following behavior:

- the old productive source runner remains present
- the historical candidate runner was additive before PATCHHARBOR.14b3
- the user-facing `c` workflow is not switched by this patch
- the candidate can be compared against the old runner by tests
- the candidate keeps `progress_context=false` metadata support in dummy patches
- source parity tests remain the safety net
- target API tests remain green
- PatchHarbor doctor remains green
- source-only patches must leave the target repository unchanged

## Explicit non-goals

This acceptance documentation does not:

- switch `c`
- replace `scripts/dev/run_latest_download_patch.sh`
- edit alias installers
- edit export scripts
- remove the old runner
- delete the candidate runner before PATCHHARBOR.14b3 before PATCHHARBOR.14b3 before PATCHHARBOR.14b3
- change PatchHarbor target code
- change runner output contracts

## Rollback

Rollback is intentionally simple:

1. Revert the commit that added the candidate runner if the candidate itself is wrong.
2. Revert this acceptance documentation if the documented state is wrong.
3. Do not touch the productive old runner unless a later explicit replacement commit changed it.
4. Keep PATCHHARBOR.10b parity tests before any future replacement attempt.

## Readiness for tests

PATCHHARBOR.10d5 should add acceptance tests for this document.

Those tests should verify:

- the document references productive and candidate runner paths
- the document records that `c` is not switched here
- the document records rollback instructions
- the candidate and harness files exist
- no private/local values are stored


## PATCHHARBOR.14b3 applied

- `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` was removed as a historical candidate artifact.
- `scripts/dev/run_latest_download_patch.sh` remains the productive `c` runner.
- `scripts/dev/run_patchharbor_patch.sh` remains the source-side PatchHarbor wrapper.
- No alias, `c`, `r`, export wrapper, or target PatchHarbor file was changed by this cleanup step.


the historical candidate runner was removed by PATCHHARBOR.14b3


the historical candidate runner was removed by PATCHHARBOR.14b3
