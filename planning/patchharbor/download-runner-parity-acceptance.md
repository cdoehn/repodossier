# PATCHHARBOR.10b8 – Download Runner Parity Acceptance

This document accepts the completed source-side download runner parity test phase.

PATCHHARBOR.10b protects the current RepoDossier download patch runner contract before the migration starts introducing PatchHarbor target APIs or source-side replacement logic.

## Accepted parity areas

The following parity areas are covered:

| Step | Area | Test file |
| --- | --- | --- |
| PATCHHARBOR.10b1 | metadata validation | `tests/test_download_runner_metadata_parity.py` |
| PATCHHARBOR.10b2 | freshness checks | `tests/test_download_runner_freshness_parity.py` |
| PATCHHARBOR.10b3 | repeat detection | `tests/test_download_runner_repeat_parity.py` |
| PATCHHARBOR.10b4 | syntax failure handling | `tests/test_download_runner_syntax_parity.py` |
| PATCHHARBOR.10b5 | success lifecycle | `tests/test_download_runner_success_lifecycle_parity.py` |
| PATCHHARBOR.10b6 | failure lifecycle | `tests/test_download_runner_failure_lifecycle_parity.py` |
| PATCHHARBOR.10b7 | footer and completion output | `tests/test_download_runner_footer_parity.py` |

## Accepted current contract

The protected current contract includes:

- valid metadata is accepted before execution
- invalid metadata stops before execution
- `progress_context=false` disables the patchscript context display
- old patchscripts require confirmation before execution
- repeat detection uses the applied ledger and done-file checks
- syntax failures stop before execution
- successful scripts move to `done`
- failed scripts move to `failed`
- ZIP input keeps the original archive as the lifecycle artifact
- log files remain in Downloads
- success runs update `.applied_patch_hashes.tsv`
- failure runs do not update `.applied_patch_hashes.tsv`
- final success and failure bands remain visible
- existing terminal output is treated as compatibility-sensitive

## Explicit non-goals

PATCHHARBOR.10b does not:

- change the runner implementation
- change PatchHarbor target code
- switch `c`
- change aliases
- change export scripts
- remove the existing RepoDossier runner
- introduce target-side download runner APIs

## Readiness for PATCHHARBOR.10c

PATCHHARBOR.10c may now start target-side planning/API work.

The next phase must use these parity tests as the safety net. If a target-side API intentionally changes current behavior, that change must be documented explicitly instead of silently weakening tests.

## Acceptance checks

This phase is accepted when the source repository passes:

    python3 -m compileall tests
    python3 -m pytest tests/test_download_runner_metadata_parity.py
    python3 -m pytest tests/test_download_runner_freshness_parity.py
    python3 -m pytest tests/test_download_runner_repeat_parity.py
    python3 -m pytest tests/test_download_runner_syntax_parity.py
    python3 -m pytest tests/test_download_runner_success_lifecycle_parity.py
    python3 -m pytest tests/test_download_runner_failure_lifecycle_parity.py
    python3 -m pytest tests/test_download_runner_footer_parity.py
    python3 -m pytest tests/test_download_runner_parity_acceptance.py

Manual review should confirm that PATCHHARBOR.10b added tests only and did not migrate execution behavior.
