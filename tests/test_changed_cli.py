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

    def fake_write_changed_export(
        repo_path: Path,
        output_path: str,
        *,
        branch: str | None,
        include_diff: bool,
    ) -> Path:
        assert repo_path == tmp_path
        assert output_path == "changed.txt"
        assert branch == "main"
        assert include_diff is False
        output = tmp_path / output_path
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

    ensured_roots: list[Path] = []

    def fake_ensure_repocontext_gitignore_entries(repository_root: Path) -> bool:
        ensured_roots.append(repository_root)
        return True

    def fake_write_changed_export(
        repo_path: Path,
        output_path: str,
        *,
        branch: str | None,
        include_diff: bool,
    ) -> Path:
        assert repo_path == tmp_path
        output = tmp_path / output_path
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

