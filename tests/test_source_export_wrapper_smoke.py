from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R_WRAPPER = ROOT / "scripts" / "dev" / "r.sh"
EXPORT_RUNNER = ROOT / "scripts" / "dev" / "run_repodossier_exports.sh"
WRAPPER_DRAFT = ROOT / "planning" / "patchharbor" / "source-export-wrapper-draft.md"


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=path, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _fake_repodossier_bin(base: Path, *, fail_mode: str | None = None) -> Path:
    bin_dir = base / "bin"
    bin_dir.mkdir(parents=True)
    fake = bin_dir / "repodossier"
    lines = [
        "#!/usr/bin/env bash",
        "set -u",
        'calls_file="${FAKE_REPODOSSIER_CALLS:?missing FAKE_REPODOSSIER_CALLS}"',
        'printf "%s\\n" "$*" >> "$calls_file"',
        'mode="$1"',
        f'fail_mode="{fail_mode or ""}"',
        'if [ -n "$fail_mode" ] && [ "$mode" = "$fail_mode" ]; then',
        "  exit 17",
        "fi",
        'case "$mode" in',
        "  full)",
        "    printf 'full export\\n' > full.txt",
        "    ;;",
        "  export-ai)",
        "    printf 'ai export\\n' > ai.txt",
        "    ;;",
        "  export-docs)",
        "    printf 'docs export\\n' > docs.txt",
        "    ;;",
        "  changed)",
        "    printf 'changed export\\n' > changed.txt",
        "    ;;",
        "  *)",
        "    exit 23",
        "    ;;",
        "esac",
    ]
    fake.write_text("\n".join(lines) + "\n", encoding="utf-8")
    fake.chmod(0o755)
    return fake


def _run_r(
    repo: Path,
    downloads: Path,
    fake_bin: Path | None,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(downloads)
    env.pop("NO_COLOR", None)
    if fake_bin is not None:
        env["REPODOSSIER_BIN"] = str(fake_bin)
        env["FAKE_REPODOSSIER_CALLS"] = str(downloads / "fake-repodossier-calls.txt")
    else:
        env["REPODOSSIER_BIN"] = "repodossier-missing-for-smoke-test"
    return subprocess.run(
        ["bash", str(R_WRAPPER), *args],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_source_export_wrapper_smoke_list_modes_uses_current_runner_contract(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    downloads = tmp_path / "Downloads"
    fake_bin = _fake_repodossier_bin(tmp_path)

    result = _run_r(repo, downloads, fake_bin, "--list-modes")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == ["all", "full", "ai", "docs", "changed"]
    assert not downloads.exists()


def test_source_export_wrapper_smoke_default_dry_run_keeps_current_mode_expansion(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    downloads = tmp_path / "Downloads"
    fake_bin = _fake_repodossier_bin(tmp_path)

    result = _run_r(repo, downloads, fake_bin, "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "r · RepoDossier Export Runner" in result.stdout
    assert "Modi: full ai docs changed" in result.stdout
    assert "Befehl: " in result.stdout
    assert "repodossier full" in result.stdout
    assert "repodossier export-ai" in result.stdout
    assert "repodossier export-docs" in result.stdout
    assert "repodossier changed" in result.stdout
    assert "Dry-run: keine Dateien geschrieben." in result.stdout
    assert "r abgeschlossen." in result.stdout
    assert not (downloads / "full.txt").exists()
    assert not (downloads / "ai.txt").exists()
    assert not (downloads / "docs.txt").exists()
    assert not (downloads / "changed.txt").exists()


def test_source_export_wrapper_smoke_default_run_exports_full_and_ai_only(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    downloads = tmp_path / "Downloads"
    fake_bin = _fake_repodossier_bin(tmp_path)

    result = _run_r(repo, downloads, fake_bin)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Modi: full ai" in result.stdout
    assert "Exportiere full" in result.stdout
    assert "Exportiere ai" in result.stdout
    assert "r abgeschlossen." in result.stdout
    assert (downloads / "full.txt").read_text(encoding="utf-8") == "full export\n"
    assert (downloads / "ai.txt").read_text(encoding="utf-8") == "ai export\n"
    assert not (downloads / "docs.txt").exists()
    assert not (downloads / "changed.txt").exists()
    calls = (downloads / "fake-repodossier-calls.txt").read_text(encoding="utf-8").splitlines()
    assert calls == ["full", "export-ai"]


def test_source_export_wrapper_smoke_alias_modes_and_patch_rules_copy(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    rules = repo / "scripts" / "dev" / "patch-rules.md"
    rules.parent.mkdir(parents=True)
    rules.write_text("rules\n", encoding="utf-8")
    downloads = tmp_path / "Downloads"
    fake_bin = _fake_repodossier_bin(tmp_path)

    result = _run_r(repo, downloads, fake_bin, "quick", "doc", "changes")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Modi: ai docs changed" in result.stdout
    assert (downloads / "ai.txt").exists()
    assert (downloads / "docs.txt").exists()
    assert (downloads / "changed.txt").exists()
    assert (downloads / "patch-rules.md").read_text(encoding="utf-8") == "rules\n"
    calls = (downloads / "fake-repodossier-calls.txt").read_text(encoding="utf-8").splitlines()
    assert calls == ["export-ai", "export-docs", "changed"]


def test_source_export_wrapper_smoke_unknown_mode_exits_with_usage(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    downloads = tmp_path / "Downloads"
    fake_bin = _fake_repodossier_bin(tmp_path)

    result = _run_r(repo, downloads, fake_bin, "unknown-mode")

    assert result.returncode == 2
    assert "Unbekannter r-Modus: unknown-mode" in result.stdout
    assert "Usage:" in result.stdout


def test_source_export_wrapper_smoke_missing_repodossier_bin_fails_before_modes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    downloads = tmp_path / "Downloads"

    result = _run_r(repo, downloads, None)

    assert result.returncode == 1
    assert "RepoDossier-Befehl nicht gefunden:" in result.stdout
    assert not downloads.exists()


def test_source_export_wrapper_smoke_not_in_git_repo_fails_before_command_lookup(tmp_path: Path) -> None:
    repo = tmp_path / "not-a-git-repo"
    repo.mkdir()
    downloads = tmp_path / "Downloads"
    fake_bin = _fake_repodossier_bin(tmp_path)

    result = _run_r(repo, downloads, fake_bin)

    assert result.returncode == 1
    assert "Kein Git-Repository:" in result.stdout
    assert not downloads.exists()


def test_source_export_wrapper_smoke_export_command_failure_preserves_exit_code(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    downloads = tmp_path / "Downloads"
    fake_bin = _fake_repodossier_bin(tmp_path, fail_mode="export-ai")

    result = _run_r(repo, downloads, fake_bin)

    assert result.returncode == 17
    assert "Exportiere full" in result.stdout
    assert "Exportiere ai" in result.stdout
    assert "ai fehlgeschlagen. Exit-Code: 17" in result.stdout
    assert (downloads / "full.txt").exists()
    assert not (downloads / "ai.txt").exists()


def test_source_export_wrapper_smoke_does_not_change_productive_files() -> None:
    assert R_WRAPPER.exists()
    assert EXPORT_RUNNER.exists()
    assert WRAPPER_DRAFT.exists()
    wrapper = R_WRAPPER.read_text(encoding="utf-8")
    runner = EXPORT_RUNNER.read_text(encoding="utf-8")
    draft = WRAPPER_DRAFT.read_text(encoding="utf-8")

    assert "run_repodossier_exports.sh" in wrapper
    assert "REPODOSSIER_BIN" in runner
    assert "PATCH_DOWNLOAD_DIR" in runner
    assert "PATCHHARBOR.11c2 should add source export wrapper smoke tests" in draft


def test_source_export_wrapper_smoke_tests_do_not_store_private_local_values() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    forbidden = [
        "/home/" + "exampleuser",
        "user" + "@",
        "example.user" + "@" + "example.invalid",
        "Example" + "Laptop",
        "~/" + "Projects",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text, value
