# REPODOSSIER ARCHITECTURE

## Goal

RepoDossier generates AI-friendly repository exports from Git repositories.

The architecture is designed around a simple pipeline:

    Git Repository
          |
          v
    File Discovery
          |
          v
    Analysis Layer
          |
          v
    Export Generators
          |
          v
    full.txt / ai.txt / docs.txt / changed.txt

---

# High-Level Architecture

repodossier/
├── cli.py
├── config.py
├── git.py
├── filetypes.py
├── scanner.py
├── statistics.py
├── symbols.py
├── imports.py
├── callgraph.py
├── schema.py
├── secrets.py
├── ranking.py
├── exporters/
│   ├── full.py
│   ├── ai.py
│   ├── docs.py
│   └── changed.py
└── models.py

---

# Module Responsibilities

## cli.py

Responsibilities:

- command line interface
- argument parsing
- mode selection
- orchestration

Commands:

    repodossier
    repodossier --ai
    repodossier --docs
    repodossier --changed

---

## config.py

Responsibilities:

- load .repodossier.yml
- merge defaults
- validate configuration

---

## git.py

Responsibilities:

- repository discovery
- git ls-files
- branch detection
- commit detection
- changed file detection

Outputs:

- tracked files
- repository metadata

---

## filetypes.py

Responsibilities:

- text file detection
- binary file detection
- language detection

Supported:

- Python
- Bash
- Markdown
- JSON
- YAML
- TOML
- INI

---

## scanner.py

Responsibilities:

- read files
- line counting
- token estimation
- content loading

Outputs:

- file metadata
- file contents

---

## statistics.py

Responsibilities:

- repository statistics
- language statistics
- line counts
- token counts

Outputs:

- repository summary

---

## symbols.py

Responsibilities:

Python:

- classes
- functions
- methods

Bash:

- functions

Outputs:

- symbol index
- function overview
- class overview

---

## imports.py

Responsibilities:

Python:

- import statements
- module dependencies

Outputs:

- import graph

---

## callgraph.py

Responsibilities:

Python:

- function calls
- method calls

Bash:

- function invocation detection

Outputs:

- static call graph

---

## schema.py

Responsibilities:

- SQLite schema extraction
- CREATE TABLE detection
- table summary generation

Outputs:

- database schema summary

---

## secrets.py

Responsibilities:

Detect:

- API_KEY
- TOKEN
- SECRET
- PASSWORD
- PRIVATE KEY

Outputs:

- warnings
- masked content

---

## ranking.py

Responsibilities:

Calculate:

- important files
- central modules
- entrypoints

Factors:

- import graph centrality
- call graph centrality
- documentation relevance

Outputs:

- important file ranking

---

# Export Layer

## exporters/full.py

Generates:

    full.txt

Contains:

- AI Quick Start
- statistics
- file summary
- repository tree
- full source dump
- warnings

---

## exporters/ai.py

Generates:

    ai.txt

Contains:

- AI Quick Start
- repository statistics
- important files
- project documents
- architecture summary
- symbol index
- function overview
- class overview
- import graph
- call graph
- dependency summary
- database schema
- CLI commands
- test commands
- configuration summary
- warnings

No full source code.

---

## exporters/docs.py

Generates:

    docs.txt

Contains documentation files only. It extracts Git-tracked documentation-like text files and excludes generated RepoDossier export files.

---

## exporters/changed.py

Generates:

    changed.txt

Contains:

- changed files
- diff summary
- changed contents

---

# Data Flow

1. Discover repository

    git.py

2. Collect files

    scanner.py

3. Build statistics

    statistics.py

4. Extract symbols

    symbols.py

5. Build import graph

    imports.py

6. Build call graph

    callgraph.py

7. Extract schemas

    schema.py

8. Detect secrets

    secrets.py

9. Rank files

    ranking.py

10. Generate export

    exporters/*

---

# Packaging

Python package

Installation:

    pipx install repodossier

CLI entrypoint:

    repodossier

---

# Future Extensions

Potential plugins:

- Java parser
- Rust parser
- Go parser
- TypeScript parser
- C/C++ parser

Potential exports:

- architecture.txt
- dependencies.txt
- security.txt

