# Security Policy

RepoDossier is a local CLI tool for creating repository exports for AI-assisted development. Because these exports can contain source code and documentation, security and privacy issues are taken seriously.

## Supported versions

Security fixes are handled on the current main branch.

## Reporting a vulnerability

Please do not disclose security vulnerabilities publicly before they have been reviewed.

Preferred reporting options:

1. Use GitHub's private vulnerability reporting or security advisory feature if it is available for this repository.
2. If private reporting is not available, open a minimal public issue that says you want to report a security issue, but do not include exploit details, credentials, private data, or sensitive files.

Useful information to include privately:

- affected RepoDossier version or commit
- operating system and Python version
- commands used
- expected behavior
- actual behavior
- a minimal reproduction using fake data only

## Secret handling

RepoDossier includes best-effort secret detection and masking for common assignment-style values such as API keys, tokens, secrets, and passwords.

This feature is not a complete security scanner. Before publishing or sharing generated exports, review them manually and confirm that no private credentials, personal data, proprietary data, or sensitive database contents are included.

## Scope

Examples of security-relevant issues:

- generated exports expose values that should have been masked
- generated exports include files that should be excluded
- project code is imported or executed during static analysis
- unsafe handling of repository paths or output paths
- database contents are exported instead of schema metadata

Out of scope:

- vulnerabilities in third-party dependencies unless RepoDossier directly exposes or worsens the issue
- secrets committed to a user's own repository before running RepoDossier
- malicious repositories intentionally crafted to confuse an AI assistant after export
