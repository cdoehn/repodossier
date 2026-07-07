from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTER = REPO_ROOT / "scripts" / "dev" / "lint_patch_script.py"


def _write_script(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _valid_script(tmp_path: Path, commands: str = "python3 -m py_compile scripts/dev/validate_patch_metadata.py\nprint_footer\n") -> Path:
    return _write_script(
        tmp_path / "patch.sh",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"TEST","title":"Test patch","commit":"Test patch"}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"scripts/dev/patch-rules.md","start":1,"end":1}',
                '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"scripts/dev/patch-rules.md","start":2,"end":2}',
                '# repodossier-meta: {"type":"display","context":1,"layout":"side-by-side","frame":false}',
                "print_footer() {",
                "  echo footer",
                "}",
                commands,
            ]
        )
        + "\n",
    )


def _run_linter(script: Path):
    return subprocess.run(
        [sys.executable, str(LINTER), "--script", str(script), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_lint_patch_script_accepts_valid_patch(tmp_path: Path) -> None:
    script = _valid_script(tmp_path)

    result = _run_linter(script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Patch preflight OK" in result.stdout


def test_lint_patch_script_rejects_missing_metadata(tmp_path: Path) -> None:
    script = _write_script(
        tmp_path / "patch.sh",
        "#!/usr/bin/env bash\nprint_footer() { echo footer; }\npython3 -m py_compile scripts/dev/validate_patch_metadata.py\n",
    )

    result = _run_linter(script)

    assert result.returncode == 20
    assert "metadata" in result.stdout
    assert "missing required repodossier-meta block" in result.stdout


def test_lint_patch_script_rejects_bundle_project(tmp_path: Path) -> None:
    script = _valid_script(tmp_path, "./bundle_project.sh\npython3 -m py_compile scripts/dev/validate_patch_metadata.py\n")

    result = _run_linter(script)

    assert result.returncode == 20
    assert "no-bundle-project" in result.stdout


def test_lint_patch_script_rejects_own_global_tee_logging(tmp_path: Path) -> None:
    script = _valid_script(tmp_path, "exec > >(tee patch.log) 2>&1\npython3 -m py_compile scripts/dev/validate_patch_metadata.py\n")

    result = _run_linter(script)

    assert result.returncode == 20
    assert "no-global-tee-log" in result.stdout


def test_lint_patch_script_rejects_clipboard_tools(tmp_path: Path) -> None:
    script = _valid_script(tmp_path, "echo bad | xclip -selection clipboard\npython3 -m py_compile scripts/dev/validate_patch_metadata.py\n")

    result = _run_linter(script)

    assert result.returncode == 20
    assert "no-clipboard" in result.stdout


def test_lint_patch_script_allows_git_diff_and_forbidden_terms_in_quoted_diagnostics(tmp_path: Path) -> None:
    script = _valid_script(
        tmp_path,
        "echo \"git diff --cached --quiet is documented here\"\n"
        "echo 'bundle_project.sh xclip aider git diff are quoted diagnostics'\n"
        "python3 -m py_compile scripts/dev/validate_patch_metadata.py\n",
    )

    result = _run_linter(script)

    assert result.returncode == 0, result.stdout + result.stderr


def test_lint_patch_script_rejects_git_diff_without_no_pager(tmp_path: Path) -> None:
    script = _valid_script(tmp_path, "git diff -- src\npython3 -m py_compile scripts/dev/validate_patch_metadata.py\n")

    result = _run_linter(script)

    assert result.returncode == 20
    assert "git-no-pager" in result.stdout


def test_lint_patch_script_allows_git_diff_quiet_commit_guard(tmp_path: Path) -> None:
    script = _valid_script(
        tmp_path,
        "if git diff --cached --quiet; then\n"
        "  echo nothing-to-commit\n"
        "fi\n"
        "python3 -m py_compile scripts/dev/validate_patch_metadata.py\n",
    )

    result = _run_linter(script)

    assert result.returncode == 0, result.stdout + result.stderr


def test_lint_patch_script_allows_git_no_pager_diff(tmp_path: Path) -> None:
    script = _valid_script(tmp_path, "git --no-pager diff -- src\npython3 -m py_compile scripts/dev/validate_patch_metadata.py\n")

    result = _run_linter(script)

    assert result.returncode == 0, result.stdout + result.stderr


def test_lint_patch_script_rejects_missing_footer(tmp_path: Path) -> None:
    script = _write_script(
        tmp_path / "patch.sh",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"TEST","title":"Test patch","commit":"Test patch"}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"scripts/dev/patch-rules.md","start":1,"end":1}',
                '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"scripts/dev/patch-rules.md","start":2,"end":2}',
                "python3 -m py_compile scripts/dev/validate_patch_metadata.py",
            ]
        )
        + "\n",
    )

    result = _run_linter(script)

    assert result.returncode == 20
    assert "missing-footer" in result.stdout


def test_lint_patch_script_rejects_literal_triple_backticks(tmp_path: Path) -> None:
    fence = chr(96) * 3
    script = _valid_script(
        tmp_path,
        f"cat > README.md <<'EOF'\n{fence}\nEOF\npython3 -m py_compile scripts/dev/validate_patch_metadata.py\n",
    )

    result = _run_linter(script)

    assert result.returncode == 20
    assert "literal-triple-backtick" in result.stdout


def test_lint_patch_script_ignores_forbidden_terms_inside_test_fixture_heredoc(tmp_path: Path) -> None:
    script = _valid_script(
        tmp_path,
        "\n".join(
            [
                "cat > tests/test_fixture.py <<'PYTEST'",
                "def test_fixture_strings():",
                "    assert 'bundle_project.sh' in 'bundle_project.sh'",
                "    assert 'xclip' in 'xclip'",
                "    assert 'aider' in 'aider'",
                "    assert 'git diff' in 'git diff'",
                "PYTEST",
                "python3 -m py_compile scripts/dev/validate_patch_metadata.py",
                "",
            ]
        ),
    )

    result = _run_linter(script)

    assert result.returncode == 0, result.stdout + result.stderr


def test_lint_patch_script_still_checks_commands_after_heredoc(tmp_path: Path) -> None:
    script = _valid_script(
        tmp_path,
        "\n".join(
            [
                "cat > tests/test_fixture.py <<'PYTEST'",
                "def test_fixture_strings():",
                "    assert 'bundle_project.sh' in 'bundle_project.sh'",
                "PYTEST",
                "git diff -- src",
                "python3 -m py_compile scripts/dev/validate_patch_metadata.py",
                "",
            ]
        ),
    )

    result = _run_linter(script)

    assert result.returncode == 20
    assert "git-no-pager" in result.stdout
