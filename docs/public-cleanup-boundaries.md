# RepoDossier public cleanup boundaries

REPODOSSIER.PRIVACY2 removes public private-data leftovers from RepoDossier metadata and public-facing documentation.

## Private data boundary

Public metadata must not contain a contributor-specific GitHub namespace, surname, home directory, workstation name, local project path, town name, or personal email address.

Dedicated tests may contain reconstructed private-like fixtures when they are necessary to verify privacy scanning, secret masking, or migration safety. Those values must stay in test code and must be built from split fragments instead of stored as normal public metadata.

## Patch infrastructure boundary

RepoDossier may still contain PatchHarbor references in migration plans, developer-wrapper tests, and compatibility wrappers while the migration is being completed.

Public README metadata should describe RepoDossier itself and should not advertise PatchHarbor as a user dependency.

Misspelled pet-prefix variants of the PatchHarbor name are not part of the repository contract and should stay absent.

## Acceptance

This cleanup is accepted when:

- public GitHub metadata uses a neutral project namespace
- public metadata no longer stores the previous contributor-specific namespace or surname
- dedicated test-private fixtures remain limited to tests
- public README metadata focuses on RepoDossier
- misspelled pet-prefix PatchHarbor variants are absent
