# PATCHHARBOR.14a1 – RepoDossier Script Cleanup Inventory

This document inventories RepoDossier source-side development scripts before any cleanup or deletion.

`planning/milestones_migration.md` is the operative plan. PATCHHARBOR.14a1 is inventory-only and source-only.

## Cleanup principle

Cleanup is not extraction.

The migration already introduced generic PatchHarbor implementations and source-side compatibility wrappers in earlier milestones. PATCHHARBOR.14 must now decide, file by file, whether old RepoDossier scripts can be removed, kept as thin wrappers, or kept as source policy.

Nothing is deleted by PATCHHARBOR.14a1.

## Current source script inventory

| Path | Current state | Cleanup classification | Removal gate |
| --- | --- | --- | --- |
| `scripts/dev/audit_public_repo.py` | source public-audit wrapper around PatchHarbor public-audit behavior | candidate for wrapper cleanup after source workflow docs are updated | prove `patchharbor audit-public` covers tracked-file audit needs |
| `scripts/dev/check_dev_environment.py` | source environment wrapper using PatchHarbor environment model additively | candidate for wrapper cleanup after source workflow docs are updated | prove `patchharbor check-env` covers source doctor needs or keep documented source wrapper |
| `scripts/dev/install_aliases.sh` | source alias installer for local developer shell aliases | keep source-side integration for now | only change after alias contract tests and install docs are updated |
| `scripts/dev/lint_patch_script.py` | legacy/source patch lint helper | candidate for obsolete lint wrapper removal | prove `patchharbor lint-script` covers the workflow and old helper is not referenced |
| `scripts/dev/patch-rules.md` | human patch policy and workflow rules | keep as source policy documentation for now | only split after generic policy model exists |
| `scripts/dev/patch-workflow-rules.json` | machine-readable workflow rules | keep source-side data for now | only move after generic workflow-rule model and rule ID compatibility tests exist |
| `scripts/dev/patch-workflow-rules.schema.json` | workflow-rule schema | keep source-side schema for now | only move after schema compatibility tests exist |
| `scripts/dev/r.sh` | source `r` export wrapper entry point | keep thin compatibility wrapper | only remove if alias/docs no longer require `r` |
| `scripts/dev/repo_patch_helper.py` | source repository patch helper library/CLI | high-risk candidate, not first cleanup target | requires explicit replaced-logic map and tests before any deletion |
| `scripts/dev/run_latest_download_patch.sh` | source `c` download patch runner | candidate for obsolete runner helper cleanup in small parts | prove `scripts/dev/run_patchharbor_patch.sh` and PatchHarbor runner cover the workflow |
| `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` | migration candidate artifact for download runner transition | candidate for cleanup artifact removal | prove no alias, test, or docs path still points at it |
| `scripts/dev/run_patchharbor_patch.sh` | source wrapper around PatchHarbor patch runner | keep source-side compatibility wrapper for now | only change after `c` alias and source docs point to the final wrapper |
| `scripts/dev/run_repodossier_exports.sh` | source export runner using PatchHarbor export planning additively | keep source-specific export wrapper | only remove if RepoDossier export workflow is replaced by documented PatchHarbor command config |
| `scripts/dev/show_progress_context.py` | source progress/context display helper | display-sensitive, do not block cleanup on display-only tests | remove only after metadata/context display responsibilities are mapped |
| `scripts/dev/validate_patch_metadata.py` | source metadata validator | candidate for obsolete metadata helper wrapper cleanup | prove PatchHarbor metadata/preflight validation covers current metadata contract |
| `scripts/dev/validate_patch_workflow_rules.py` | source workflow-rule validator | keep until rule model is migrated | requires workflow-rule model and schema compatibility tests |

## Non-dev script noted for later review

| Path | Current state | Cleanup classification | Removal gate |
| --- | --- | --- | --- |
| `scripts/validate_pipx_release.sh` | RepoDossier release validation script | source product release helper, not a PatchHarbor cleanup target in 14b | review only in RepoDossier install/release documentation updates |

## First cleanup candidates

These are the safest candidates for the 14b series, but only after 14a2 and 14a3 prove replacement coverage.

| Planned area | Candidate files | Why it is a candidate |
| --- | --- | --- |
| obsolete metadata helper wrapper | `scripts/dev/validate_patch_metadata.py`, possibly part of `scripts/dev/show_progress_context.py` | PatchHarbor runner/preflight metadata contracts exist, but source compatibility must be mapped |
| obsolete lint wrapper | `scripts/dev/lint_patch_script.py` | PatchHarbor `lint-script` exists and is tested |
| obsolete runner helper part 1 | `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` | migration artifact likely obsolete after adoption |
| obsolete runner helper part 2 | old logic inside `scripts/dev/run_latest_download_patch.sh` | high-risk because `c` workflow and Download runner lifecycle are user-facing |

## Keep for now

These files should not be removed in early 14b cleanup:

- `scripts/dev/install_aliases.sh`
- `scripts/dev/run_patchharbor_patch.sh`
- `scripts/dev/r.sh`
- `scripts/dev/run_repodossier_exports.sh`
- `scripts/dev/patch-rules.md`
- `scripts/dev/patch-workflow-rules.json`
- `scripts/dev/patch-workflow-rules.schema.json`
- `scripts/dev/validate_patch_workflow_rules.py`
- `scripts/dev/repo_patch_helper.py`
- `scripts/validate_pipx_release.sh`

## Replacement evidence already available

| Source concern | PatchHarbor evidence |
| --- | --- |
| download patch runner | download runner parity, adoption acceptance, source wrapper sanity tests |
| export runner | export model, planning, display helpers, source export wrapper smoke tests |
| public repository audit | public audit model/checks/CLI and source public audit wrapper |
| environment checks | environment model/CLI and source environment wrapper |
| CLI/package readiness | CLI inventory, exit-code contract, help-surface tests, packaging metadata/readme/pipx/acceptance tests |

## Required next document

PATCHHARBOR.14a2 must create a replaced logic map before any source deletion.

That map should connect every candidate deletion to:

- replacement PatchHarbor module or command
- source wrapper or alias still in use
- tests that prove the old behavior is covered
- known gaps that block deletion

## Required safety tests

PATCHHARBOR.14a3 must add cleanup safety tests before 14b removes any script or helper.

The safety tests should prove at least:

- no alias points at a deleted candidate
- no README/planning/test path references a deleted candidate unless explicitly historical
- `c` and `r` compatibility paths remain intact
- target PatchHarbor commands still exist
- display-only formatting is not treated as a functional cleanup blocker

## Non-goals for PATCHHARBOR.14a1

This patch does not:

- delete source scripts
- edit source scripts
- change aliases
- change `c`
- change `r`
- change PatchHarbor target files
- change package metadata
- change README installation docs
- decide final deletion of high-risk helpers
- add cleanup safety tests
- add display-only assertions

## Acceptance for this patch

PATCHHARBOR.14a1 is accepted when:

- all current source development scripts are inventoried
- currently migrated wrappers are separated from source-specific policy files
- first cleanup candidates are named but not removed
- high-risk files are explicitly kept for now
- PATCHHARBOR.14a2 and PATCHHARBOR.14a3 gates are clear
- PatchHarbor target repository remains unchanged


## PATCHHARBOR.14b1 applied

- `scripts/dev/validate_patch_metadata.py` was removed as an obsolete metadata helper wrapper.
- `scripts/dev/run_latest_download_patch.sh` calls `scripts/dev/lint_patch_script.py --metadata-only` for `c` metadata checks.
- `scripts/dev/lint_patch_script.py` keeps temporary metadata compatibility until PATCHHARBOR.14b2 removes the obsolete lint wrapper.
