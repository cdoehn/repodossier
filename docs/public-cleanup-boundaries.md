# RepoDossier public cleanup boundaries

## Private data boundary

Public metadata must not contain contributor-specific names, home directories, workstation names, local project paths, towns, or personal email addresses.

Dedicated tests may contain reconstructed private-like fixtures when necessary to verify privacy scanning or secret masking. Those values must stay in test code and should be assembled from fragments instead of stored as normal public metadata.

## Dependency boundary

RepoDossier source code, development helpers, tests, and documentation must not depend on unrelated sibling repositories or external project-specific command-line tools.

## Acceptance

This cleanup is accepted when public metadata uses neutral project values, private fixtures remain limited to tests, and all repository functionality can be tested from a standalone checkout.
