from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from repodossier.archive_cli import (
    ArchiveCliArguments,
    DEFAULT_ARCHIVE_NAME,
    SourceReference,
    collect_source_references,
    create_archive_dossier,
    resolve_archive_inputs,
)
from repodossier.scanner import detect_language, is_source_code_language


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    result = _git(path, "init")
    assert result.returncode == 0, result.stderr
    assert _git(path, "config", "user.name", "Example User").returncode == 0
    assert _git(path, "config", "user.email", "example@example.invalid").returncode == 0
    return path


def _commit(repo: Path) -> None:
    result = _git(repo, "commit", "-m", "snapshot")
    assert result.returncode == 0, result.stderr


def _arguments(*sources: Path, output_dir: Path) -> ArchiveCliArguments:
    return ArchiveCliArguments(
        source_paths=tuple(sources),
        output_dir=output_dir,
        output_name=None,
        archive_name=DEFAULT_ARCHIVE_NAME,
    )


def _archive_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def _archive_text(path: Path, name: str) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read(name).decode("utf-8")


def test_code_classification_uses_central_language_detection() -> None:
    assert detect_language(Path("src/app.py"), "def run():\n    return 1\n") == "python"
    assert is_source_code_language("python")
    assert not is_source_code_language("markdown")
    assert not is_source_code_language(None)


def test_source_reference_reports_point_to_archived_source_without_embedding_code(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    source = repo / "src" / "backend"
    source.mkdir(parents=True)
    code_body = "UNIQUE_SOURCE_BODY_SHOULD_ONLY_BE_IN_SNAPSHOT = 42\n"
    (source / "app.py").write_text(code_body, encoding="utf-8")
    (source / "README.md").write_text("# Backend docs\n", encoding="utf-8")
    assert _git(repo, "add", "src/backend/app.py", "src/backend/README.md").returncode == 0
    _commit(repo)

    resolved = resolve_archive_inputs(_arguments(source, output_dir=tmp_path / "out"))
    result = create_archive_dossier(resolved)

    names = _archive_names(result.archive_path)
    assert "reports/source-references.txt" in names
    assert "reports/source-references.md" in names
    assert "reports/source-references.xml" in names
    assert "repositories/project/src/backend/app.py" in names

    text_report = _archive_text(result.archive_path, "reports/source-references.txt")
    markdown_report = _archive_text(result.archive_path, "reports/source-references.md")
    xml_report = _archive_text(result.archive_path, "reports/source-references.xml")

    for report in [text_report, markdown_report, xml_report]:
        assert "src/backend/app.py" in report
        assert "../repositories/project/src/backend/app.py" in report
        assert code_body.strip() not in report
        assert "Backend docs" not in report

    assert _archive_text(result.archive_path, "repositories/project/src/backend/app.py") == code_body


def test_structured_source_references_are_returned_on_archive_result(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    source = repo / "src"
    source.mkdir()
    (source / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    assert _git(repo, "add", "src/app.py").returncode == 0
    _commit(repo)

    resolved = resolve_archive_inputs(_arguments(source, output_dir=tmp_path / "out"))
    result = create_archive_dossier(resolved)

    assert len(result.source_references) == 1
    reference = result.source_references[0]
    assert isinstance(reference, SourceReference)
    assert reference.repository_id == "project"
    assert reference.repository_path == Path("src/app.py")
    assert reference.archive_path.as_posix() == "repositories/project/src/app.py"
    assert reference.report_relative_archive_path.as_posix() == "../repositories/project/src/app.py"
    assert reference.language == "python"


def test_source_references_are_limited_to_explicit_analysis_sources(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    selected = repo / "selected"
    ignored_for_analysis = repo / "other"
    selected.mkdir()
    ignored_for_analysis.mkdir()
    (selected / "app.py").write_text("print('selected')\n", encoding="utf-8")
    (ignored_for_analysis / "app.py").write_text("print('other')\n", encoding="utf-8")
    assert _git(repo, "add", "selected/app.py", "other/app.py").returncode == 0
    _commit(repo)

    resolved = resolve_archive_inputs(_arguments(selected, output_dir=tmp_path / "out"))
    result = create_archive_dossier(resolved)

    text_report = _archive_text(result.archive_path, "reports/source-references.txt")
    assert "Source file: selected/app.py" in text_report
    assert "other/app.py" not in text_report
    assert "repositories/project/other/app.py" in _archive_names(result.archive_path)


def test_source_reference_xml_is_valid_and_contains_structured_paths(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "main.py").write_text("print('xml')\n", encoding="utf-8")
    assert _git(repo, "add", "main.py").returncode == 0
    _commit(repo)

    resolved = resolve_archive_inputs(_arguments(repo, output_dir=tmp_path / "out"))
    result = create_archive_dossier(resolved)

    root = ET.fromstring(_archive_text(result.archive_path, "reports/source-references.xml"))
    source_file = root.find("source-file")
    assert source_file is not None
    assert source_file.attrib["repository-id"] == "project"
    assert source_file.attrib["language"] == "python"
    assert source_file.attrib["repository-path"] == "main.py"
    assert source_file.attrib["archive-path"] == "../repositories/project/main.py"


def test_collect_source_references_can_be_called_independently(tmp_path: Path) -> None:
    repo = _git_init(tmp_path / "project")
    (repo / "tool.sh").write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    (repo / "notes.txt").write_text("plain text\n", encoding="utf-8")
    assert _git(repo, "add", "tool.sh", "notes.txt").returncode == 0
    _commit(repo)

    resolved = resolve_archive_inputs(_arguments(repo, output_dir=tmp_path / "out"))
    result = create_archive_dossier(resolved)
    references = collect_source_references(resolved, result.snapshot_files)

    assert [reference.repository_path for reference in references] == [Path("tool.sh")]
    assert references[0].language == "bash"
