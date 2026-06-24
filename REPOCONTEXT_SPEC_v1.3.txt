REPOCONTEXT SPECIFICATION
Version: 1.3

PROJECT NAME
============
RepoContext

PURPOSE
=======
RepoContext creates AI-friendly exports of Git repositories.

The goal is to provide complete or summarized repository context for AI systems
such as ChatGPT, Claude, Gemini, Aider and others.

Only Git-tracked files are exported.

INSTALLATION
============

Primary installation method:

    pipx install repocontext

Supported installation methods:

    pipx install repocontext
    pip install repocontext
    pip install -e .

CLI entrypoint:

    repocontext

EXPORT MODES
============

1. Full Export

    repocontext

Output:

    full.txt

Contains:

- AI Quick Start
- repository statistics
- file summary
- repository tree
- complete source export
- warnings

2. AI Export

    repocontext --ai

Output:

    ai.txt

Contains:

1. AI Quick Start
2. Repository Statistics
3. Important Files
4. Project Documents
5. Architecture Summary
6. File Summary
7. Repository Tree
8. Symbol Index
9. Function Overview
10. Class Overview
11. Import Graph
12. Call Graph
13. Dependency Summary
14. Database Schema
15. CLI Commands
16. Test Commands
17. Configuration Summary
18. Warnings

No complete code dump.

3. Documentation Export

    repocontext --docs

Output:

    docs.txt

Contains documentation files such as:

- README.md
- ARCHITECTURE.md
- TASKS.md
- SPEC.md
- CHANGELOG.md

4. Changed Files Export

    repocontext --changed
    repocontext --changed main

Output:

    changed.txt

Contains:

- changed files
- git diff summary
- changed file contents
- warnings

GIT INTEGRATION
===============

File discovery is based on:

    git ls-files

Only Git-tracked files are exported.

GITIGNORE MANAGEMENT
====================

RepoContext automatically ensures the following files are present in .gitignore:

- full.txt
- ai.txt
- docs.txt
- changed.txt

AI QUICK START
==============

Every export begins with a short AI-oriented project summary.

Includes:

- project type
- primary language
- package manager
- test framework
- entrypoints
- project purpose

REPOSITORY STATISTICS
=====================

Includes:

- total files
- total lines
- file type counts
- estimated token count

IMPORTANT FILES
===============

Automatically ranks the most important files in the repository.

PROJECT DOCUMENTS
=================

Documentation files are prioritized and embedded into ai.txt.

Examples:

- README.md
- ARCHITECTURE.md
- TASKS.md
- SPEC.md
- CHANGELOG.md

ARCHITECTURE SUMMARY
====================

Automatically generated overview including:

- entrypoints
- core modules
- databases
- external services
- test areas

FILE SUMMARY
============

Line counts for all exported files.

REPOSITORY TREE
===============

Tree view of exported files.

SYMBOL INDEX
============

Global index of:

- functions
- classes
- symbols

FUNCTION OVERVIEW
=================

Function signatures without function bodies.

CLASS OVERVIEW
==============

Class names and inheritance information where available.

IMPORT GRAPH
============

Static dependency overview between files and modules.

CALL GRAPH
==========

Static call graph showing major relationships between functions.

DEPENDENCY SUMMARY
==================

Generated from:

- pyproject.toml
- requirements.txt

DATABASE SCHEMA
===============

Database structure extracted where possible.

Examples:

- SQLite schemas
- CREATE TABLE statements
- table summaries

CLI COMMANDS
============

Detected commands and entrypoints.

TEST COMMANDS
=============

Detected test commands and test locations.

CONFIGURATION SUMMARY
=====================

Configuration files and major configuration keys.

SUPPORTED LANGUAGES
===================

Initial support:

- Python
- Bash

SUPPORTED FILE TYPES
====================

- .py
- .sh
- .bash
- .md
- .txt
- .yaml
- .yml
- .toml
- .ini
- .cfg
- .json

Files without extensions may be included if detected as text.

BINARY FILES
============

Binary files are excluded and reported.

Examples:

- .png
- .jpg
- .pdf
- .zip
- .db
- .sqlite
- .pyc

SECRET DETECTION
================

Detect likely secrets:

- API_KEY
- TOKEN
- SECRET
- PASSWORD
- PRIVATE KEY

Values may be masked.

TOKEN ESTIMATION
================

Estimate AI context size.

CONFIGURATION FILE
==================

Optional:

    .repocontext.yml

Supports:

- include filters
- exclude filters
- secret masking
- export limits
- split settings

CORE FEATURES
=============

- Git-based file discovery
- Full export
- AI export
- Documentation export
- Changed export
- Repository statistics
- Important file ranking
- Function discovery
- Class discovery
- Symbol index
- Import graph
- Call graph
- Dependency detection
- Database schema extraction
- Binary detection
- Secret detection
- Warning generation
- Token estimation
- Split exports
- Include/exclude filters

FUTURE EXTENSIONS
=================

Additional language support:

- C
- C++
- Rust
- Go
- Java
- Kotlin
- JavaScript
- TypeScript

END OF SPECIFICATION
