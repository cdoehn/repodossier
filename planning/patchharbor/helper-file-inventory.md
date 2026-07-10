# PATCHHARBOR.12a1 – Helper File Inventory

This document inventories RepoDossier development helper files before helper migration work starts.

`planning/milestones_migration.md` is the operative plan for this migration. This document follows the `PATCHHARBOR.12a1 – Helper File Inventory` entry and does not introduce classification or implementation changes.

## Current helper files

| Path | Current role | Migration note |
| --- | --- | --- |
| `scripts/dev/audit_public_repo.py` | public repository audit helper | candidate for generic PatchHarbor audit helpers |
| `scripts/dev/check_dev_environment.py` | developer environment check helper | candidate for generic PatchHarbor environment helpers |
| `scripts/dev/install_aliases.sh` | source-side alias installer | source-specific integration wrapper |
| `scripts/dev/lint_patch_script.py` | patch script lint helper | already related to PatchHarbor linting contracts |
| `scripts/dev/patch-rules.md` | human-readable patch rules | source policy / workflow documentation |
| `scripts/dev/patch-workflow-rules.json` | patch workflow rule data | candidate for generic workflow-rule data only after classification |
| `scripts/dev/patch-workflow-rules.schema.json` | patch workflow rule schema | candidate for generic workflow-rule schema only after classification |
| `scripts/dev/r.sh` | source export wrapper entry point | source-specific wrapper kept for `r` workflow |
| `scripts/dev/repo_patch_helper.py` | repository patch helper | candidate for classification before any move |
| `scripts/dev/run_latest_download_patch.sh` | source download patch runner | already covered by PATCHHARBOR.10 migration |
| `scripts/dev/run_patchharbor_patch.sh` | source PatchHarbor patch runner wrapper | source integration wrapper |
| `scripts/dev/run_repodossier_exports.sh` | source export runner | already covered by PATCHHARBOR.11 migration |
| `scripts/dev/show_progress_context.py` | progress/context display helper | candidate for classification; display behavior is compatibility-sensitive |
| `scripts/dev/validate_patch_metadata.py` | patch metadata validator | candidate only if metadata contract remains compatible |
| `scripts/dev/validate_patch_workflow_rules.py` | workflow rule validator | candidate for generic workflow-rule validation after classification |

Optional/currently migration-created helpers may also exist:

| Path | Current role | Migration note |
| --- | --- | --- |
| `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` | removed candidate download runner wrapper | migration artifact from PATCHHARBOR.10d, removed by PATCHHARBOR.14b3 |

## Helper groups for the next classification step

PATCHHARBOR.12a1 only inventories files. PATCHHARBOR.12a2 should classify them into groups such as:

- public audit helpers
- development environment helpers
- patch workflow rule helpers
- metadata validation helpers
- source-only alias and wrapper helpers
- already migrated download/export runner helpers
- documentation/rule data files

## Known source-specific constraints

The following details must not be blindly moved into generic PatchHarbor target code:

- RepoDossier package names or CLI defaults
- source repository wrapper names
- `r` and `c` alias behavior
- generated export artifact names
- German source-side terminal output markers
- migration planning file paths
- local machine paths or private identity values

## Non-goals for PATCHHARBOR.12a1

This patch does not:

- classify helpers
- move helpers to PatchHarbor
- modify helper behavior
- change aliases
- change `c`
- change `r`
- change download runner behavior
- change export runner behavior
- add target-side helper APIs
- delete source-side helpers

## Acceptance for this patch

This inventory is accepted when:

- every current `scripts/dev` helper is listed or intentionally noted as optional
- source-specific and generic-candidate concerns are separated
- no helper behavior is changed
- both repositories remain clean except for this inventory document

## Next step

PATCHHARBOR.12a2 should classify helpers using this inventory as input.


## PATCHHARBOR.14b2 applied

- `scripts/dev/lint_patch_script.py` was removed as an obsolete lint wrapper.
- `scripts/dev/run_latest_download_patch.sh` calls PatchHarbor `lint-script` for dry-run preflight linting.
- `scripts/dev/run_latest_download_patch.sh` keeps internal metadata validation for `c` compatibility.


## PATCHHARBOR.14b3 applied

- `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` was removed as a historical candidate artifact.
- `scripts/dev/run_latest_download_patch.sh` remains the productive `c` runner.
- `scripts/dev/run_patchharbor_patch.sh` remains the source-side PatchHarbor wrapper.
- No alias, `c`, `r`, export wrapper, or target PatchHarbor file was changed by this cleanup step.
