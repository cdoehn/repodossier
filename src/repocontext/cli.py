"""Command-line interface entrypoint for RepoContext."""

from __future__ import annotations

from .dependencies import append_dependencies_full_section

import argparse
from importlib import metadata
from pathlib import Path
from typing import Iterable, Optional

from .exporters import generate_ai_export, generate_docs_export, generate_full_export
from .git import RepositoryInfo, find_repository_root, get_repository_info
from .gitignore import GitignoreUpdateError
from .import_graph import build_import_graph, calculate_import_graph_metrics
from repocontext.changed_command import add_changed_subparser, run_changed_command
from repocontext.config import ConfigError, load_config_from_args, set_active_config, with_config_arguments


_FALLBACK_VERSION = "0.1.0.dev0"


def _determine_version() -> str:
    """Return the installed package version or a fallback value."""
    try:
        return metadata.version("repocontext")
    except metadata.PackageNotFoundError:
        return _FALLBACK_VERSION


def _print_repository_info(repository_info: RepositoryInfo) -> None:
    """Display repository information for the CLI."""
    print("Repository info:")
    name_display = repository_info.name if repository_info.name is not None else "unknown"
    print(f"  Name: {name_display}")
    print(f"  Root: {repository_info.root_path}")
    print(f"  Current directory is root: {'yes' if repository_info.is_current_directory_root else 'no'}")
    branch_display = repository_info.branch if repository_info.branch is not None else "unknown"
    print(f"  Branch: {branch_display}")
    commit_display = repository_info.commit_hash if repository_info.commit_hash is not None else "unknown"
    print(f"  Commit: {commit_display}")
    short_commit_display = repository_info.short_commit_hash if repository_info.short_commit_hash is not None else "unknown"
    print(f"  Short commit: {short_commit_display}")
    remote_display = repository_info.remote_url if repository_info.remote_url is not None else "none"
    print(f"  Remote: {remote_display}")
    dirty_status = repository_info.is_dirty
    if dirty_status is None:
        print("  Dirty: unknown")
    else:
        print(f"  Dirty: {'yes' if dirty_status else 'no'}")
    commit_metadata = repository_info.commit_metadata
    if commit_metadata is None:
        print("  Commit author: unknown")
        print("  Commit date: unknown")
        print("  Commit subject: unknown")
    else:
        author_name = commit_metadata.author_name or "unknown"
        author_email = commit_metadata.author_email or "unknown"
        commit_date = commit_metadata.commit_date or "unknown"
        subject = commit_metadata.subject or "unknown"
        print(f"  Commit author: {author_name} <{author_email}>")
        print(f"  Commit date: {commit_date}")
        print(f"  Commit subject: {subject}")
    print(f"  Tracked files: {len(repository_info.tracked_files)}")



def _python_source_paths_from_repository_info(repository_info: RepositoryInfo) -> tuple[Path, ...]:
    """Return Git-tracked Python source paths for import graph analysis."""

    return tuple(
        repository_info.root_path / tracked_file.path
        for tracked_file in repository_info.tracked_files
        if tracked_file.path.suffix == ".py"
    )


def _print_import_graph_info(repository_info: RepositoryInfo) -> None:
    """Display a compact import graph summary for the info command."""

    print("Import graph:")

    try:
        import_graph = build_import_graph(
            _python_source_paths_from_repository_info(repository_info),
            repo_root=repository_info.root_path,
        )
        metrics = calculate_import_graph_metrics(import_graph)
    except Exception as exc:
        print("  Status: unavailable")
        print(f"  Error: {type(exc).__name__}: {exc}")
        return

    print(f"  Python modules: {metrics.module_count}")
    print(f"  Import dependencies: {metrics.local_dependency_count}")
    print(f"  External imports: {metrics.external_import_count}")
    print(f"  Unresolved imports: {metrics.unresolved_import_count}")
    print(f"  Analysis errors: {metrics.error_count}")


def _find_repository_root_or_report_error() -> Optional[Path]:
    repository_root = find_repository_root()
    if repository_root is None:
        print("Error: Could not determine the repository root.")
        return None
    return repository_root


def _handle_full_export_command(_args: argparse.Namespace) -> int:
    """Run the default export command and write full.txt plus ai.txt."""
    repository_root = _find_repository_root_or_report_error()
    if repository_root is None:
        return 1

    try:
        full_output_path = generate_full_export(repository_root)
        ai_output_path = generate_ai_export(repository_root)
    except GitignoreUpdateError as exc:
        print(f"Error: Could not update .gitignore: {exc}")
        return 1
    except OSError as exc:
        print(f"Error: Could not write export files: {exc}")
        return 1

    print(f"Wrote {full_output_path}")
    print(f"Wrote {ai_output_path}")
    return 0


def _handle_ai_export_command(_args: argparse.Namespace) -> int:
    """Run the AI Export command and write ai.txt."""
    repository_root = _find_repository_root_or_report_error()
    if repository_root is None:
        return 1

    try:
        output_path = generate_ai_export(repository_root)
    except GitignoreUpdateError as exc:
        print(f"Error: Could not update .gitignore: {exc}")
        return 1
    except OSError as exc:
        print(f"Error: Could not write ai.txt: {exc}")
        return 1

    print(f"Wrote {output_path}")
    return 0


def _handle_docs_export_command(_args: argparse.Namespace) -> int:
    """Run the documentation export command and write docs.txt."""
    repository_root = _find_repository_root_or_report_error()
    if repository_root is None:
        return 1

    try:
        output_path = generate_docs_export(repository_root)
    except GitignoreUpdateError as exc:
        print(f"Error: Could not update .gitignore: {exc}")
        return 1
    except OSError as exc:
        print(f"Error: Could not write docs.txt: {exc}")
        return 1

    print(f"Wrote {output_path}")
    return 0


def _handle_info_command(_args: argparse.Namespace) -> int:
    """Run the repository info command."""
    repository_root = _find_repository_root_or_report_error()
    if repository_root is None:
        return 1

    repository_info = get_repository_info(repository_root)
    _print_repository_info(repository_info)
    _print_import_graph_info(repository_info)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(prog="repocontext")
    parser.add_argument("--version", action="version", version=_determine_version())

    subparsers = parser.add_subparsers(dest="command")

    add_changed_subparser(subparsers)

    info_parser = subparsers.add_parser("info", help="Show repository info")
    info_parser.set_defaults(handler=_handle_info_command)

    full_parser = with_config_arguments(subparsers.add_parser("full", help="Generate full.txt and ai.txt exports"))
    full_parser.set_defaults(handler=_handle_full_export_command)

    export_parser = subparsers.add_parser("export", help="Generate full.txt and ai.txt exports")
    export_parser.set_defaults(handler=_handle_full_export_command)

    ai_export_parser = with_config_arguments(subparsers.add_parser("export-ai", help="Generate ai.txt export"))
    ai_export_parser.set_defaults(handler=_handle_ai_export_command)

    docs_export_parser = with_config_arguments(subparsers.add_parser("export-docs", help="Generate docs.txt export"))
    docs_export_parser.set_defaults(handler=_handle_docs_export_command)

    parser.set_defaults(handler=_handle_full_export_command)
    return parser


def _main_without_export_secret_safety_net(argv: Optional[Iterable[str]] = None) -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    _load_config_for_cli_args(arguments)
    return arguments.handler(arguments)







def _repocontext_cli_repository_root() -> object:
    """Return the nearest Git repository root or the current directory."""

    from pathlib import Path

    current = Path.cwd()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate

    return current


def _mask_known_exports_after_cli_command(argv: object = None) -> None:
    """Mask generated export files after CLI commands complete."""

    import sys
    from pathlib import Path

    from repocontext.secrets import mask_export_file

    raw_args = list(sys.argv[1:] if argv is None else argv)
    repo_root = Path(_repocontext_cli_repository_root())

    export_targets = {
        "full": (
            "full.txt",
            "Potential secrets were masked before full export was written.",
        ),
        "export-ai": (
            "ai.txt",
            "Potential secrets were masked before AI export was written.",
        ),
        "export-docs": (
            "docs.txt",
            "Potential secrets were masked before documentation export was written.",
        ),
        "changed": (
            "changed.txt",
            "Potential secrets masked in changed export.",
        ),
    }

    for command, target in export_targets.items():
        if command not in raw_args:
            continue

        filename, summary = target
        mask_export_file(repo_root / filename, filename, summary)





def _repocontext_export_safety_root() -> object:
    """Return the nearest Git repository root or current directory."""

    from pathlib import Path

    current = Path.cwd()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate

    return current


def _repocontext_mask_known_export_files() -> None:
    """Apply final secret masking to known generated export files."""

    from pathlib import Path

    from repocontext.secrets import mask_export_file

    root = Path(_repocontext_export_safety_root())

    targets = [
        (
            "full.txt",
            "Potential secrets were masked before full export was written.",
        ),
        (
            "ai.txt",
            "Potential secrets were masked before AI export was written.",
        ),
        (
            "docs.txt",
            "Potential secrets were masked before documentation export was written.",
        ),
        (
            "changed.txt",
            "Potential secrets masked in changed export.",
        ),
    ]

    for filename, summary in targets:
        mask_export_file(root / filename, filename, summary)

def _load_config_for_cli_args(arguments):
    """Load RepoContext config for subcommands that expose config options."""

    has_config_options = hasattr(arguments, "config_path") or hasattr(arguments, "no_config")
    if not has_config_options:
        return None

    try:
        config = load_config_from_args(arguments)
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    setattr(arguments, "repocontext_config", config)
    set_active_config(config)
    return config

def main(*args: object, **kwargs: object) -> object:
    """Run the CLI and apply final export secret masking."""

    result = _main_without_export_secret_safety_net(*args, **kwargs)

    argv = None
    if args and isinstance(args[0], list):
        argv = args[0]
    elif "argv" in kwargs:
        argv = kwargs["argv"]

    _mask_known_exports_after_cli_command(argv)
    return result
_REPOCONTEXT_DEPENDENCY_FULL_EXPORT_HOOK = True


def _repocontext_add_dependencies_to_full_export(full_text, local_values):
    """Add dependency information to full.txt text right before it is written."""

    if not isinstance(full_text, str):
        return full_text

    repo_root = _repocontext_dependency_repo_root_from_locals(local_values)
    files = _repocontext_dependency_files_from_locals(local_values)

    return append_dependencies_full_section(full_text, repo_root, files=files)


def _repocontext_dependency_repo_root_from_locals(local_values):
    from pathlib import Path as _Path
    import os as _os

    for key in (
        "repo_root",
        "repository_root",
        "project_root",
        "root",
        "base_path",
        "workdir",
        "cwd",
    ):
        value = local_values.get(key)
        candidate = _repocontext_dependency_path_from_value(value)
        if candidate is not None and candidate.exists() and candidate.is_dir():
            return candidate

    for key in (
        "output_path",
        "output_file",
        "full_path",
        "full_txt_path",
        "full_output_path",
        "full_file",
    ):
        value = local_values.get(key)
        candidate = _repocontext_dependency_path_from_value(value)
        if candidate is not None:
            if candidate.name == "full.txt":
                return candidate.parent
            if candidate.exists() and candidate.is_dir():
                return candidate

    files = _repocontext_dependency_files_from_locals(local_values)
    if files:
        absolute_paths = []
        for file_item in files:
            path_value = _repocontext_dependency_path_from_value(file_item)
            if path_value is not None and path_value.is_absolute():
                absolute_paths.append(path_value)

        if absolute_paths:
            common = _Path(_os.path.commonpath([path.as_posix() for path in absolute_paths]))
            if common.is_file():
                common = common.parent
            if common.exists():
                return common

    return _Path.cwd()


def _repocontext_dependency_files_from_locals(local_values):
    for key in (
        "files",
        "scanned_files",
        "file_infos",
        "file_reports",
        "source_files",
        "project_files",
    ):
        value = local_values.get(key)
        files = _repocontext_dependency_files_from_value(value)
        if files is not None:
            return files

    for value in local_values.values():
        files = _repocontext_dependency_files_from_value(value)
        if files is not None:
            return files

    return None


def _repocontext_dependency_files_from_value(value):
    if value is None or isinstance(value, (str, bytes, dict)):
        return None

    try:
        items = list(value)
    except TypeError:
        return None

    if not items:
        return None

    path_like_count = 0
    for item in items:
        if _repocontext_dependency_path_from_value(item) is not None:
            path_like_count += 1

    if path_like_count == 0:
        return None

    return items


def _repocontext_dependency_path_from_value(value):
    from pathlib import Path as _Path

    if isinstance(value, (str, _Path)):
        try:
            return _Path(value)
        except TypeError:
            return None

    for attribute_name in (
        "absolute_path",
        "relative_path",
        "path",
        "repo_root",
        "repository_root",
        "project_root",
        "root",
        "name",
    ):
        attribute_value = getattr(value, attribute_name, None)
        if isinstance(attribute_value, (str, _Path)):
            try:
                return _Path(attribute_value)
            except TypeError:
                return None

    return None

if __name__ == "__main__":
    raise SystemExit(main())
