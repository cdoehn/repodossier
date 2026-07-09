# PATCHHARBOR.10a2 – Download Runner Lifecycle Flow

This document records the current lifecycle flow of the RepoDossier `c` download patch runner.

This is an inventory document. It does not change runner behavior.

## Scope

The lifecycle begins when the user starts the `c` runner and ends when the selected input is either left untouched, moved to the done workflow, or moved to the failed workflow.

The selected input can be either:

- a direct `.sh` patch script
- a `.zip` archive containing exactly one `.sh` patch script

The `.zip` archive is the input artifact for repeat detection, freshness checks, and done or failed moves.

## High-level lifecycle

1. Resolve download, done, and failed workflow locations.
2. Select the input patch when no explicit path was supplied.
3. If the input is a `.zip` archive, safely extract exactly one `.sh` script into a temporary directory.
4. Print start information and determine the run log name.
5. Validate metadata.
6. Apply display metadata such as `progress_context=false`.
7. Check whether the input was already applied.
8. Check freshness.
9. Run Bash syntax validation.
10. Run patch preflight linting.
11. Execute the patch unless dry-run or no-execute behavior prevents execution.
12. Capture the patch exit code.
13. Move the original input artifact to done or failed.
14. Record successful application in the applied ledger.
15. Keep the run log in the download directory.
16. Print final status and success or failure band.

## Selection phase

When no explicit input path is supplied, the runner chooses the newest eligible input from the download directory.

Eligible inputs are:

- `.sh` patch scripts
- `.zip` patch archives

Hidden files are ignored.

The selection phase must not select worktree archives or unrelated project export archives unless they are valid patch archives containing exactly one `.sh` patch script.

## ZIP extraction phase

When the selected input is a `.zip` archive, the runner extracts it to a temporary directory.

Required behavior:

- reject unsafe archive entries
- reject archives with zero `.sh` patch scripts
- reject archives with more than one `.sh` patch script
- use the extracted `.sh` script for metadata, syntax, lint, and execution checks
- use the original `.zip` archive as the lifecycle input artifact

The temporary extraction directory is cleaned up after the run.

## Metadata phase

The runner validates metadata before repeat, freshness, syntax, lint, or execution.

Metadata failure means:

- the patch script is not executed
- the input artifact is not recorded as successfully applied
- the log remains available
- failure is reported

Current metadata rules include:

- patch metadata is required
- `progress_context=false` is accepted in display metadata
- progress_context=false must not be combined with progress metadata records
- progress metadata is required unless direct Bash or disabled progress context explicitly makes it unnecessary

## Repeat phase

The runner checks whether the input artifact was already applied.

For direct `.sh` input, the script content is hashed.

For `.zip` input, the archive content is hashed.

A previously applied input is rejected unless the user explicitly confirms or the runner contract allows a deliberate repeat.

## Freshness phase

The runner checks the selected input artifact age.

Freshness applies to:

- direct `.sh` files
- `.zip` archives

The extracted temporary `.sh` file is not the freshness source.

## Syntax phase

The runner runs Bash syntax validation against the executable `.sh` script.

For `.zip` input, syntax validation runs against the extracted `.sh` script.

Syntax failure means:

- the patch is not executed
- the original input artifact is moved to the failed workflow
- the log remains available

## Preflight lint phase

The runner runs patch preflight linting before execution.

Lint failure means:

- the patch is not executed
- the original input artifact is moved to the failed workflow
- the log remains available

## Execution phase

Execution runs only after metadata, repeat, freshness, syntax, and lint checks pass.

Dry-run mode stops before execution.

No-execute behavior stops before execution when supported by the invoked runner path.

## Success lifecycle

On success:

- the original input artifact is moved to the done workflow
- the applied ledger is updated
- the log remains in the download directory
- a final success band is printed

For `.zip` input, the `.zip` file is moved to done.

## Failure lifecycle

On failure:

- the original input artifact is moved to the failed workflow when execution or preflight reached the move stage
- the applied ledger is not updated as successful
- the log remains in the download directory
- a final failure band is printed

For `.zip` input, the `.zip` file is moved to failed.

## Progress context display lifecycle

The runner can show or hide the progress context display.

The display is hidden when:

- `--no-progress-context` is passed
- `--no-context` is passed
- `C_RUNNER_PROGRESS_CONTEXT=0` is set
- display metadata sets `progress_context=false`

When the progress context is hidden, the final success or failure band still appears.

## Non-goals

This document does not:

- switch `c` to PatchHarbor
- replace the download runner
- change alias behavior
- migrate export behavior
- claim parity with a future target download runner API
- define the terminal output contract in full

The terminal output contract is documented in the next planned step.
