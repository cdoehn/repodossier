# RepoContext

RepoContext creates AI-friendly exports of Git repositories.

It scans Git-tracked files, builds a structured repository overview, and writes `full.txt`, a compact `ai.txt` export, and an explicit documentation-only `docs.txt` export that can be pasted into large language models such as ChatGPT, Claude, Gemini, Aider, and other coding assistants.

The current implementation focuses on robust **Full Export**, compact **AI Export**, and documentation-only **Docs Export** modes for Python projects. It includes repository statistics, file summaries, a tree view, complete source export, documentation extraction, warnings, important-file ranking, a Python symbol index, a Python import graph, and a static Python call graph.

## Why RepoContext exists

Large language models work best when they receive repository context in a stable, readable format.

Manually copying files into a chat is slow and error-prone. RepoContext automates that process and produces a deterministic export that is easy for AI tools to understand.

RepoContext is useful when you want to:

- give an AI assistant the current state of a repository
- review a project architecture with AI
- generate implementation plans from real code
- inspect dependencies between local Python modules
- understand where functions and methods are called
- create reproducible `full.txt` snapshots during development

## Current status

RepoContext is currently in early development.

Implemented:

- Git repository detection
- Git-tracked file discovery via `git ls-files`
- text and binary file detection
- language detection for common text formats
- file metadata scanning
- line counts and token estimation
- complete `full.txt` export
- automatic `.gitignore` integration for RepoContext export files
- repository info command
- Python symbol extraction
- Python import graph
- Python call graph
- compact `ai.txt` export
- documentation-only `docs.txt` export
- CLI aliases for full and AI exports

Planned but not complete yet:

- `changed.txt`
- dependency summary from `pyproject.toml` and requirements files
- database schema extraction
- secret detection
- advanced important-file ranking
- configuration via `.repocontext.yml`
- split exports for very large repositories
- Bash symbol and call graph support

## Installation

### Install from the local repository during development

From the repository root:

```bash
pipx install .
```

Or reinstall after local changes:

```bash
pipx uninstall repocontext
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
repocontext --version
repocontext info
```

## Usage

Run RepoContext inside a Git repository or any subdirectory of a Git repository.

### Default export

```bash
repocontext
```

This writes both standard export files to the repository root:

```text
full.txt
ai.txt
```

### Explicit full export command

```bash
repocontext full
```

This also writes both `full.txt` and `ai.txt`.

### Export alias

```bash
repocontext export
```

`repocontext export` behaves like `repocontext full` and writes both `full.txt` and `ai.txt`.

### AI-only export

```bash
repocontext export-ai
```

This writes only:

```text
ai.txt
```

to the repository root.

### Documentation-only export

```bash
repocontext export-docs
```

This writes only:

```text
docs.txt
```

to the repository root.

The documentation export contains Git-tracked documentation files such as README, architecture notes, specifications, tasks, roadmaps, changelogs, contributing documents, licenses, and files under `docs/`. It excludes generated RepoContext export files such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt`.

### Repository info

```bash
repocontext info
```

This prints repository metadata and a compact import graph summary.

### Version

```bash
repocontext --version
```

## Output: full.txt

The current `full.txt` export contains:

1. AI Quick Start
2. Repository Statistics
3. File Summary
4. Repository Tree
5. Complete Source Export
6. Warnings
7. Import Graph
8. Call Graph

The export is Markdown-oriented and designed to be readable both by humans and AI systems.

## Output: ai.txt

The current `ai.txt` export contains:

1. Project summary
2. Architecture Summary
3. Important Files
4. Symbol Index
5. Import Graph
6. Call Graph
7. Notes

The AI export is intentionally compact and does not include a complete source dump.

## Output: docs.txt

The current `docs.txt` export contains:

1. Documentation Quick Start
2. Documentation Summary
3. Documentation Files
4. Extracted Documents
5. Warnings

The docs export is documentation-only. It includes documentation-like Git-tracked text files and excludes source-code files plus generated RepoContext exports.

## What gets exported

RepoContext exports **Git-tracked files only**.

File discovery is based on:

```bash
git ls-files
```

This means:

- untracked files are ignored
- ignored files are ignored unless they are already tracked
- generated exports such as `full.txt`, `ai.txt`, `docs.txt`, and `changed.txt` are normally not included
- binary files are detected and skipped from the source dump

## Automatic .gitignore integration

When RepoContext runs, it ensures these generated export files are present in `.gitignore`:

```text
full.txt
ai.txt
docs.txt
changed.txt
```

The `.gitignore` update is idempotent:

- existing content is preserved
- existing entries are not duplicated
- missing RepoContext entries are added
- repeated runs should not create new diffs

## Import Graph

RepoContext statically analyzes Python imports and adds an Import Graph section to `full.txt`.

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
- repocontext.cli -> repocontext.exporters
- repocontext.exporters.full -> repocontext.scanner
```

The Import Graph is built with Python AST analysis. Project code is not imported or executed.

## Call Graph

RepoContext statically analyzes Python function and method calls and adds a Call Graph section to `full.txt`.

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
repocontext.cli.main (src/repocontext/cli.py)
  - line 150: calls repocontext.exporters.generate_full_export [function, imported_local]

External calls:
- repocontext.git.list_tracked_files -> subprocess.run (line 74, method, external)
```

The Call Graph is intentionally conservative. Dynamic calls, monkeypatching, reflection, decorators, runtime imports, and complex type inference are not guaranteed to be resolved.

### Call Graph guarantees and limits

RepoContext's Call Graph is designed to be useful without pretending to be perfect.

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

RepoContext includes a Python Symbol Index used internally by later analysis stages.

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
│   └── repocontext
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
│       ├── symbols.py
│       └── models.py
├── tests
├── planning
├── pyproject.toml
├── LICENSE
└── README.md
```

## Architecture overview

RepoContext follows a simple pipeline:

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
| `repocontext.cli` | command-line interface |
| `repocontext.git` | Git repository discovery and metadata |
| `repocontext.scanner` | file scanning, text/binary detection, metadata |
| `repocontext.gitignore` | automatic `.gitignore` management |
| `repocontext.symbols` | Python symbol extraction |
| `repocontext.import_graph` | Python import analysis and dependency graph |
| `repocontext.call_graph` | Python static call graph analysis |
| `repocontext.exporters.full` | `full.txt` context creation, rendering, and writing |
| `repocontext.exporters.ai` | compact `ai.txt` context creation, rendering, and writing |
| `repocontext.exporters.docs` | documentation-only `docs.txt` context creation, rendering, and writing |
| `repocontext.models` | shared data models |

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
repocontext full
```

or:

```bash
repocontext export
```

## Development workflow

Typical local workflow:

```bash
source .venv/bin/activate
python3 -m pytest --color=yes
repocontext full
git status --short
```

For local pipx testing:

```bash
pipx uninstall repocontext
pipx install .
repocontext --version
repocontext info
repocontext full
```

## Design principles

RepoContext tries to be:

- deterministic
- safe
- static-analysis based
- easy to inspect
- useful for AI context windows
- conservative when resolution is uncertain
- robust against partial or broken source files

Important safety rule:

RepoContext does **not** import or execute project code for symbol, import, or call analysis. Python analysis is AST-based.

## Limitations

Current limitations:

- advanced analysis is Python-focused
- dynamic calls may not be resolved
- object types are not inferred deeply
- import resolution is static and best-effort
- external packages are not inspected
- only Git-tracked files are considered
- `changed.txt` is planned but not complete yet
- configuration support is planned but not complete yet

## Roadmap

High-level roadmap:

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

See the files in `planning/` for detailed milestone notes.

## License

MIT License. See `LICENSE`.

## Features

- Dependency detection from pyproject.toml and requirements.txt

## Dependency Detection

RepoContext detects Python project dependencies with static analysis and includes them in generated exports.

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
