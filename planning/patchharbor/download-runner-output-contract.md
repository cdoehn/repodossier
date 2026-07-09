# PATCHHARBOR.10a3 – Download Runner Output Contract

This document records the current terminal output contract of the RepoDossier `c` download patch runner.

This is a documentation step only. It does not change runner behavior.

## Scope

The output contract covers the visible terminal output that a user relies on while applying a downloaded patch script or patch archive.

It covers:

- start banner
- input artifact summary
- metadata check output
- repeat check output
- freshness check output
- syntax check output
- execution output
- progress context display
- done and failed move output
- final success or failure band
- exit-code meaning

## Stable opening output

A normal run begins with the `c` runner banner.

The opening output must show:

- download directory
- done directory
- failed directory
- selected patch artifact
- selected patch script when known
- log file path
- start time

For direct `.sh` input, the patch artifact and patch script can be the same file.

For `.zip` input, the patch artifact is the `.zip` file and the patch script is the extracted `.sh` script.

## Phase heading contract

Major phases are printed as clearly separated headings.

The current source runner uses headings for:

- start
- metadata check
- repeat check
- safety or freshness check
- syntax check
- execution
- completion

The exact colors are not part of the contract. The phase meaning is part of the contract.

## Metadata output contract

The metadata phase must clearly show whether metadata validation passed or failed.

On success, the output includes:

- metadata validation was attempted
- metadata validation passed
- display metadata effects when relevant

When display metadata disables progress context, the output states that the patch script requested no progress context.

On metadata failure, the output must make clear:

- metadata validation failed
- the patch was not executed
- the log remains available

## Repeat output contract

The repeat phase reports whether the selected input was already applied.

Successful repeat check output states that the patch was not recognized as already successful.

A repeat failure must stop execution before the patch body runs.

## Freshness output contract

The freshness or safety phase reports whether the selected input is fresh enough.

For direct `.sh` input, freshness applies to the script file.

For `.zip` input, freshness applies to the original `.zip` artifact.

Freshness failure must stop execution before the patch body runs.

## Syntax output contract

The syntax phase reports the Bash syntax check command and the result.

Syntax success must be explicit.

Syntax failure must stop execution before the patch body runs.

## Execution output contract

When preflight passes, the execution phase prints that the patch script is being started with Bash.

The patch script owns its inner output.

The runner must preserve the patch script output in the terminal stream and in the run log.

## Progress context output contract

Progress context can be shown or hidden.

Progress context is hidden when:

- `--no-progress-context` is passed
- `--no-context` is passed
- `C_RUNNER_PROGRESS_CONTEXT=0` is set
- display metadata sets `progress_context=false`

When hidden, the runner still prints final status and the final success or failure band.

## Completion output contract

The completion phase must print:

- patch script exit code
- success or failure result
- destination of the moved patch artifact when a move happens
- run log location
- end time

For `.zip` input, the moved artifact is the original `.zip` file.

## Final band contract

A successful run ends with a prominent success band.

A failed run ends with a prominent failure band.

The final band is intentionally loud because it is the last thing the user sees after a long patch run.

## Exit-code contract

The runner exits with code `0` only when the selected patch lifecycle was successful.

The runner exits non-zero when:

- metadata validation fails
- repeat check rejects the input
- freshness check fails
- Bash syntax validation fails
- preflight lint fails
- patch execution fails
- lifecycle file moves fail
- an unexpected runner error occurs

## Failure diagnosability contract

A failed run must leave enough information to debug the failure.

At minimum, the output must show:

- which artifact was selected
- which script was checked or executed
- which phase failed
- whether the patch body ran
- where the run log remains

If the patch script itself exits under `set -e` without setting an explicit problem message, the patch footer should still print a generic problem line.

## Non-goals

This document does not:

- define exact ANSI color codes
- define exact line wrapping
- replace the lifecycle flow document
- change the download runner
- switch `c` to PatchHarbor
- define the future PatchHarbor output API

The next step adds tests around the inventory documents.
