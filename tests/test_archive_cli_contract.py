from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from repodossier.archive_cli import (
    DEFAULT_ARCHIVE_NAME,
    ArchiveCliArgumentError,
    build_archive_parser,
    parse_archive_cli_arguments,
    split_archive_positionals,
)
from repodossier.cli import main

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"


def _git_init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return path


def test_split_archive_positionals_requires_source_and_output() -> None:
    with pytest.raises(ArchiveCliArgumentError):
        split_archive_positionals([])

    with pytest.raises(ArchiveCliArgumentError):
        split_archive_positionals(["only-one-path"])


def test_split_archive_positionals_treats_last_argument_as_output_folder() -> None:
    sources, output_dir = split_archive_positionals(["repo-a", "repo-b", "out"])

    assert sources == (Path("repo-a"), Path("repo-b"))
    assert output_dir == Path("out")


def test_archive_parser_accepts_output_name_with_any_extension() -> None:
    parser = build_archive_parser("1.0.0")
    namespace = parser.parse_args(["repo", "out", "--output-name", "projektstand.xml"])
    arguments = parse_archive_cli_arguments(namespace)

    assert arguments.source_paths == (Path("repo"),)
    assert arguments.output_dir == Path("out")
    assert arguments.output_name == "projektstand.xml"
    assert arguments.archive_filename == "projektstand.xml"


def test_archive_parser_uses_default_archive_name() -> None:
    parser = build_archive_parser("1.0.0")
    namespace = parser.parse_args(["repo", "out"])
    arguments = parse_archive_cli_arguments(namespace)

    assert arguments.output_name is None
    assert arguments.archive_name == DEFAULT_ARCHIVE_NAME
    assert arguments.archive_filename == DEFAULT_ARCHIVE_NAME


def test_main_reports_error_for_no_positionals(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "usage:" in captured.err
    assert "at least two positional arguments are required" in captured.err
    assert "QUELLE [QUELLE ...] AUSGABEORDNER" in captured.err


def test_main_reports_error_for_one_positional(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["repo"])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "usage:" in captured.err
    assert "one or more source folders followed by the output folder" in captured.err


def test_main_rejects_non_git_source(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    source = tmp_path / "plain"
    source.mkdir()

    exit_code = main([str(source), str(tmp_path / "out")])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "not inside a Git repository" in captured.err


def test_main_accepts_two_positionals(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "repo")
    output_dir = tmp_path / "out"

    exit_code = main([str(repo), str(output_dir)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "RepoDossier archive CLI contract accepted." in captured.out
    assert "Sources: 1" in captured.out
    assert f"Output folder: {output_dir}" in captured.out
    assert "Archive filename: repodossier-archive.zip" in captured.out
    assert "Repositories: 1" in captured.out


def test_main_accepts_multiple_sources_and_output_name(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    repo_a = _git_init(tmp_path / "repo-a")
    repo_b = _git_init(tmp_path / "repo-b")
    output_dir = tmp_path / "out"

    exit_code = main([str(repo_a), str(repo_b), str(output_dir), "--output-name", "mein-paket.zip"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Sources: 2" in captured.out
    assert "Archive filename: mein-paket.zip" in captured.out
    assert "Repositories: 2" in captured.out


def test_help_screen_describes_archive_contract() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(SRC_ROOT), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)

    result = subprocess.run(
        [sys.executable, "-m", "repodossier", "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    help_text = result.stdout
    assert "RepoDossier creates one compressed ZIP dossier" in help_text
    assert "repodossier [OPTIONEN] QUELLE [QUELLE ...] AUSGABEORDNER" in help_text
    assert "Das letzte Positionsargument ist immer der Ausgabeordner" in help_text
    assert "--output-name" in help_text
    assert "reports/" in help_text
    assert "repositories/" in help_text
    assert "repodossier ./repository ./output" in help_text
    assert "repodossier ./repository-a ./repository-b ./output" in help_text
    assert "repodossier ./repository/backend ./repository/frontend ./output" in help_text
    assert "projektstand.xml" in help_text


def test_short_help_alias_works() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(SRC_ROOT), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)

    result = subprocess.run(
        [sys.executable, "-m", "repodossier", "-h"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "--output-name" in result.stdout


def test_pyproject_declares_installable_console_entry_point() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "repodossier"
    assert data["project"]["scripts"]["repodossier"] == "repodossier.cli:main"
    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
