# REPODOSSIER ARCHITECTURE

## Goal

RepoDossier generates deterministic, AI-friendly repository exports from Git repositories.

The current architecture has two layers:

1. The established CLI/exporter pipeline that still writes the user-facing Markdown-oriented files: `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt`.
2. The Milestone 3 structured export-model layer centered on `RepositoryExport`.

The structured model is now the internal target architecture for future renderer work. The existing Markdown exporters remain compatible while the renderer migration is done incrementally.

---

## Current Pipeline

RepoDossier currently follows this practical pipeline:

~~~text
CLI command
    |
    v
Repository discovery and configuration
    |
    v
Git-tracked file discovery / changed-file discovery
    |
    v
Scanner and file metadata collection
    |
    v
Static analyzers
    |
    v
Structured RepositoryExport model
    |
    v
Markdown-oriented legacy exporters and renderer helpers
    |
    v
full.txt / ai.txt / docs.txt / changed.txt
~~~

Important boundary:

- Scanner, Git, config, and analyzers collect data.
- `RepositoryExport` is the structured internal model.
- Renderers and exporters should render data; they should not grow new scanner, Git, or analyzer logic.
- The full Markdown migration is Milestone 4.
- XML output is Milestone 5.

---

## CLI Entry Points

RepoDossier exposes these command-line entry points:

~~~text
repodossier
repocontext
python -m repodossier
python -m repocontext
~~~

`repodossier` is the current command.

`repocontext` is kept as a temporary legacy compatibility alias and delegates to the same CLI implementation.

Main entry modules:

- `src/repodossier/cli.py`
- `src/repodossier/__main__.py`
- `src/repocontext/cli.py`
- `src/repocontext/__main__.py`

---

## Main Package Layout

~~~text
src/
├── repocontext/
│   ├── __init__.py
│   ├── __main__.py
│   └── cli.py
└── repodossier/
    ├── cli.py
    ├── config.py
    ├── git.py
    ├── gitignore.py
    ├── scanner.py
    ├── models.py
    ├── dependencies.py
    ├── schema.py
    ├── secrets.py
    ├── ranking.py
    ├── symbols.py
    ├── import_graph.py
    ├── call_graph.py
    ├── changed.py
    ├── changed_command.py
    ├── changed_exporter.py
    ├── export_model*.py
    ├── exporters/
    │   ├── full.py
    │   ├── ai.py
    │   └── docs.py
    └── renderers/
        └── markdown.py
~~~

---

## Module Responsibilities

### `repodossier.cli`

Responsibilities:

- parse command-line arguments
- select export mode
- load configuration
- find repository root
- dispatch to export commands
- preserve `repodossier` and `repocontext` compatibility

Main user-facing commands:

~~~text
repodossier full
repodossier export-ai
repodossier export-docs
repodossier changed
repodossier info
~~~

---

### `repodossier.config`

Responsibilities:

- load `.repodossier.yml`, `.repodossier.yaml`, or `.repodossier.toml`
- accept legacy `.repocontext.*` config files as fallback
- parse include and exclude rules
- parse export limits
- parse split-export settings
- apply configured filtering and limits to file metadata

---

### `repodossier.git`

Responsibilities:

- discover repository root
- list Git-tracked files
- read branch, commit, and dirty metadata
- collect changed files and diffs
- provide stable Git metadata for exports and model builders

---

### `repodossier.gitignore`

Responsibilities:

- keep generated export files ignored
- update `.gitignore` idempotently
- protect the repository from self-referential export artifacts

Generated files normally ignored:

~~~text
full.txt
ai.txt
docs.txt
changed.txt
~~~

---

### `repodossier.scanner`

Responsibilities:

- scan Git-tracked files
- read text file contents
- detect binary files
- count lines
- estimate tokens
- assign language labels through the central language detector
- return `FileInfo` objects

The scanner reads project files but does not execute project code.

---

### `repodossier.models`

Responsibilities:

- hold legacy/shared data structures such as `FileInfo`
- provide data used by scanner, exporters, and the export-model bridge

---

### `repodossier.languages`

Responsibilities:

- central deterministic language detection
- extension mapping
- known filename detection
- shebang detection
- conservative content heuristics
- Markdown code-fence language mapping

Language detection currently supports common repository formats including Python, Bash/Shell, Markdown, JSON, YAML, TOML, INI, TypeScript, JavaScript, HTML, CSS, Java, C, C++, and C#.

---

### `repodossier.dependencies`

Responsibilities:

- statically detect Python dependency metadata
- parse `pyproject.toml`
- parse requirements files
- classify runtime, optional, development, and unknown dependencies
- render dependency sections for current Markdown exports
- provide data that can be represented in structured reports

---

### `repodossier.schema`

Responsibilities:

- detect database/schema files
- read SQLite schema metadata without exporting table contents
- parse SQL `CREATE TABLE` statements best-effort
- report tables, columns, indexes, foreign-key relationships, and warnings

RepoDossier does not execute migrations and does not export database rows.

---

### `repodossier.secrets`

Responsibilities:

- detect common credential-like assignments
- mask potential secrets before export files are written
- provide summary information for generated exports
- prevent obvious unmasked secrets from leaking into shareable output

Secret detection is best-effort and does not replace manual review.

---

### `repodossier.symbols`

Responsibilities:

- statically extract Python symbols
- statically extract Bash functions
- provide symbol information for export sections and graph analysis

Project code is parsed, not imported or executed.

---

### `repodossier.import_graph`

Responsibilities:

- statically analyze Python imports
- distinguish local, external, unresolved, and analysis-error imports
- provide local dependency graph information for full and AI exports
- support call-graph resolution

---

### `repodossier.call_graph`

Responsibilities:

- statically analyze Python calls
- represent internal, external, ambiguous, and unresolved calls
- use import graph and symbol information where available
- avoid pretending dynamic calls are fully resolvable

---

### `repodossier.bash_symbols` and `repodossier.bash_call_graph`

Responsibilities:

- detect Bash and shell functions
- provide simple conservative Bash call relationships
- avoid executing shell scripts

---

### `repodossier.ranking`

Responsibilities:

- rank important files for AI exports
- combine entrypoint, import-graph, call-graph, documentation, and structural signals
- exclude generated RepoDossier export files

---

## Structured Export Model Layer

Milestone 3 introduced the structured export-model layer.

The central model is `RepositoryExport`.

Primary modules:

| Module | Purpose |
| --- | --- |
| `export_model.py` | Core dataclasses and validation |
| `export_model_builder.py` | Build model data from `FileEntry` objects and scanner `FileInfo` data |
| `export_model_factory.py` | Central factory for finalized `RepositoryExport` objects |
| `export_model_finalize.py` | Refresh derived summary and tree data |
| `export_model_summary.py` | Build export statistics and language statistics |
| `export_model_tree.py` | Build deterministic repository tree entries |
| `export_model_reports.py` | Create structured report placeholders |
| `export_model_serialization.py` | Convert model objects to plain dictionaries |
| `export_model_deserialization.py` | Restore model objects from dictionaries and JSON |
| `export_model_snapshot.py` | Stable JSON, fingerprint, and snapshot helpers |
| `export_model_manifest.py` | Stable export manifest |
| `export_model_inventory.py` | Stable file inventory |
| `export_model_view.py` | Section-oriented view helpers |
| `export_model_contract.py` | Contract checks for required model sections and API symbols |
| `export_model_audit.py` | Internal consistency checks |
| `export_model_readiness.py` | End-to-end readiness status |
| `export_model_roundtrip.py` | Serialization roundtrip checks |
| `export_model_selftest.py` | Built-in model selftest |
| `export_model_api.py` | Public facade for model helpers |

---

## `RepositoryExport`

`RepositoryExport` is the internal source of truth for future renderer work.

It contains:

- repository metadata
- effective configuration summary
- export summary
- language statistics
- repository tree
- exported files
- omitted files
- truncated files
- warnings
- dependency report
- database schema report
- secret detection summary
- symbol index
- import graph report
- call graph report
- test map placeholder
- recent commit placeholder

Renderer code should be able to consume `RepositoryExport` without knowing scanner, Git, or analyzer details.

---

## Scanner-to-Model Bridge

`export_model_builder.build_repository_export_from_scan(...)` bridges the existing scanner layer into the structured model.

It can:

- scan a real repository through `RepositoryScanner`
- accept pre-scanned `FileInfo` objects for tests or adapters
- convert `FileInfo` into structured `FileEntry` objects
- collect Git metadata when requested
- preserve file content or build a metadata-only model
- classify binary/skipped/error files as omitted entries
- finalize summary and repository tree through the model factory

This bridge is intentionally not a renderer. It builds data; later renderer milestones decide how to present it.

---

## Export Reports

Structured report areas are available for:

- dependencies
- database schema
- secret detection
- symbol index
- import graph
- call graph
- test map
- recent commits

Some reports are currently placeholders or adapters around existing analysis data. They exist so later milestones can extend the model without another fundamental redesign.

---

## Current Export Layer

The current user-facing exports are still Markdown-oriented.

### `repodossier.exporters.full`

Generates `full.txt`.

Current responsibilities include:

- full-export context creation
- repository statistics
- file summary
- repository tree
- dependency section
- database schema section
- source export
- warnings
- symbol/import/call graph sections
- secret masking safety integration

This module still contains legacy Markdown rendering logic. It remains functional while the MarkdownRenderer migration is deferred to Milestone 4.

---

### `repodossier.exporters.ai`

Generates `ai.txt`.

Current responsibilities include:

- compact AI context
- architecture summary
- important files
- dependencies
- database schema summary
- symbol index
- import graph
- call graph
- notes and warnings

---

### `repodossier.exporters.docs`

Generates `docs.txt`.

Current responsibilities include:

- documentation-only file selection
- documentation summary
- extracted documentation contents
- warnings

---

## exporters/docs.py

Generates:

    docs.txt

Contains documentation files only. It extracts Git-tracked documentation-like text files and excludes generated RepoDossier export files.

This heading is kept intentionally because documentation regression tests assert the concrete legacy architecture heading while the surrounding document now describes the current RepoDossier export-model architecture.

---

### `repodossier.changed_exporter`

Generates `changed.txt`.

Current responsibilities include:

- changed-file summary
- Git diff context
- changed file contents
- deleted-file entries
- binary/skipped-file entries
- optional Bash call-graph context
- secret masking safety integration

---

## Renderer Direction

`src/repodossier/renderers/markdown.py` exists as the renderer direction for structured output.

Current reality:

- Existing exports remain compatible and Markdown-oriented.
- `RepositoryExport` is ready as the internal data model.
- Full Markdown rendering from `RepositoryExport` is not yet the default export pipeline.
- Milestone 4 should migrate Markdown rendering to consume `RepositoryExport`.
- Milestone 5 should add XML rendering from the same model.

Expected future renderer boundary:

~~~text
RepositoryExport
      |
      v
Renderer
      |
      +-- Markdown
      +-- XML
      +-- later formats
~~~

---

## Output Writer and Split Exports

`repodossier.output_writer` and split helpers are responsible for:

- writing complete export files
- optionally writing `.partXX` split files
- preserving deterministic output names
- avoiding partial writes where possible

Split export behavior applies to supported export commands such as full, AI, docs, and changed exports.

---

## Data Flow by Command

### `repodossier full`

~~~text
CLI
  -> repository discovery
  -> config loading
  -> Git-tracked file discovery
  -> scanner FileInfo collection
  -> dependencies/schema/symbol/import/call analysis
  -> current full Markdown exporter
  -> full.txt and ai.txt where applicable
~~~

The structured model can be built from scanner data, but the full Markdown migration is still a separate Milestone 4 task.

---

### `repodossier export-ai`

~~~text
CLI
  -> repository discovery
  -> config loading
  -> scanner and analysis data
  -> important-file ranking
  -> compact AI Markdown exporter
  -> ai.txt
~~~

---

### `repodossier export-docs`

~~~text
CLI
  -> repository discovery
  -> config loading
  -> documentation file selection
  -> docs Markdown exporter
  -> docs.txt
~~~

---

### `repodossier changed`

~~~text
CLI
  -> repository discovery
  -> changed-file discovery
  -> optional branch comparison
  -> changed file scans
  -> diff collection
  -> changed Markdown exporter
  -> changed.txt
~~~

Changed export is Git-diff based and can include untracked, non-ignored files where supported.

---

## Determinism and Safety Rules

RepoDossier is designed around these rules:

- deterministic output where practical
- stable sorting for paths and reports
- no project-code execution during analysis
- static parsing instead of imports
- conservative classification when analysis is uncertain
- generated exports are local artifacts, not source files
- generated exports should normally stay uncommitted
- potential secrets are masked before shareable exports are written

---

## Tests and Regression Coverage

Important test groups:

| Area | Tests |
| --- | --- |
| CLI and aliases | `tests/test_cli.py`, `tests/test_repodossier_cli_alias.py`, `tests/test_release_smoke_cli.py` |
| scanner | `tests/test_scanner.py` |
| language detection | `tests/test_language_detection*.py` |
| full export | `tests/test_full_exporter*.py` |
| AI export | `tests/test_ai_exporter*.py` |
| docs export | `tests/test_docs_exporter.py`, `tests/test_cli_docs_export.py` |
| changed export | `tests/test_changed*.py` |
| export model | `tests/test_export_model*.py` |
| scanner-to-model integration | `tests/test_export_model_scanner_integration.py` |
| Markdown renderer direction | `tests/test_markdown_renderer.py` |
| pipx/release validation | `tests/test_pipx_release_validation_script.py`, `tests/test_public_release_metadata.py` |

The export-model tests cover dataclasses, serialization, deserialization, summary, tree, reports, contract, audit, readiness, selftest, API surface, module discovery, golden snapshots, public API E2E behavior, and scanner integration.

---

## Packaging

RepoDossier is a Python CLI project using `pyproject.toml`.

Runtime dependency:

- `PyYAML`

Optional development dependencies include:

- `pytest`
- `build`
- `twine`

Local development setup:

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest --color=yes
~~~

Local pipx validation from a checkout:

~~~bash
python3 -m pipx uninstall repodossier 2>/dev/null || true
python3 -m pipx install "$PWD"
export PATH="$HOME/.local/bin:$PATH"
repodossier --help
repocontext --help
~~~

---

## Current Milestone Boundary

Milestone 3 status:

- structured export model exists
- scanner-to-model bridge exists
- model API, contract, audit, readiness, roundtrip, selftest, and integration tests exist
- existing Markdown-oriented exports remain compatible

Not yet Milestone 3 scope:

- complete MarkdownRenderer migration
- XMLRenderer
- `--format xml`
- optional line numbers
- Test Map feature implementation
- Recent Commit Context feature implementation
- deeper non-Python static analysis beyond current language and Bash support

Next architectural step:

- Milestone 4 should migrate Markdown rendering to consume `RepositoryExport` as the primary renderer input.
- Milestone 5 should add XML rendering from the same model.
