# Milestone 3 – Full Export MVP

Goal: Implement the first complete default export mode of RepoContext.

The default command:

    repocontext

must generate:

    full.txt

The full export must contain:

- AI Quick Start
- Repository Statistics
- File Summary
- Repository Tree
- Complete Source Export
- Warnings

Milestone 3 intentionally does not include:

- .gitignore integration
- ai.txt generation
- docs.txt generation
- changed.txt generation
- symbol extraction
- import graph
- call graph
- secret detection
- configuration support


## 3.1 – Export Data Model and Section Structure

Goal: Create a clean internal foundation for rendering full.txt.

### 3.1.A – Define export section order

Define the exact section order for the Full Export MVP:

1. AI Quick Start
2. Repository Statistics
3. File Summary
4. Repository Tree
5. Complete Source Export
6. Warnings

The order must stay stable because AI tools should receive predictable exports.

### 3.1.B – Define section heading style

Use clear Markdown-style headings for every section.

Example:

    # AI Quick Start
    # Repository Statistics
    # File Summary
    # Repository Tree
    # Complete Source Export
    # Warnings

### 3.1.C – Create or extend export-related data structures

Introduce a simple internal structure that can carry:

- repository root
- git metadata
- scanned file metadata
- text files
- skipped binary files
- warnings
- total statistics

Do not over-engineer this yet. The goal is an MVP that is easy to extend later.

### 3.1.D – Separate data collection from rendering

Avoid mixing filesystem scanning, Git discovery and text rendering too tightly.

The desired flow should be:

1. discover repository
2. discover tracked files
3. scan files
4. build export model
5. render full.txt
6. write full.txt

### 3.1.E – Keep Milestone 3 focused on full.txt only

Do not implement ai.txt, docs.txt or changed.txt in this milestone.

Those belong to later milestones.


## 3.2 – Full Export Orchestrator

Goal: Make the default CLI command run the full export pipeline.

### 3.2.A – Wire default CLI behavior to Full Export

The command:

    repocontext

should run the Full Export MVP.

It should not require an explicit flag.

### 3.2.B – Reuse Git discovery from Milestone 1

Use existing Git repository detection.

The export must only work inside a Git repository or below a Git repository.

### 3.2.C – Reuse git ls-files integration

Use the existing tracked-file discovery.

Only Git-tracked files should be considered for export.

### 3.2.D – Reuse File Scanner from Milestone 2

Use existing scanner functionality for:

- text detection
- binary detection
- line counting
- token estimation
- language detection

### 3.2.E – Build the Full Export context

Collect all data needed by the renderer:

- repository root
- tracked files
- scanned files
- skipped binary files
- warnings
- statistics

### 3.2.F – Choose output path

The default output file must be:

    full.txt

It should be written into the repository root.

### 3.2.G – Print a simple CLI success message

After successful export, print a clear message such as:

    Wrote full.txt

Keep the CLI output minimal for now.


## 3.3 – Repository Statistics Section

Goal: Add repository-wide statistics to full.txt.

### 3.3.A – Count total tracked files

Count all Git-tracked files returned by git ls-files.

This includes text files and binary files.

### 3.3.B – Count exported text files

Count all files that are detected as text and included in the source dump.

### 3.3.C – Count skipped binary files

Count all files detected as binary and excluded from the complete source dump.

### 3.3.D – Sum total lines

Sum line counts from all exported text files.

Binary files must not contribute to the line count.

### 3.3.E – Sum estimated tokens

Sum token estimates from all exported text files.

Use the token estimation logic from Milestone 2.

### 3.3.F – Count file types

Generate file type counts using file extensions or detected language.

Example:

    .py: 12
    .md: 3
    .toml: 1

Files without extension should be grouped clearly.

### 3.3.G – Render statistics in readable text

The output should be simple and AI-friendly.

Example:

    # Repository Statistics

    Total tracked files: 42
    Exported text files: 39
    Skipped binary files: 3
    Total lines: 4200
    Estimated tokens: 28000

    File types:
    - .py: 18
    - .md: 5
    - .toml: 1


## 3.4 – AI Quick Start Section

Goal: Add a short AI-oriented project summary at the beginning of full.txt.

### 3.4.A – Detect primary language

Use scanner data to determine the dominant language.

For example:

- Python
- Bash
- Markdown-heavy project
- Unknown

### 3.4.B – Detect project type

Infer a simple project type.

Examples:

- Python CLI project
- Python package
- Bash project
- Documentation project
- Unknown Git repository

For the current RepoContext project, Python CLI project should likely be detected.

### 3.4.C – Detect package manager or packaging files

Detect common files such as:

- pyproject.toml
- requirements.txt
- setup.py
- package.json

For Milestone 3, simple file-presence detection is enough.

### 3.4.D – Detect test framework

Detect test framework from known files and folders.

Examples:

- pytest if tests/ exists or pytest appears in pyproject.toml
- unittest if unittest patterns are found
- unknown if nothing is detected

### 3.4.E – Detect entrypoints

Detect likely entrypoints from:

- pyproject.toml console scripts
- src package layout
- obvious CLI files
- existing CLI entrypoint code

For Milestone 3, a basic best-effort implementation is enough.

### 3.4.F – Detect project purpose

Try to derive a short purpose from README.md if available.

If no README exists, use a fallback such as:

    Purpose: Unknown

Do not invent a detailed purpose.

### 3.4.G – Render AI Quick Start as the first section

Example:

    # AI Quick Start

    Project type: Python CLI project
    Primary language: Python
    Package manager: pyproject.toml
    Test framework: pytest
    Entrypoints: repocontext
    Purpose: Creates AI-friendly exports of Git repositories.


## 3.5 – File Summary Section

Goal: Add a compact overview of all exported files.

### 3.5.A – Include every exported text file

The File Summary should list all text files that are included in the Complete Source Export.

### 3.5.B – Include path

Each row or item must include the repository-relative file path.

Example:

    src/repocontext/cli.py

### 3.5.C – Include language or file type

Use language detection from Milestone 2.

Examples:

- Python
- Bash
- Markdown
- TOML
- YAML
- Text
- Unknown

### 3.5.D – Include line count

Include the line count for each exported text file.

### 3.5.E – Include estimated token count

Include the estimated token count for each exported text file.

### 3.5.F – Keep output stable and sorted

Sort files by repository-relative path.

Stable order is important for reproducible exports.

### 3.5.G – Choose a simple readable format

A Markdown table is acceptable if easy to implement.

Example:

    # File Summary

    | Path | Language | Lines | Tokens |
    | --- | --- | ---: | ---: |
    | README.md | Markdown | 80 | 600 |
    | src/repocontext/cli.py | Python | 120 | 900 |

If Markdown table formatting becomes annoying, use a simple bullet format instead.


## 3.6 – Repository Tree Section

Goal: Add a tree view of exported Git-tracked files.

### 3.6.A – Build tree from repository-relative paths

Use all Git-tracked paths as input.

The tree should reflect repository structure.

### 3.6.B – Sort paths alphabetically

The tree output must be deterministic.

### 3.6.C – Render directories and files clearly

Example:

    # Repository Tree

    .
    ├── README.md
    ├── pyproject.toml
    ├── src
    │   └── repocontext
    │       ├── cli.py
    │       └── scanner.py
    └── tests
        └── test_scanner.py

### 3.6.D – Include skipped binary files in the tree

Binary files may appear in the repository tree because they are Git-tracked.

They must not appear in the Complete Source Export.

### 3.6.E – Optionally mark binary files

If simple to implement, mark binary files as skipped.

Example:

    image.png [binary skipped]

This is optional for the MVP.

### 3.6.F – Keep tree renderer independent

The tree rendering logic should be reusable later by ai.txt.


## 3.7 – Complete Source Export Section

Goal: Dump the full contents of all exported text files.

### 3.7.A – Include only text files

Only include files detected as text by the scanner.

Binary files must be excluded.

### 3.7.B – Use stable file order

Sort files by repository-relative path.

This makes diffs and repeated exports predictable.

### 3.7.C – Add a clear file heading for each file

Example:

    ## File: src/repocontext/cli.py

The heading must make it easy for AI tools to identify file boundaries.

### 3.7.D – Wrap source content in fenced code blocks

Use Markdown code fences.

Example:

    ```python
    ...
    ```

Use language identifiers when known.

### 3.7.E – Use suitable fence language identifiers

Examples:

- python for Python
- bash for Bash
- markdown for Markdown
- toml for TOML
- yaml for YAML
- json for JSON
- text for unknown text

### 3.7.F – Preserve file contents exactly enough for AI use

Do not modify indentation.

Do not trim meaningful content.

Do not summarize code in full.txt.

### 3.7.G – Handle files containing triple backticks safely

If a file contains Markdown code fences, avoid breaking the export.

Possible approaches:

- use longer fences for wrapping
- or use plain file delimiters instead of normal code fences

Milestone 3 should at least not produce obviously broken output for Markdown files.

### 3.7.H – Handle read errors gracefully

If a file cannot be read, do not crash the whole export if avoidable.

Add a warning instead.

### 3.7.I – Do not include full.txt itself unless it is Git-tracked

The export is based on git ls-files.

Since full.txt should normally not be Git-tracked later, this becomes more important in Milestone 4.


## 3.8 – Warnings Section

Goal: Collect and render export warnings at the end of full.txt.

### 3.8.A – Add warning for skipped binary files

Example:

    Skipped binary file: image.png

### 3.8.B – Add warning for unreadable files

Example:

    Could not read file: path/to/file.txt

### 3.8.C – Add warning for encoding problems

If decoding required fallback behavior, add a warning.

Example:

    Decoding fallback used for: path/to/file.txt

### 3.8.D – Add warning for empty repositories

If no tracked files are found, render a warning.

Example:

    No Git-tracked files found.

### 3.8.E – Add warning when no text files are exportable

If tracked files exist but all are binary or unreadable, render a warning.

Example:

    No exportable text files found.

### 3.8.F – Render explicit no-warning state

If there are no warnings, render:

    No warnings.

This keeps the section predictable.

### 3.8.G – Keep warnings as plain text bullets

Example:

    # Warnings

    - Skipped binary file: image.png
    - Could not read file: broken.txt


## 3.9 – Full Export Write Logic

Goal: Write full.txt robustly and predictably.

### 3.9.A – Write UTF-8 output

full.txt must be written as UTF-8.

### 3.9.B – Overwrite existing full.txt

Running repocontext again should replace the previous full.txt.

### 3.9.C – Write into repository root

The output path should be:

    <repo-root>/full.txt

not necessarily the current working directory.

### 3.9.D – Consider atomic writing

If simple, write to a temporary file first and then replace full.txt.

This prevents partially written exports.

### 3.9.E – Ensure parent directory exists

The repository root should already exist, but the write logic should remain clean.

### 3.9.F – Return or print final path

The CLI should tell the user where the file was written.

Example:

    Wrote full.txt

or:

    Wrote /path/to/repo/full.txt

### 3.9.G – Keep failure messages understandable

If writing fails, report a clear error.

Example:

    Could not write full.txt: permission denied


## 3.10 – MVP Tests for Milestone 3

Goal: Add enough tests to prove that the Full Export MVP works.

### 3.10.A – Test that default CLI creates full.txt

Create a test repository fixture.

Run:

    repocontext

Assert that:

    full.txt

exists.

### 3.10.B – Test required sections

Assert that full.txt contains:

- # AI Quick Start
- # Repository Statistics
- # File Summary
- # Repository Tree
- # Complete Source Export
- # Warnings

### 3.10.C – Test tracked text file export

Create a tracked text file.

Assert that:

- the file appears in File Summary
- the file appears in Repository Tree
- the file content appears in Complete Source Export

### 3.10.D – Test binary file exclusion from source dump

Create a tracked binary file.

Assert that:

- it does not appear as dumped source content
- it appears as skipped or warning if that behavior is implemented

### 3.10.E – Test line counts

Create files with known line counts.

Assert that File Summary and Repository Statistics contain expected line totals.

### 3.10.F – Test token estimate presence

Do not over-test exact token values unless the estimator is deterministic and already tested.

At minimum, assert that token estimates are present.

### 3.10.G – Test repository tree output

Create nested files.

Assert that the tree contains expected paths and structure markers.

### 3.10.H – Test warnings section with no warnings

For a normal text-only repository, assert that Warnings contains:

    No warnings.

### 3.10.I – Test warnings section with skipped binary file

For a repository with a tracked binary file, assert that a warning is rendered.

### 3.10.J – Test output path is repository root

Run the CLI from a subdirectory inside the repository.

Assert that full.txt is written to the repository root, not the subdirectory.

### 3.10.K – Keep tests at stable semantic insertion points

Add tests near related existing tests.

Do not append everything blindly to the end of test files if a better location exists.

### 3.10.L – Keep tests focused on Milestone 3

Do not add tests for:

- .gitignore auto-management
- ai.txt
- docs.txt
- changed.txt
- symbol index
- import graph
- call graph

Those belong to later milestones.


## Suggested implementation order

1. 3.1 – Export Data Model and Section Structure
2. 3.2 – Full Export Orchestrator
3. 3.3 – Repository Statistics Section
4. 3.4 – AI Quick Start Section
5. 3.5 – File Summary Section
6. 3.6 – Repository Tree Section
7. 3.7 – Complete Source Export Section
8. 3.8 – Warnings Section
9. 3.9 – Full Export Write Logic
10. 3.10 – MVP Tests for Milestone 3
