from __future__ import annotations

from pathlib import Path

import pytest

from scripts.dev.check_dev_environment import (
    CheckResult,
    _check_category,
    _is_required_check,
    render_results,
)


def test_render_results_reports_success() -> None:
    output = render_results(
        [
            CheckResult("repo root", True, "/tmp/repo_dossier"),
            CheckResult("git user.name", True, "RepoDossier Developer"),
        ]
    )

    assert "[OK] repo root: /tmp/repo_dossier" in output
    assert "OK: development environment looks ready." in output


def test_render_results_reports_hints_for_failures() -> None:
    output = render_results(
        [
            CheckResult("git user.email", False, "not configured", "git config --global user.email user@example.com"),
        ]
    )

    assert "[FAIL] git user.email: not configured" in output
    assert "hint: git config --global user.email user@example.com" in output
    assert "FAILED: 1 check(s) need attention." in output


def test_collect_checks_can_run_inside_repo() -> None:
    from scripts.dev.check_dev_environment import collect_checks

    repo_root = Path(__file__).resolve().parents[1]
    results = collect_checks(repo_root)

    names = {result.name for result in results}
    assert "repo root" in names
    assert "python" in names
    assert "pytest" in names
    assert "c runner" in names
    assert "workflow rules" in names


def test_main_returns_failure_outside_git_repo(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.dev.check_dev_environment import main

    status = main(["--repo", str(tmp_path)])

    captured = capsys.readouterr()
    assert status == 2
    assert "[FAIL] repo root" in captured.out



def test_required_and_category_mapping_preserves_legacy_optional_tools() -> None:
    assert _is_required_check("python")
    assert _is_required_check("pytest")
    assert not _is_required_check("repodossier cli")
    assert not _is_required_check("pipx")
    assert _check_category("git user.email") == "git"
    assert _check_category("c runner") == "source-helper"
    assert _check_category("workflow rules validator") == "source-helper"


def test_check_dev_environment_tests_do_not_add_private_literals() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    old_user = "chris" + "tian"
    old_person = old_user + "." + "doehn"
    old_mail_host = "g" + "mail" + "." + "com"
    forbidden = [
        "/home/" + old_user,
        old_user + "@",
        old_person + "@" + old_mail_host,
        ("Th" + "ink") + ("Pa" + "d"),
        ("Bl" + "ade") + "-" + "15",
        "~/" + ("Pro" + "jek" + "te"),
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text
