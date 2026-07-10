# PATCHHARBOR.12a2 – Helper Classification

This document classifies RepoDossier development helper files after the PATCHHARBOR.12a1 helper file inventory.

`planning/milestones_migration.md` is the operative patch plan. This classification follows the `PATCHHARBOR.12a2 – Helper Classification` entry and does not move or modify helper behavior.

## Classification overview

| Group | Helper files | Migration direction |
| --- | --- | --- |
| public audit helpers | `scripts/dev/audit_public_repo.py` | migrate to generic PatchHarbor audit APIs in PATCHHARBOR.12b |
| development environment helpers | `scripts/dev/check_dev_environment.py` | migrate to generic PatchHarbor environment checks in PATCHHARBOR.12c |
| patch script lint helpers | `scripts/dev/lint_patch_script.py` | already related to target linting contracts; do not re-migrate blindly |
| patch workflow rule helpers | `scripts/dev/patch-workflow-rules.json`, `scripts/dev/patch-workflow-rules.schema.json`, `scripts/dev/validate_patch_workflow_rules.py` | candidate for later generic workflow-rule model after public/environment helpers |
| patch metadata helpers | `scripts/dev/validate_patch_metadata.py`, `scripts/dev/show_progress_context.py` | compatibility-sensitive; keep source-side until metadata/display contracts are explicitly migrated |
| source alias and wrapper helpers | `scripts/dev/install_aliases.sh`, `scripts/dev/run_patchharbor_patch.sh` | source integration wrappers; keep source-side unless a later patch explicitly changes alias behavior |
| source export helpers | `scripts/dev/r.sh`, `scripts/dev/run_repodossier_exports.sh` | already covered by PATCHHARBOR.11 migration |
| source download helpers | `scripts/dev/run_latest_download_patch.sh`, `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` | already covered by PATCHHARBOR.10 migration |
| repository patch helper | `scripts/dev/repo_patch_helper.py` | candidate for later classification only; do not move before exact contract tests exist |
| documentation and policy data | `scripts/dev/patch-rules.md` | source policy/rule documentation; keep source-side unless a later generic policy model is introduced |

## Detailed helper classification

### Public audit helpers

Primary file:

    scripts/dev/audit_public_repo.py

Classification:

- generic-candidate
- target direction: PatchHarbor public audit model/checks/CLI
- planned area: PATCHHARBOR.12b
- source-specific risk: repository-publication policy may include RepoDossier wording

Migration rule:

Do not change the current source helper until target public-audit tests prove the generic contract.

### Development environment helpers

Primary file:

    scripts/dev/check_dev_environment.py

Classification:

- generic-candidate
- target direction: PatchHarbor environment check model/CLI
- planned area: PATCHHARBOR.12c
- source-specific risk: local tool names, package assumptions, and source workflow defaults

Migration rule:

Generic environment checks must be parameterized. Do not hard-code local workstation paths or private identities.

### Patch workflow rule helpers

Files:

    scripts/dev/patch-workflow-rules.json
    scripts/dev/patch-workflow-rules.schema.json
    scripts/dev/validate_patch_workflow_rules.py

Classification:

- generic-candidate, but not immediate
- target direction: possible workflow-rule data/model/validation API
- planned area: later helper migration after 12b and 12c

Migration rule:

The schema and rule identifiers are contracts. Any migration must read existing tests and rule data first.

### Patch metadata and context helpers

Files:

    scripts/dev/validate_patch_metadata.py
    scripts/dev/show_progress_context.py

Classification:

- compatibility-sensitive
- target direction: only after metadata and context-display contracts are fully specified
- planned area: not PATCHHARBOR.12b or PATCHHARBOR.12c

Migration rule:

Do not weaken metadata validation. Context display suppression through `progress_context=false` must remain compatible.

### Source alias and wrapper helpers

Files:

    scripts/dev/install_aliases.sh
    scripts/dev/run_patchharbor_patch.sh

Classification:

- source-only integration helpers
- target direction: usually no generic target migration
- planned area: only explicit source-adoption patches

Migration rule:

Alias output is a compatibility contract. Do not invent exact new alias forms when the existing installer already defines the behavior.

### Source export helpers

Files:

    scripts/dev/r.sh
    scripts/dev/run_repodossier_exports.sh

Classification:

- already-migrating source export helpers
- target direction: PATCHHARBOR.11 already introduced generic export model/planning/display helpers
- planned area: PATCHHARBOR.11

Migration rule:

Do not reclassify these as PATCHHARBOR.12 targets. PATCHHARBOR.12 should only depend on their inventory where needed.

### Source download helpers

Files:

    scripts/dev/run_latest_download_patch.sh
    scripts/dev/run_latest_download_patch_patchharbor_candidate.sh

Classification:

- already-migrated / already-covered download helpers
- target direction: PATCHHARBOR.10 already covered download runner parity/API/adoption
- planned area: PATCHHARBOR.10

Migration rule:

Do not restart download runner migration under PATCHHARBOR.12.

### Repository patch helper

Primary file:

    scripts/dev/repo_patch_helper.py

Classification:

- undecided generic-candidate
- target direction: possible later helper API
- planned area: later than PATCHHARBOR.12c unless milestones define otherwise

Migration rule:

Read implementation and tests before moving. Do not assume it is generic just because it is a Python helper.

### Documentation and policy data

Primary file:

    scripts/dev/patch-rules.md

Classification:

- source policy/documentation
- target direction: keep source-side for now
- planned area: none in current 12b/12c plan

Migration rule:

Do not move policy text into generic target code without a specific milestone and tests.

## Immediate migration sequence from this classification

The next operative steps from `planning/milestones_migration.md` are:

1. PATCHHARBOR.12a3 – Helper Inventory Tests
2. PATCHHARBOR.12b1 – Public Audit Model
3. PATCHHARBOR.12b2 – Public Audit Checks
4. PATCHHARBOR.12b3 – Public Audit CLI
5. PATCHHARBOR.12b4 – Source Public Audit Wrapper
6. PATCHHARBOR.12c1 – Environment Check Model
7. PATCHHARBOR.12c2 – Environment Check CLI
8. PATCHHARBOR.12c3 – Source Environment Wrapper

## Explicit non-goals

PATCHHARBOR.12a2 does not:

- move helper files
- modify helper behavior
- add target-side helper APIs
- change aliases
- change `c`
- change `r`
- change download runner behavior
- change export runner behavior
- change metadata validation
- change context-display behavior
- delete source-side helpers

## Acceptance for this patch

This classification is accepted when:

- every helper from PATCHHARBOR.12a1 is classified
- generic-candidate helpers are separated from source-only wrappers
- already migrated download/export helpers are not reintroduced as new PATCHHARBOR.12 migrations
- immediate next steps match `planning/milestones_migration.md`
- no helper behavior is changed
- both repositories remain clean except for this classification document
