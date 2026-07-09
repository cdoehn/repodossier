# PATCHHARBOR.09e2 – `c` alias switch criteria

This document defines the criteria for a future controlled switch of the RepoDossier `c` alias.

This patch does not switch `c`.

## Current decision

The `c` alias remains on the existing local download patch runner:

    scripts/dev/run_latest_download_patch.sh

The additive `patchharbor-patch` alias remains the explicit PatchHarbor path:

    scripts/dev/run_patchharbor_patch.sh

A future `c` switch is allowed only after parity is proven and rollback is documented.

## Required parity before any `c` switch

A future patch may only repoint `c` when all of these are true:

- metadata validation parity is tested
- repeat-detection parity is tested
- freshness-check parity is tested
- Bash syntax failure parity is tested
- successful patch lifecycle parity is tested
- failed patch lifecycle parity is tested
- footer and progress context parity is tested
- log file behavior is tested
- done and failed folder behavior is tested
- the old download runner remains available for rollback
- export scripts remain untouched
- `r` remains unchanged

## Required implementation shape

A future switch must be explicit and small.

Allowed future approaches:

1. Keep `c` unchanged and keep `patchharbor-patch` as the explicit PatchHarbor path.
2. Repoint `c` to a source-side wrapper only after parity tests are green.
3. Keep the old runner under a documented rollback name before switching.

Not allowed in the same patch:

- switching `c` and changing export scripts
- switching `c` and deleting the old runner
- switching `c` and changing `r`
- switching `c` and installing aliases into the real shell environment
- switching `c` without focused tests

## Required rollback notes

A future switch patch must document:

- previous `c` target
- new `c` target
- one-command rollback
- how to verify rollback
- which files changed
- which tests prove parity

## Required focused tests before switching

The switch patch must run focused tests that prove:

- `c` is present
- `c` points to the intended new target
- old runner still exists
- new target exists
- `r` still points to export workflow
- `patchharbor-patch` remains available
- dry-run does not write shell rc files
- no private path literals are stored in tracked files

## Non-goals for this criteria document

This document does not:

- switch `c`
- modify aliases
- install aliases
- edit shell rc files
- modify PatchHarbor
- touch export scripts
- delete the old runner
- claim that parity already exists

## Acceptance

This criteria document is accepted when it states that `c` is not switched, lists required parity areas, lists rollback requirements, and names the focused tests needed before any future switch.
