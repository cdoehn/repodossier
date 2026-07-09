# PATCHHARBOR.09f1 – Source-side runner adoption acceptance

This document records the acceptance state for the first additive RepoDossier adoption of the PatchHarbor runner.

This patch documents acceptance only. It does not change scripts, aliases, tests, export behavior, or the PatchHarbor target repository.

## Accepted scope

Milestone 09 is accepted as a source-side additive adoption step when these artifacts exist and keep their documented roles.

| Area | Artifact | Accepted role |
| --- | --- | --- |
| Thin source wrapper | `scripts/dev/run_patchharbor_patch.sh` | explicit wrapper for running a selected patch through PatchHarbor |
| Wrapper contract tests | `tests/test_patchharbor_runner_wrapper.py` | verifies wrapper shape and preserved source runner files |
| Wrapper smoke tests | `tests/test_patchharbor_runner_wrapper_smoke.py` | verifies no-execute smoke through the PatchHarbor CLI path |
| Alias compatibility | `scripts/dev/install_aliases.sh` | keeps old aliases and adds `patchharbor-patch` additively |
| Alias tests | `tests/test_dev_alias_installer.py` | verifies old aliases are preserved and the new alias is additive |
| Current `c` contract | `planning/patchharbor/c-alias-contract.md` | documents that `c` still belongs to the old download runner |
| Future `c` criteria | `planning/patchharbor/c-alias-switch-criteria.md` | documents conditions before any future `c` switch |
| Switch plan tests | `tests/test_c_alias_switch_plan.py` | checks that the contract and criteria remain explicit |

## Explicitly accepted current behavior

The current adoption accepts these statements:

- `patchharbor-patch` is an additional alias, not a replacement for `c`.
- `c` still points to `scripts/dev/run_latest_download_patch.sh`.
- `r` still points to `scripts/dev/r.sh`.
- scripts/dev/run_repodossier_exports.sh remains unchanged.
- `scripts/dev/run_repodossier_exports.sh` remains unchanged by this adoption.
- `scripts/dev/run_patchharbor_patch.sh` is the explicit PatchHarbor path.
- The PatchHarbor target repository is checked but not changed by source-side adoption patches.
- The old local download runner remains available.
- The export workflow remains outside this milestone.

## Non-goals

Milestone 09 does not finish the full migration.

It does not:

- switch `c`
- replace the download patch lifecycle
- delete the old download runner
- migrate exports
- delete source helper files
- install aliases into a real shell environment
- mutate the PatchHarbor target repository from source adoption patches
- claim download runner parity
- claim export runner parity

## Required next checks

The next acceptance test patch should verify this document and the related files.

That test patch should stay small and should only add the acceptance test file. It should not edit scripts or aliases.

## Acceptance checklist

PATCHHARBOR.09 source-side runner adoption is accepted when:

- the explicit PatchHarbor wrapper exists
- wrapper tests exist
- wrapper smoke tests exist
- `patchharbor-patch` is additive
- `c` remains on the old download runner
- `r` remains on the export wrapper
- export scripts remain untouched
- the `c` switch is documented as a future controlled step
- the PatchHarbor target repository remains read-only during source-side adoption
