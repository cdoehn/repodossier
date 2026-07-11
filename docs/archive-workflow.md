# RepoDossier archive workflow

RepoDossier can build a shared repository dossier archive with this command form:

    repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER

At least one source folder and one output folder are required. The last positional argument is always the output folder. All earlier positional arguments are source folders.

## Source folders

Source folders may be Git repository roots or subfolders inside Git repositories. RepoDossier resolves the corresponding repository root for every source folder.

Only the explicitly supplied source folders are analyzed for source references. The repository snapshot stores the complete detected repository working tree.

## Archive structure

Each invocation creates exactly one ZIP archive. The archive contains:

    reports/
    repositories/
        repository-a/
        repository-b/

Repository folder names inside the archive are deterministic and collision-free.

## Archive names

The optional `--output-name` value is used as the exact output filename. Any extension is accepted:

    repodossier ./projekt ./output --output-name projektpaket.zip
    repodossier ./projekt ./output --output-name projektpaket.xml

The content remains a ZIP archive regardless of the selected filename.

Existing target files are not overwritten silently.

## Snapshot contents

The snapshot represents the visible working tree, not just the last commit. It includes tracked files, staged changes, unstaged changes, staged new files, and untracked files that are not ignored by Git.

The snapshot excludes `.git`, Git internals, ignored untracked files, the output folder, the final archive, and temporary archive files from the active run.

## Source references

Reports do not embed full source-code bodies for detected code files. Instead they point to the archived snapshot file:

    Source file: src/main.py
    Archive path: ../repositories/projekt/src/main.py

Source-code classification uses RepoDossier's central language detection. A separate source-code extension list must not be introduced for this workflow.

## Installation checks

The command is exposed through the package entry point:

    repodossier = repodossier.cli:main

The intended install checks are:

    python3 -m pip install .
    pipx install .

After installation, `repodossier --help` must succeed.
