# PatchHarbor Dev-Script Migration Inventory

This document records the current RepoDossier development scripts before they are extracted into a separate PatchHarbor/dev-tools repository.

Scope of this first migration step:

- source repository only
- no target repository changes
- no deletion or moving of existing RepoDossier scripts
- no private local paths, names, email addresses, or machine identifiers
- deterministic repository-relative inventory

The intended migration style is incremental: first inventory, then target skeleton, then extraction/generalization, then thin RepoDossier wrappers.

## Source Inventory

| Path | Kind | Lines | Current role | Migration bucket | RepoDossier-specific markers |
| --- | --- | ---: | --- | --- | --- |
| scripts/dev/audit_public_repo.py | .py | 136 | release/privacy audit | candidate: generic with policy config | RepoDossier |
| scripts/dev/check_dev_environment.py | .py | 165 | local environment check | candidate: generic with per-repo checks | RepoDossier, repodossier |
| scripts/dev/install_aliases.sh | .sh | 139 | local alias installer | candidate: generic installer, repo-specific config | RepoDossier, repodossier, REPODOSSIER_REPO |
| scripts/dev/lint_patch_script.py | .py | 240 | patch script linter | candidate: generic core | RepoDossier |
| scripts/dev/patch-rules.md | .md | 1021 | human workflow rules | split: generic rules plus repo overlay | RepoDossier, repodossier, full.txt, ai.txt |
| scripts/dev/patch-workflow-rules.json | .json | 218 | machine workflow rules | split: generic rules plus repo overlay | RepoDossier, repodossier |
| scripts/dev/patch-workflow-rules.schema.json | .json | 114 | workflow rules schema | candidate: generic schema | RepoDossier, repodossier |
| scripts/dev/r.sh | .sh | 5 | short export runner wrapper | keep as thin RepoDossier wrapper first | repodossier |
| scripts/dev/repo_patch_helper.py | .py | 714 | patch helper library/CLI | candidate: generic core | RepoDossier |
| scripts/dev/run_latest_download_patch.sh | .sh | 702 | download patch runner | candidate: generic runner with adapters | RepoDossier, repodossier, REPODOSSIER_REPO, .repodossier |
| scripts/dev/run_repodossier_exports.sh | .sh | 249 | export runner | split: generic runner plus RepoDossier command config | RepoDossier, repodossier, full.txt, ai.txt, docs.txt, changed.txt |
| scripts/dev/show_progress_context.py | .py | 561 | milestone progress renderer | candidate: generic core | RepoDossier, repodossier |
| scripts/dev/validate_patch_metadata.py | .py | 299 | patch metadata validator | candidate: generic core | repodossier |
| scripts/dev/validate_patch_workflow_rules.py | .py | 128 | workflow rule validator | candidate: generic core | RepoDossier |
| scripts/validate_pipx_release.sh | .sh | 209 | RepoDossier release validation | stay in RepoDossier unless made product-specific plugin | RepoDossier, repodossier, repocontext, full.txt, ai.txt, docs.txt ... |

## Existing Test Coverage

| Path | Status | Notes |
| --- | --- | --- |
| tests/test_audit_public_repo.py | present | public repo audit helper |
| tests/test_check_dev_environment.py | present | environment check rendering |
| tests/test_dev_alias_installer.py | present | alias installer behavior and managed shell block |
| tests/test_dev_r_runner_modes.py | present | r runner mode aliases and dry-run behavior |
| tests/test_download_patch_runner.py | present | download patch runner behavior |
| tests/test_lint_patch_script.py | present | patch script lint rules |
| tests/test_patch_metadata.py | present | patch metadata parser and validator |
| tests/test_patch_workflow_rules_schema.py | present | workflow rules schema validity |
| tests/test_repo_patch_helper_script.py | present | repo patch helper behavior |
| tests/test_repodossier_export_runner.py | present | RepoDossier export runner behavior |
| tests/test_pipx_release_validation_script.py | present | release validation script |

## Initial Generalization Candidates

### Likely generic core

- patch metadata parsing and validation
- patch script linting rules
- workflow rules schema validation
- repository patch helper primitives
- progress/context rendering
- download patch runner mechanics
- local environment checks with configurable requirements

### RepoDossier-specific behavior to parameterize

- export filenames such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt`
- CLI commands such as `repodossier full`, `repodossier export-ai`, `repodossier export-docs`, and `repodossier changed`
- legacy `repocontext` compatibility checks
- environment variables and shell blocks currently named around RepoDossier
- public release validation for the RepoDossier product package

### Compatibility boundary

- Keep `c` and `r` workflows working while PatchHarbor becomes the source of truth.
- Prefer thin RepoDossier wrappers after PatchHarbor has a tested target CLI.
- Do not remove or destructively rewrite RepoDossier scripts before the target repository is independently green.

## Proposed Small-Step Migration Order

1. Inventory existing scripts and tests in RepoDossier.
2. Create a PatchHarbor target repository skeleton with tests and neutral naming.
3. Copy one generic, low-risk component into PatchHarbor with tests.
4. Parameterize RepoDossier-specific names through config or wrapper arguments.
5. Add PatchHarbor `c` and `r` entrypoints while keeping RepoDossier wrappers.
6. Switch RepoDossier wrappers to delegate to PatchHarbor once target tests are green.
7. Remove duplicated source-repo implementations only after compatibility checks pass.

## Non-Goals For This Step

- no Git history rewrite
- no `git filter-repo` execution
- no target repository creation
- no script deletion
- no alias installation
- no machine-specific tracked configuration
