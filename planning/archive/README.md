# Planning Archive

This directory stores historical planning records by release version.

## Release archives

- `1.0.0/` contains the original `roadmap.md` and `milestone*.md` files that led to RepoContext 1.0.0.

Future release archives should be added as separate version directories instead of mixing files together.

Suggested layout:

    archive/
    ├── 1.0.0/
    │   ├── roadmap.md
    │   ├── milestone2.md
    │   ├── milestone3.md
    │   └── milestone18.md
    ├── 1.1.0/
    │   ├── roadmap.md
    │   └── milestone1.md
    └── 2.0.0/
        ├── roadmap.md
        └── milestone1.md

Naming rule:

- Use `roadmap.md` for the roadmap inside each release archive.
- Use lowercase milestone filenames such as `milestone4.md`.
- Do not use uppercase archive names such as `MILESTONE4.md`.

Each release archive may contain its own roadmap, milestone files, release notes, or implementation notes.
