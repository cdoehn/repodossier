# PATCHHARBOR.14a2 – Replaced Logic Map


## PATCHHARBOR.14 cleanup ordered anchor

This anchor keeps cleanup-safety tests tied to the intended 14b execution order.

1. PATCHHARBOR.14b1 – Remove obsolete metadata helper wrapper
2. PATCHHARBOR.14b2 – Remove obsolete lint wrapper
3. PATCHHARBOR.14b3 – Remove obsolete runner helper part 1
4. PATCHHARBOR.14b4 – Remove obsolete runner helper part 2

This document maps RepoDossier source-side development script logic to the PatchHarbor target implementation that now replaces, supports, or deliberately does not replace it.

`planning/milestones_migration.md` is the operative plan. PATCHHARBOR.14a2 is source-only documentation and does not delete or edit source scripts.

## Map status vocabulary

| Status | Meaning |
| --- | --- |
| replaced | PatchHarbor has a target implementation and a source wrapper can eventually be removed or simplified after safety tests |
| wrapped | RepoDossier source wrapper still provides compatibility over PatchHarbor target behavior |
| source-policy | source-side data/policy remains intentionally in RepoDossier |
| blocked | no deletion until a later model, wrapper, or acceptance test exists |
| high-risk | cleanup must be split into smaller patches and cannot be removed only by inference |

## Replaced logic overview

| Source logic area | Source file(s) | PatchHarbor replacement | Status | Cleanup direction |
| --- | --- | --- | --- | --- |
| patch metadata validation | `scripts/dev/validate_patch_metadata.py` | `src/patchharbor/metadata.py`, `src/patchharbor/runner_preflight.py`, runner preflight tests | replaced | candidate for 14b1 after cleanup safety tests prove no source references require the legacy helper |
| patch lifecycle runner | `scripts/dev/run_latest_download_patch.sh` | `src/patchharbor/runner_core.py`, `src/patchharbor/runner_lifecycle.py`, `src/patchharbor/runner_preflight.py`, `src/patchharbor/runner_display.py` | wrapped / high-risk | cleanup only in small parts; keep `c` compatibility until alias/docs are updated |
| PatchHarbor source wrapper | `scripts/dev/run_patchharbor_patch.sh` | PatchHarbor CLI `run-script` and runner modules | wrapped | keep as source-side bridge for now |
| shell/script linting | `scripts/dev/lint_patch_script.py` | `src/patchharbor/patch_lint.py`, `src/patchharbor/patch_lint_api.py`, `src/patchharbor/patch_lint_rules.py`, CLI `lint-script` | replaced | removed by 14b2 after cleanup safety tests |
| workflow rule validation | `scripts/dev/validate_patch_workflow_rules.py`, `scripts/dev/patch-workflow-rules.json`, `scripts/dev/patch-workflow-rules.schema.json` | `src/patchharbor/workflow_rules.py`, `src/patchharbor/workflow_validation.py` | source-policy / blocked | keep until rule data ownership and schema compatibility are explicitly migrated |
| public repository audit | `scripts/dev/audit_public_repo.py` | `src/patchharbor/public_audit.py`, `src/patchharbor/public_audit_checks.py`, CLI `audit-public` | wrapped | keep source wrapper until source workflow docs point to target command |
| environment doctor | `scripts/dev/check_dev_environment.py` | `src/patchharbor/environment_check.py`, CLI `check-env` | wrapped | keep source wrapper until source workflow docs point to target command |
| export runner planning | `scripts/dev/r.sh`, `scripts/dev/run_repodossier_exports.sh` | `src/patchharbor/export_model.py`, `src/patchharbor/export_planning.py`, `src/patchharbor/export_display.py` | wrapped | keep source-specific export wrapper |
| download candidate migration artifact | `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` | final source runner wrapper and PatchHarbor runner | replaced if unreferenced | removed by PATCHHARBOR.14b3 after safety tests proved no active wrapper references |
| progress/context display | `scripts/dev/show_progress_context.py` | partially covered by runner display and metadata/context contracts | blocked / display-sensitive | do not delete because display-only instability must not block functional cleanup, but responsibilities must be mapped first |
| alias installer | `scripts/dev/install_aliases.sh` | no target replacement | source-policy | keep source-side |
| human patch rules | `scripts/dev/patch-rules.md` | no full target replacement | source-policy | keep source-side |
| repository patch helper | `scripts/dev/repo_patch_helper.py` | no complete target replacement | high-risk / blocked | keep until a dedicated replaced-logic map and tests exist |
| release validation | `scripts/validate_pipx_release.sh` | package smoke and acceptance tests in PatchHarbor are related but not equivalent | source-policy | keep; it validates RepoDossier release flow rather than PatchHarbor internals |

## Detailed replacement map

### Metadata helper replacement

Source path:

    scripts/dev/validate_patch_metadata.py

PatchHarbor replacement paths:

    src/patchharbor/metadata.py
    src/patchharbor/runner_preflight.py
    src/patchharbor/runner_core.py

Evidence:

- Patch metadata is parsed and validated by target modules.
- Runner preflight consumes metadata before execution.
- Source runner adoption has already used PatchHarbor preflight behavior.

Deletion gate:

- PATCHHARBOR.14a3 must prove no active source alias or wrapper invokes `scripts/dev/validate_patch_metadata.py` directly.
- Existing metadata tests must pass in the target.
- `c` workflow must continue to reject malformed metadata.

Status: replaced, candidate for PATCHHARBOR.14b1.

### Lint helper replacement

Source path:

    scripts/dev/lint_patch_script.py

PatchHarbor replacement paths:

    src/patchharbor/patch_lint.py
    src/patchharbor/patch_lint_api.py
    src/patchharbor/patch_lint_rules.py

Evidence:

- PatchHarbor has a `lint-script` CLI.
- Patch lint API and CLI tests exist.
- Lint behavior is generic and target-side.

Deletion gate:

- PATCHHARBOR.14a3 must prove no active source wrapper calls the old lint helper.
- Source docs/tests must refer to `patchharbor lint-script` or the supported wrapper path.
- Lint findings must remain blocking where required.

Status: replaced, candidate for PATCHHARBOR.14b2.

### Download runner replacement

Source paths:

    scripts/dev/run_latest_download_patch.sh
    scripts/dev/run_patchharbor_patch.sh
    scripts/dev/run_latest_download_patch_patchharbor_candidate.sh

PatchHarbor replacement paths:

    src/patchharbor/runner_core.py
    src/patchharbor/runner_lifecycle.py
    src/patchharbor/runner_preflight.py
    src/patchharbor/runner_display.py
    src/patchharbor/runner_status.py

Evidence:

- PatchHarbor runner core and lifecycle tests exist.
- Source-side adoption and wrapper compatibility tests exist.
- Packaging hardening now verifies target CLI availability.

Deletion gate:

- PATCHHARBOR.14a3 must prove `c` alias behavior remains intact.
- The final source wrapper must be the only active runner bridge.
- The candidate artifact may be removed first if unreferenced.
- Old monolithic logic inside `run_latest_download_patch.sh` must only be removed after wrapper parity proves replacement.

Status: wrapped and high-risk. Candidate artifact may be 14b3; runner helper cleanup may be 14b4.

### Workflow-rule validator replacement

Source paths:

    scripts/dev/validate_patch_workflow_rules.py
    scripts/dev/patch-workflow-rules.json
    scripts/dev/patch-workflow-rules.schema.json

PatchHarbor related paths:

    src/patchharbor/workflow_rules.py
    src/patchharbor/workflow_validation.py

Evidence:

- PatchHarbor workflow-rule modules and tests exist.
- Source rules still represent source policy and rule data.

Deletion gate:

- A later patch must decide rule data ownership.
- Rule IDs must not be guessed or renamed.
- Schema compatibility tests must prove the target accepts current source rule data.

Status: blocked and source-policy. Keep for now.

### Public audit wrapper replacement

Source path:

    scripts/dev/audit_public_repo.py

PatchHarbor replacement paths:

    src/patchharbor/public_audit.py
    src/patchharbor/public_audit_checks.py

Target command:

    patchharbor audit-public

Evidence:

- Public audit model, checks, and CLI exist.
- Source public audit wrapper uses PatchHarbor additively.

Deletion gate:

- Source workflow docs must point to the target command or explicitly retain the source wrapper.
- Safety tests must prove public audit still rejects private/local values.
- Historical/source-specific pattern handling must remain correct.

Status: wrapped. Keep until docs and workflow are updated.

### Environment wrapper replacement

Source path:

    scripts/dev/check_dev_environment.py

PatchHarbor replacement paths:

    src/patchharbor/environment_check.py

Target command:

    patchharbor check-env

Evidence:

- Environment check model and CLI exist.
- Source wrapper uses PatchHarbor model additively.
- Packaging acceptance includes `check-env` smoke.

Deletion gate:

- Source workflow docs must point to the target command or explicitly retain the source wrapper.
- Required-vs-optional behavior must remain compatible.
- Safety tests must prove no active docs rely on the old source command as the only path.

Status: wrapped. Keep until docs and workflow are updated.

### Export runner replacement

Source paths:

    scripts/dev/r.sh
    scripts/dev/run_repodossier_exports.sh

PatchHarbor replacement paths:

    src/patchharbor/export_model.py
    src/patchharbor/export_planning.py
    src/patchharbor/export_display.py

Evidence:

- Export model/planning/display modules exist.
- Source export wrapper smoke tests exist.
- The source runner uses target planning additively.

Deletion gate:

- Do not delete source export wrapper in 14b.
- RepoDossier export commands are source-specific and still need a source wrapper.
- `r` compatibility must remain intact.

Status: wrapped and source-specific. Keep.

### Context display replacement

Source path:

    scripts/dev/show_progress_context.py

PatchHarbor related paths:

    src/patchharbor/runner_display.py
    src/patchharbor/metadata.py

Evidence:

- Runner display exists target-side.
- Metadata can express `progress_context=false`.
- Display-only tests are not cleanup blockers.

Deletion gate:

- Functional context metadata handling must remain intact.
- Exact display layout must not be treated as a blocker.
- Responsibilities must be separated between metadata interpretation and terminal rendering.

Status: blocked / display-sensitive. Keep for now.

## Cleanup order implied by this map

The 14b cleanup should stay conservative:

1. PATCHHARBOR.14b1 – remove or replace the obsolete metadata helper wrapper only after 14a3 safety tests.
2. PATCHHARBOR.14b2 – remove or replace the obsolete lint wrapper only after references are updated.
3. PATCHHARBOR.14b3 – remove the obsolete download candidate artifact if unreferenced.
4. PATCHHARBOR.14b4 – remove old download runner logic only in the smallest possible patch while keeping `c` green.

Do not jump directly to deleting high-risk files.

## Safety requirements for PATCHHARBOR.14a3

The cleanup safety tests must check:

- every planned deletion candidate has a mapped replacement
- no active alias points at a deleted path
- no active source wrapper imports or executes a deleted path
- no active README or workflow doc uses a deleted path as current guidance
- target PatchHarbor command still exists for each replaced command
- `c` and `r` compatibility paths remain intact
- display-only output layout tests are skipped or separated from functional cleanup tests

## Non-goals for PATCHHARBOR.14a2

This patch does not:

- delete source scripts
- edit source scripts
- change aliases
- change `c`
- change `r`
- change PatchHarbor target files
- change package metadata
- decide final deletion of high-risk helpers
- add cleanup safety tests
- add display-only assertions

## Acceptance for this patch

PATCHHARBOR.14a2 is accepted when:

- every 14a1 cleanup candidate has a replacement or blocker mapped
- first 14b candidates are ordered conservatively
- high-risk runner and repository helper logic are explicitly not removed yet
- workflow-rule and policy files are not misclassified as safe deletion targets
- target PatchHarbor repository remains unchanged


## PATCHHARBOR.14b1 applied

- `scripts/dev/validate_patch_metadata.py` was removed as an obsolete metadata helper wrapper.
- `scripts/dev/run_latest_download_patch.sh` calls `scripts/dev/lint_patch_script.py --metadata-only` for `c` metadata checks.
- `scripts/dev/lint_patch_script.py` keeps temporary metadata compatibility until PATCHHARBOR.14b2 removes the obsolete lint wrapper.


## PATCHHARBOR.14b2 applied

- `scripts/dev/lint_patch_script.py` was removed as an obsolete lint wrapper.
- `scripts/dev/run_latest_download_patch.sh` calls PatchHarbor `lint-script` for dry-run preflight linting.
- `scripts/dev/run_latest_download_patch.sh` keeps internal metadata validation for `c` compatibility.


## PATCHHARBOR.14b3 applied

- `scripts/dev/run_latest_download_patch_patchharbor_candidate.sh` was removed as a historical candidate artifact.
- `scripts/dev/run_latest_download_patch.sh` remains the productive `c` runner.
- `scripts/dev/run_patchharbor_patch.sh` remains the source-side PatchHarbor wrapper.
- No alias, `c`, `r`, export wrapper, or target PatchHarbor file was changed by this cleanup step.
