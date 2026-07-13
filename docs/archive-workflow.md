# RepoDossier archive workflow

RepoDossier can build a shared repository dossier archive with this command form:

    repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER

At least one source folder and one output folder are required. The last positional argument is always the output folder. All earlier positional arguments are source folders.

## Source folders

Source folders may be Git repository roots or subfolders inside Git repositories. RepoDossier resolves the corresponding repository root for every source folder.

Only the explicitly supplied source folders are analyzed for source references. The repository snapshot stores the complete committed `HEAD` tree of each detected repository.

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

The snapshot represents the committed `HEAD` tree. RepoDossier delegates snapshot creation to Git using the core command semantics:

    git archive --format=zip --output=repodossier.zip HEAD

For the shared dossier, RepoDossier adds a deterministic `repositories/<repository-id>/` prefix and uses a temporary ZIP before merging the snapshot with the reports.

The snapshot includes files committed at `HEAD`. It excludes staged changes, unstaged changes, untracked files, ignored files, `.git` metadata, branches, tags, and repository history. A repository therefore needs at least one commit before it can be archived.

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
