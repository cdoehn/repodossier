import os
import subprocess
import sys
from pathlib import Path


def run_command(repo: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "repodossier", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr + result.stdout


def test_secret_detection_masks_generated_exports_end_to_end(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)

    source_secret = "sk-live-1234567890abcdefSOURCESECRET"
    docs_secret = "ghp_1234567890abcdefDOCSSECRET"
    changed_secret = "changed-token-1234567890abcdefSECRET"

    (repo / "pyproject.toml").write_text(
        "[project]\n"
        'name = "secret-e2e-repo"\n'
        'version = "0.1.0"\n',
        encoding="utf-8",
    )
    (repo / "config.py").write_text(
        f'OPENAI_API_KEY = "{source_secret}"\n'
        "def safe_function():\n"
        "    return True\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text(
        "# Secret E2E Repo\n\n"
        f'GITHUB_TOKEN = "{docs_secret}"\n\n'
        "This README intentionally contains a fake token for export masking tests.\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=RepoDossier Test",
            "-c",
            "user.email=repodossier@example.invalid",
            "commit",
            "-m",
            "initial",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src_path = str(project_root / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

    for command in [["full"], ["export-ai"], ["export-docs"]]:
        assert_success(run_command(repo, command, env))

    (repo / "config.py").write_text(
        f'OPENAI_API_KEY = "{source_secret}"\n'
        f'ACCESS_TOKEN = "{changed_secret}"\n'
        "def safe_function():\n"
        "    return True\n",
        encoding="utf-8",
    )

    assert_success(run_command(repo, ["changed"], env))

    generated_files = [
        repo / "full.txt",
        repo / "ai.txt",
        repo / "docs.txt",
        repo / "changed.txt",
    ]

    for generated_file in generated_files:
        assert generated_file.exists(), f"{generated_file.name} was not generated"
        content = generated_file.read_text(encoding="utf-8")
        assert source_secret not in content
        assert docs_secret not in content
        assert changed_secret not in content

    full_text = (repo / "full.txt").read_text(encoding="utf-8")
    ai_text = (repo / "ai.txt").read_text(encoding="utf-8")
    docs_text = (repo / "docs.txt").read_text(encoding="utf-8")
    changed_text = (repo / "changed.txt").read_text(encoding="utf-8")

    assert "# Secret Detection" in full_text
    assert "# Secret Detection" in docs_text
    assert "# Secret Detection" in changed_text
    assert "***REDACTED***" in full_text
    assert "***REDACTED***" in docs_text
    assert "***REDACTED***" in changed_text
    assert "Potential secrets masked in changed export" in changed_text

    if "***REDACTED***" in ai_text:
        assert "# Secret Detection" in ai_text
