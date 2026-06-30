# RepoDossier

RepoDossier creates AI-friendly exports of Git repositories.

It scans Git-tracked files, builds a structured repository overview, and writes `full.txt`, a compact `ai.txt` export, an explicit documentation-only `docs.txt` export, and a focused `changed.txt` export that can be pasted into large language models such as ChatGPT, Claude, Gemini, Aider, and other coding assistants.

The current implementation focuses on robust **Full Export**, compact **AI Export**, documentation-only **Docs Export**, and focused **Changed Export** modes for Python projects. It includes repository statistics, file summaries, a tree view, complete source export, documentation extraction, warnings, important-file ranking, a Python symbol index, a Python import graph, and a static Python call graph.

## Why RepoDossier exists

Large language models work best when they receive repository context in a stable, readable format.

Manually copying files into a chat is slow and error-prone. RepoDossier automates that process and produces a deterministic export that is easy for AI tools to understand.

RepoDossier is useful when you want to:

- give an AI assistant the current state of a repository
- review a project architecture with AI
- generate implementation plans from real code
- inspect dependencies between local Python modules
- understand where functions and methods are called
- create reproducible `full.txt` snapshots during development

## Current status

RepoDossier 1.0 is the first stable release line for local CLI repository exports.

Implemented:

- configuration via `.repodossier.yml`
- split exports for large `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` files
- Git repository detection
- Git-tracked file discovery via `git ls-files`
- text and binary file detection
- language detection for common text formats
- file metadata scanning
- line counts and token estimation
- complete `full.txt` export
- automatic `.gitignore` integration for RepoDossier export files
- repository info command
- Python symbol extraction
- Python import graph
- Python call graph
- compact `ai.txt` export
- documentation-only `docs.txt` export
- dependency detection from `pyproject.toml` and requirements files
- database schema extraction from SQLite databases and SQL schema files
- multi-signal important-file ranking for AI exports
- `changed.txt` export for git diffs, changed file contents, and branch comparisons
- CLI aliases for full and AI exports
- Bash source detection, function discovery, symbol index integration, and static Bash call graph support



Planned but not complete yet:

None for Release 1.0.


## Installation

### Install from the local repository during development

From the repository root:

```bash
pipx install .
```

Or reinstall after local changes:

```bash
pipx uninstall repodossier
pipx install .
```

### Editable development install

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

### Verify installation

```bash
repodossier --version
repodossier info
```

## Secret Detection

RepoDossier masks potential secrets before writing exports. This is a best-effort
safety feature for sharing repository context with AI tools and documentation
workflows.

The built-in detector looks for common assignment-style secrets, including:

- `API_KEY`
- `TOKEN`
- `SECRET`
- `PASSWORD`

Detected values are replaced with a masked value that keeps a small prefix and
suffix for context while removing the sensitive middle part.

Example:

    OPENAI_API_KEY="sk-t***REDACTED***cdef"

Secret masking is enabled for generated exports such as `full.txt`, `ai.txt`,
`docs.txt`, and `changed.txt`. Export summaries may include secret types, counts,
and affected export sections, but they must not include the original secret
values.

This feature is intentionally conservative and is not a full security scanner.
It cannot guarantee that every possible credential format will be found. Always
review generated files before publishing or sharing them outside a trusted
environment.

## Usage

Run RepoDossier inside a Git repository or any subdirectory of a Git repository.

### Default export

```bash
repodossier
```

This writes both standard export files to the repository root:

```text
full.txt
ai.txt
```

### Explicit full export command

```bash
repodossier full
```

This also writes both `full.txt` and `ai.txt`.

### Export alias

```bash
repodossier export
```

`repodossier export` behaves like `repodossier full` and writes both `full.txt` and `ai.txt`.

### AI-only export

```bash
repodossier export-ai
```

This writes only:

```text
ai.txt
```

to the repository root.

### Documentation-only export

```bash
repodossier export-docs
```

This writes only:

```text
docs.txt
```

to the repository root.

The documentation export contains Git-tracked documentation files such as README, architecture notes, specifications, tasks, roadmaps, changelogs, contributing documents, licenses, and files under `docs/`. It excludes generated RepoDossier export files such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt`.

### Changed-files export

```bash
repodossier changed
```

This writes:

```text
changed.txt
```

to the repository root.

The changed export focuses on files changed in the current Git working tree. It includes a changed-file summary, unified Git diff output, changed text-file contents, deleted-file entries, and binary/skipped-file entries.

For feature branches, compare committed changes against another branch with Git's three-dot comparison:

```bash
repodossier changed --branch main
```

Use a custom output path when needed:

```bash
repodossier changed --output review-changes.txt
```

Disable the Git diff section while keeping the changed file contents:

```bash
repodossier changed --no-diff
```

The changed export can include modified, staged, deleted, renamed, and untracked non-ignored files. Generated RepoDossier export files such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` are kept in `.gitignore` to avoid self-reference loops.


### Split exports

Large exports can be written as additional part files next to the complete export.

The main export file is always still written in full. Split files are optional companion files, for example:

```text
full.txt
full.part01.txt
full.part02.txt
```

Enable split output for the supported export commands:

```bash
repodossier full --split
repodossier export-ai --split
repodossier export-docs --split
repodossier changed --split
```

Choose a maximum raw character count per part:

```bash
repodossier full --split --split-max-chars 200000
```

Choose the splitting strategy:

```bash
repodossier export-ai --split --split-strategy heading
repodossier export-ai --split --split-strategy plain
```

Supported strategies:

- `heading`: prefers Markdown heading boundaries where possible
- `plain`: splits by raw character count

Disable split output even when enabled in configuration:

```bash
repodossier full --no-split
```

Output file names follow the source export name:

```text
full.part01.txt
ai.part01.txt
docs.part01.txt
changed.part01.txt
```

For changed exports with a custom output path, the part files follow the custom name:

```bash
repodossier changed --output review-changes.txt --split
```

```text
review-changes.part01.txt
review-changes.part02.txt
```

Split exports can also be enabled through `.repodossier.yml`:

```yaml
exports:
  split:
    enabled: true
    max_chars: 200000
    strategy: heading
```

CLI options override the configuration file.
### Repository info

```bash
repodossier info
```

This prints repository metadata and a compact import graph summary.

### Version

```bash
repodossier --version
```

## Output: full.txt

The current `full.txt` export contains:

1. AI Quick Start
2. Repository Statistics
3. File Summary
4. Repository Tree
5. Dependencies
6. Database Schema
7. Complete Source Export
8. Warnings
9. Import Graph
10. Call Graph

The export is Markdown-oriented and designed to be readable both by humans and AI systems.

## Output: ai.txt

The current `ai.txt` export contains:

1. Project summary
2. Architecture Summary
3. Important Files
4. Dependencies
5. Database Schema
6. Symbol Index
7. Import Graph
8. Call Graph
9. Notes

The AI export is intentionally compact and does not include a complete source dump.

### Important file ranking

The `Important Files` section is produced by RepoDossier's shared important-file ranking.

The ranking combines these deterministic signals:

- CLI and Python entrypoints from `pyproject.toml`, `__main__.py`, `main.py`, `cli.py`, `app.py`, `server.py`, `manage.py`, `wsgi.py`, and `asgi.py`
- import graph centrality, especially files imported by several local modules
- call graph centrality, especially files whose functions or methods are called by several local files
- documentation relevance such as README, architecture, specification, roadmap, changelog, contributing, and docs files
- structural project files such as `pyproject.toml`, `setup.py`, `setup.cfg`, requirements files, `Dockerfile`, `Makefile`, and package initializers

Each ranked file carries a compact reason in `ai.txt`, for example `Project script entry point`, `Imported by 3 local files`, `Called by 2 local files`, `Primary project documentation`, or `Python project configuration`.

Generated RepoDossier exports such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` are excluded from the important-file ranking.

## Output: docs.txt

The current `docs.txt` export contains:

1. Documentation Quick Start
2. Documentation Summary
3. Documentation Files
4. Extracted Documents
5. Warnings

The docs export is documentation-only. It includes documentation-like Git-tracked text files and excludes source-code files plus generated RepoDossier exports.

## Output: changed.txt

The current `changed.txt` export contains:

1. Changed Export header
2. Repository path
3. Compare Mode
4. Changed Files Summary
5. Changed Files overview
6. Git Diff
7. Changed File Contents
8. Deleted Files
9. Binary / Skipped Files

The changed export is intended for focused code review and AI-assisted patch work. It shows what changed without dumping the entire repository.

Default mode compares the current working tree, including staged and unstaged changes. Branch mode compares committed changes against another branch, for example `repodossier changed --branch main`.


## What gets exported

RepoDossier's standard `full.txt`, `ai.txt`, and `docs.txt` exports use **Git-tracked files only**.

File discovery for those standard exports is based on:

```bash
git ls-files
```

This means:

- untracked files are ignored by the standard full, AI, and docs exports
- ignored files are ignored unless they are already tracked
- generated exports such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` are normally not included
- binary files are detected and skipped from the source dump

The `changed.txt` export is different: it is Git-diff based and focuses on current changes. It can include untracked files when they are not ignored by `.gitignore`.

## Automatic .gitignore integration

When RepoDossier runs, it ensures these generated export files are present in `.gitignore`:

```text
full.txt
ai.txt
docs.txt
changed.txt
```

The `.gitignore` update is idempotent:

- existing content is preserved
- existing entries are not duplicated
- missing RepoDossier entries are added
- repeated runs should not create new diffs

## Import Graph

RepoDossier statically analyzes Python imports and adds an Import Graph section to `full.txt`.

It detects:

- `import module`
- `import module as alias`
- `from module import name`
- relative imports
- local module dependencies
- external imports
- unresolved imports
- syntax errors during import analysis

Example output shape:

```text
## Import Graph

Summary:
- Local modules: 12
- Local dependencies: 18
- External imports: 9
- Unresolved imports: 0
- Analysis errors: 0

Local dependencies:
- repodossier.cli -> repodossier.exporters
- repodossier.exporters.full -> repodossier.scanner
```

The Import Graph is built with Python AST analysis. Project code is not imported or executed.

## Call Graph

RepoDossier statically analyzes Python function and method calls and adds a Call Graph section to `full.txt`.

It currently detects:

- direct function calls
- nested function calls
- module-level calls
- method and attribute calls
- `self.method()` calls
- `cls.method()` and same-class calls where resolvable
- imported local function calls using the Import Graph and Symbol Index
- external calls such as `pathlib.Path()` or `subprocess.run()`
- unresolved calls without pretending they are known

Example output shape:

```text
## Call Graph

Summary:
- Call edges: 42
- Local/internal calls: 18
- External calls: 14
- Ambiguous calls: 1
- Unresolved calls: 9

Internal calls by caller:
repodossier.cli.main (src/repodossier/cli.py)
  - line 150: calls repodossier.exporters.generate_full_export [function, imported_local]

External calls:
- repodossier.git.list_tracked_files -> subprocess.run (line 74, method, external)
```

The Call Graph is intentionally conservative. Dynamic calls, monkeypatching, reflection, decorators, runtime imports, and complex type inference are not guaranteed to be resolved.

### Call Graph guarantees and limits

RepoDossier's Call Graph is designed to be useful without pretending to be perfect.

It guarantees that:

- Python source is parsed statically with `ast`
- project code is not imported or executed
- directly visible calls are collected
- identical call edges at the same call location are deduplicated
- repeated calls on different lines remain visible
- repo-internal resolved calls are shown prominently
- external, ambiguous, and unresolved calls are separated from internal calls
- large call groups are truncated with deterministic `... more` lines

Default `full.txt` Call Graph display limits:

| Group | Default limit |
| --- | ---: |
| Internal calls | 200 |
| External calls | 25 |
| Ambiguous calls | 25 |
| Unresolved calls | 25 |

The Call Graph does not guarantee complete resolution for dynamic Python behavior such as monkeypatching, runtime imports, reflection, framework injection, decorators that replace functions, or object method calls where the receiver type is unknown.

## Symbol extraction

RepoDossier includes a Python Symbol Index used internally by later analysis stages.

It can detect:

- top-level functions
- async functions
- classes
- methods
- async methods
- line numbers
- parent class for methods
- syntax errors without aborting the entire analysis

The Symbol Index is currently mainly used by the Call Graph to resolve local and imported functions.

## Supported files

Current scanner support includes:

- Python
- Bash
- Markdown
- TOML
- YAML
- JSON
- INI
- plain text
- common extensionless files such as `LICENSE`, `README`, `Makefile`, and `Dockerfile`

Binary files are detected and excluded from the complete source dump.

## Project layout

```text
.
├── src
│   └── repodossier
│       ├── cli.py
│       ├── exporters
│       │   ├── ai.py
│       │   ├── docs.py
│       │   └── full.py
│       ├── git.py
│       ├── gitignore.py
│       ├── import_graph.py
│       ├── call_graph.py
│       ├── scanner.py
│       ├── schema.py
│       ├── symbols.py
│       └── models.py
├── tests
├── planning
├── pyproject.toml
├── LICENSE
└── README.md
```

## Architecture overview

RepoDossier follows a simple pipeline:

```text
Git repository
      |
      v
Git-tracked file discovery
      |
      v
File scanner
      |
      v
Static analysis
      |
      v
Export renderers
      |
      v
full.txt / ai.txt / docs.txt
```

Main modules:

| Module | Purpose |
| --- | --- |
| `repodossier.cli` | command-line interface |
| `repodossier.git` | Git repository discovery and metadata |
| `repodossier.scanner` | file scanning, text/binary detection, metadata |
| `repodossier.schema` | Database schema discovery, SQLite metadata extraction, SQL CREATE TABLE parsing, and schema report merging |
| `repodossier.gitignore` | automatic `.gitignore` management |
| `repodossier.symbols` | Python symbol extraction |
| `repodossier.import_graph` | Python import analysis and dependency graph |
| `repodossier.call_graph` | Python static call graph analysis |
| `repodossier.exporters.full` | `full.txt` context creation, rendering, and writing |
| `repodossier.exporters.ai` | compact `ai.txt` context creation, rendering, and writing |
| `repodossier.exporters.docs` | documentation-only `docs.txt` context creation, rendering, and writing |
| `repodossier.models` | shared data models |

## Bash Support

RepoDossier includes static Bash and shell script analysis for common project scripts.

Supported Bash analysis includes:

- Bash source detection for `.sh`, `.bash`, and Bash or POSIX shell shebang files
- Bash function discovery for common function forms such as `deploy() { ... }` and `function deploy { ... }`
- Bash functions in the symbol index
- simple internal Bash function calls in the Bash call graph

The Bash analysis is intentionally static and conservative. RepoDossier reads shell source text but does not execute scripts, source files, expand variables, run `eval`, or attempt to implement a complete Bash grammar.

## Configuration with `.repodossier.yml`

RepoDossier can read an optional `.repodossier.yml` file from the repository root. This file lets you keep common export settings in the project instead of repeating the same command-line options.

If no `.repodossier.yml` exists, RepoDossier keeps its default behavior.

Example:

```yaml
include:
  paths:
    - src
    - tests
  globs:
    - "*.md"

exclude:
  paths:
    - .venv
    - build
    - dist
  globs:
    - "*.log"
    - "*.sqlite"
    - "**/__pycache__/**"

limits:
  max_file_bytes: 200000
  max_total_files: 500
  max_export_bytes: 2000000
  max_line_count: 2000

exports:
  split:
    enabled: false
    max_chars: 200000
    strategy: heading
```

Supported sections:

- `include.paths`: repository-relative files or directories to include.
- `include.globs`: repository-relative glob patterns to include.
- `exclude.paths`: repository-relative files or directories to exclude.
- `exclude.globs`: repository-relative glob patterns to exclude.
- `limits.max_file_bytes`: skip full file content when a single file is larger than this many bytes.
- `limits.max_total_files`: limit the number of files considered for export after filtering.
- `limits.max_export_bytes`: limit the generated export size.
- `limits.max_line_count`: limit the number of exported lines per file.
- `exports.split.enabled`: write additional `.partXX` files next to complete exports.
- `exports.split.max_chars`: maximum raw export characters per split part.
- `exports.split.strategy`: split strategy, either `heading` or `plain`.

Include rules are additive. If at least one include rule is configured, a file is selected when it matches any include path or include glob. If no include rule is configured, files are included by default.

Exclude rules always win over include rules. This means you can include a broad directory like `src` and still exclude a sensitive or generated subdirectory.

All paths and globs are interpreted relative to the repository root. This also applies when RepoDossier is started from a subdirectory.

A separate `.repodossier.example.yml` file is provided as a starting point. Copy it to `.repodossier.yml` and adjust it for your repository.

## Development

### Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install development dependencies

```bash
python3 -m pip install -e ".[dev]"
```

### Run tests

```bash
python3 -m pytest --color=yes
```

### Run selected tests

```bash
python3 -m pytest --color=yes tests/test_call_graph.py
python3 -m pytest --color=yes tests/test_import_graph.py
python3 -m pytest --color=yes tests/test_full_exporter.py
python3 -m pytest --color=yes tests/test_cli.py
```

### Generate fresh exports of the current repository

```bash
repodossier full
```

or:

```bash
repodossier export
```

## Development workflow

Typical local workflow:

```bash
source .venv/bin/activate
python3 -m pytest --color=yes
repodossier full
repodossier changed
git status --short
```

For local pipx testing:

```bash
pipx uninstall repodossier
pipx install .
repodossier --version
repodossier info
repodossier full
```

## Design principles

RepoDossier tries to be:

- deterministic
- safe
- static-analysis based
- easy to inspect
- useful for AI context windows
- conservative when resolution is uncertain
- robust against partial or broken source files

Important safety rule:

RepoDossier does **not** import or execute project code for symbol, import, or call analysis. Python analysis is AST-based.

## Limitations

Current limitations:

- advanced analysis is Python-focused
- dynamic calls may not be resolved
- object types are not inferred deeply
- import resolution is static and best-effort
- external packages are not inspected
- standard `full.txt`, `ai.txt`, and `docs.txt` exports consider Git-tracked files
- `changed.txt` is diff-based and can include untracked, non-ignored files
- configuration support is available via `.repodossier.yml`

## Roadmap

Completed 1.0 roadmap:

1. Full Export
2. `.gitignore` integration
3. Symbol extraction
4. Import Graph
5. Call Graph
6. AI-focused summarized export
7. Documentation export
8. Changed-files export
9. Dependency detection
10. Secret detection
11. Configuration support
12. Split exports
13. Release 1.0

See `planning/roadmap_next.md` for future work and `planning/archive/1.0.0/roadmap.md` plus `planning/archive/1.0.0/milestone*.md` for the historical 1.0.0 roadmap and milestone notes.

## License

MIT License. See `LICENSE`.

## Features

- Dependency detection from pyproject.toml and requirements.txt

## Dependency Detection

RepoDossier detects Python project dependencies with static analysis and includes them in generated exports.

Supported dependency sources:

- `pyproject.toml`
  - PEP 621 `project.dependencies`
  - PEP 621 `project.optional-dependencies`
  - Poetry `tool.poetry.dependencies`
  - Poetry development groups such as `dev`, `test`, `docs`, and `lint`
- `requirements.txt`
- development requirement files such as `requirements-dev.txt`, `requirements-test.txt`, and `requirements-docs.txt`
- requirement files below `requirements/*.txt`

Detected dependencies are classified as:

- runtime
- development
- optional
- unknown

Dependency information is exported to:

- `full.txt` as a detailed dependency section
- `ai.txt` as a compact AI-oriented dependency summary

Current limits:

- no package installation
- no network access
- no PyPI lookup
- no full dependency resolver
- no lockfile analysis
- no vulnerability scanning
- no license analysis
- unsupported requirement lines such as `-r other.txt`, `-c constraints.txt`, `--index-url`, editable installs, and VCS URLs are reported but not resolved

## Database Schema Export

RepoDossier detects and summarizes database schema information in both `full.txt` and `ai.txt`.

The schema export supports:

- SQLite database files such as `.db`, `.sqlite`, `.sqlite3`, `.db3`, and `.s3db`
- SQL schema files and migration files such as `.sql`
- `CREATE TABLE` statements in SQL files
- tables, views, columns, primary keys, indexes, and foreign-key relationships where available
- warnings for unsupported, corrupt, unreadable, or ambiguous schema files

The `full.txt` export includes a detailed `# Database Schema` section with:

- schema file counts
- detected database and SQL schema files
- table and view summaries
- columns, indexes, and foreign keys
- limited `CREATE TABLE` statement summaries
- schema warnings

The `ai.txt` export includes a compact `## Database Schema` section optimized for LLM context:

- database/schema file overview
- compact table summaries
- important columns and primary keys
- foreign-key relationships
- warnings when schema analysis was incomplete

### Safety Boundaries

Database schema export is metadata-only.

RepoDossier does **not** export table contents. It does not read application rows, user records, secrets, tokens, e-mail addresses, or inserted values from SQLite databases.

SQLite files are opened read-only and queried only through SQLite schema metadata and PRAGMA metadata.

SQL files are parsed as text. RepoDossier does not execute migrations, does not connect to external databases, and does not evaluate SQL expressions.

The SQL parser is intentionally best-effort. It is designed to extract useful structure from common `CREATE TABLE` statements, not to fully implement every SQL dialect.

Generated RepoDossier exports such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` are excluded from schema discovery.

<!-- repodossier-release-usage:start -->

## Release 1.0 usage guide

RepoDossier creates repository exports that are designed to be pasted into or attached to AI assistants. It summarizes source files, documentation, symbols, imports, call relationships, dependency metadata, database schemas, changed files, and shell scripts where supported.

The 1.0 release focuses on stable local CLI usage:

- full.txt for a complete repository context export.
- ai.txt for a compact AI-oriented architecture and code context export.
- docs.txt for documentation-focused context.
- changed.txt for reviewing current Git changes.
- .repodossier.yml for project-specific include, exclude, and limit settings.
- secret masking to reduce the risk of exporting credentials.
- split exports when configured limits require multi-part output.
- Python and Bash-aware symbol and call analysis where supported.

### Installation

For normal CLI usage from a local checkout, pipx is the recommended installation method:

    pipx install .
    repodossier --help

For a regular local Python installation:

    python3 -m pip install .
    repodossier --help

For development work:

    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -e ".[dev]"
    python3 -m pytest

### Quick start

Run RepoDossier from the root of a Git repository:

    repodossier full
    repodossier export-ai
    repodossier export-docs
    repodossier changed

The generated export files are intended as local artifacts. They should normally stay uncommitted.

### Command reference

#### repodossier full

Creates full.txt, the broadest repository export. Use it when an AI assistant needs maximum project context.

Typical content includes:

- repository overview
- AI quick-start information
- file summaries
- repository tree
- dependency information
- symbol information
- source file contents
- database schema information where available
- Bash script information where available

Example:

    repodossier full

#### repodossier export-ai

Creates ai.txt, a more focused export for AI coding sessions.

Typical content includes:

- architecture summary
- important files
- symbol index
- import graph
- call graph
- dependency information
- selected source context

Example:

    repodossier export-ai

#### repodossier export-docs

Creates docs.txt, a documentation-focused export.

Typical content includes recognized project documentation such as:

- README
- ARCHITECTURE
- TASKS
- SPEC
- other supported documentation files

Example:

    repodossier export-docs

#### repodossier changed

Creates changed.txt, a Git-change-focused export for review work.

Typical content includes:

- changed files
- relevant diff context
- changed source snippets where supported
- comparison information for the selected Git base where supported

Example:

    repodossier changed

### Configuration

RepoDossier can be configured with .repodossier.yml when project-specific filtering or limits are needed.

Example:

    include:
      - "src/**"
      - "tests/**"
      - "README.md"

    exclude:
      - ".venv/**"
      - "__pycache__/**"
      - ".git/**"
      - "full.txt"
      - "ai.txt"
      - "docs.txt"
      - "changed.txt"

    limits:
      max_file_bytes: 200000
      max_total_bytes: 2000000

Only use options that are supported by the installed RepoDossier version. If an option is not supported, prefer removing it rather than relying on undefined behavior.

### Export files

RepoDossier commonly creates these local files:

| File | Purpose |
| --- | --- |
| full.txt | complete repository context |
| ai.txt | compact AI coding context |
| docs.txt | documentation-only context |
| changed.txt | Git change review context |

When split exports are enabled or required by configured limits, RepoDossier may create multiple numbered output parts instead of one large file.

### Secret masking

RepoDossier includes secret detection and masking for common credential-like values such as API keys, tokens, secrets, and passwords. This reduces accidental exposure, but it is not a substitute for manual review.

Before sharing an export externally, inspect the generated file and confirm that no private credentials, personal data, or proprietary material are included unintentionally.

### Bash support

RepoDossier 1.0 includes Bash-aware analysis where supported by the current implementation. Bash files may contribute function information, symbol index entries, and call graph information.

### Release limitations

RepoDossier uses static analysis. Some relationships may be incomplete when code depends on dynamic imports, reflection, runtime-generated calls, shell indirection, external tools, or framework magic.

The generated exports are designed to be useful AI context, not a formal compiler, security scanner, or complete program analysis database.

### Release checklist

Before cutting or validating a release, run:

    python3 -m pytest --color=yes
    repodossier --help
    repodossier full --help
    repodossier export-ai --help
    repodossier export-docs --help
    repodossier changed --help

<!-- repodossier-pipx-validation-note -->

For a full isolated pipx release validation, run:

    scripts/validate_pipx_release.sh

The script installs RepoDossier into a temporary pipx home, runs CLI help checks, creates a temporary Git repository, validates full, AI, docs, and changed exports, and verifies that reinstalling through pipx still exposes the CLI.

For pipx validation from a local checkout:

    pipx uninstall repodossier || true
    pipx install .
    repodossier --help

<!-- repodossier-release-usage:end -->

## Legacy RepoContext compatibility

RepoDossier keeps a temporary compatibility layer for projects that still use
the old RepoContext names.

Prefer the current command for new projects:

```bash
repodossier full
repodossier export-ai
repodossier export-docs
```

Current config names:

```text
.repodossier.yml
.repodossier.yaml
.repodossier.toml
[tool.repodossier]
```

Legacy config names are still accepted as fallbacks:

```text
.repocontext.yml
.repocontext.yaml
.repocontext.toml
[tool.repocontext]
```

If both current and legacy config values are present, the RepoDossier config
takes precedence.
