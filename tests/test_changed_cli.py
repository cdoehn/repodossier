from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path

import pytest

from repocontext.changed_command import add_changed_subparser, run_changed_command


def test_changed_subparser_registers_output_branch_and_diff_options(capsys) -> None:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_changed_subparser(subparsers)

    help_text = parser.format_help()
    assert "changed" in help_text

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["changed", "--help"])

    assert exc_info.value.code == 0
    changed_help = capsys.readouterr().out
    assert "--output" in changed_help
    assert "--branch" in changed_help
    assert "--include-diff" in changed_help
    assert "--no-diff" in changed_help


def test_changed_command_parser_accepts_output_branch_and_no_diff() -> None:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_changed_subparser(subparsers)

    args = parser.parse_args(
        ["changed", "--output", "custom.txt", "--branch", "main", "--no-diff"]
    )

    assert args.command == "changed"
    assert args.output == "custom.txt"
    assert args.branch == "main"
    assert args.include_diff is False


def test_run_changed_command_writes_changed_export(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "repocontext.changed_command.find_repository_root",
        lambda current_path: tmp_path,
    )

    def fake_write_changed_export(
        repo_path: Path,
        output_path: Path,
        *,
        branch: str | None,
        include_diff: bool,
    ) -> Path:
        assert repo_path == tmp_path
        assert output_path == tmp_path / "changed.txt"
        assert branch == "main"
        assert include_diff is False
        output = output_path
        output.write_text("# Changed Export\n", encoding="utf-8")
        return output

    monkeypatch.setattr(
        "repocontext.changed_command.write_changed_export",
        fake_write_changed_export,
    )

    status = run_changed_command(
        Namespace(output="changed.txt", branch="main", include_diff=False)
    )

    assert status == 0
    assert "Wrote" in capsys.readouterr().out


def test_run_changed_command_ensures_repocontext_gitignore_entries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "repocontext.changed_command.find_repository_root",
        lambda current_path: tmp_path,
    )

    ensured_roots: list[Path] = []

    def fake_ensure_repocontext_gitignore_entries(repository_root: Path) -> bool:
        ensured_roots.append(repository_root)
        return True

    def fake_write_changed_export(
        repo_path: Path,
        output_path: Path,
        *,
        branch: str | None,
        include_diff: bool,
    ) -> Path:
        assert repo_path == tmp_path
        assert output_path == tmp_path / "changed.txt"
        output = output_path
        output.write_text("# Changed Export\n", encoding="utf-8")
        return output

    monkeypatch.setattr(
        "repocontext.changed_command.ensure_repocontext_gitignore_entries",
        fake_ensure_repocontext_gitignore_entries,
    )
    monkeypatch.setattr(
        "repocontext.changed_command.write_changed_export",
        fake_write_changed_export,
    )

    status = run_changed_command(
        Namespace(output="changed.txt", branch=None, include_diff=True)
    )

    assert status == 0
    assert ensured_roots == [tmp_path]


def test_changed_help_documents_all_changed_export_options(capsys) -> None:
    parser = ArgumentParser(prog="repocontext")
    subparsers = parser.add_subparsers(dest="command")
    add_changed_subparser(subparsers)

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["changed", "--help"])

    assert exc_info.value.code == 0

    help_text = capsys.readouterr().out

    assert "Generate changed.txt with changed files, unified diffs, and changed file contents." in help_text
    assert "--output OUTPUT" in help_text
    assert "Defaults to changed.txt" in help_text
    assert "--branch BRANCH" in help_text
    assert "branch...HEAD" in help_text
    assert "--include-diff" in help_text
    assert "--no-diff" in help_text
    assert "unified Git diff section" in help_text


def test_changed_help_documents_usage_examples(capsys) -> None:
    parser = ArgumentParser(prog="repocontext")
    subparsers = parser.add_subparsers(dest="command")
    add_changed_subparser(subparsers)

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["changed", "--help"])

    assert exc_info.value.code == 0

    help_text = capsys.readouterr().out

    assert "Examples:" in help_text
    assert "repocontext changed" in help_text
    assert "repocontext changed --branch main" in help_text
    assert "repocontext changed --output review-changes.txt" in help_text
    assert "repocontext changed --no-diff" in help_text

