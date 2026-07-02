from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def run_repodossier(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src_path = str(project_root / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

    return subprocess.run(
        [sys.executable, "-m", "repodossier", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def write_file(repo: Path, relative_path: str, content: str) -> None:
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_language_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    write_file(repo, "README.md", "# Example\n\nDocumentation body.\n")
    write_file(repo, "scripts/python-tool", "#!/usr/bin/env python3\nprint('ok')\n")
    write_file(repo, "scripts/node-tool", "#!/usr/bin/env node\nconsole.log('ok');\n")
    write_file(repo, "src/app.ts", "export const value: string = 'ok';\n")
    write_file(repo, "src/main.js", "console.log('ok');\n")
    write_file(repo, "web/index.html", "<!DOCTYPE html>\n<html></html>\n")
    write_file(repo, "web/styles.css", "body { margin: 0; color: black; }\n")
    write_file(repo, "src/App.java", "public class App {}\n")
    write_file(repo, "src/main.c", "#include <stdio.h>\nint main(void) { return 0; }\n")
    write_file(repo, "src/main.cpp", "#include <iostream>\nint main() { return 0; }\n")
    write_file(repo, "src/App.cs", "using System;\npublic class App {}\n")
    write_file(repo, "include/user.h", "namespace demo { class User {}; }\n")

    run_git(repo, "init")
    run_git(repo, "add", ".")
    run_git(repo, "-c", "user.name=RepoDossier Test", "-c", "user.email=repodossier@example.invalid", "commit", "-m", "init")

    return repo


def test_cli_full_export_uses_new_language_detection_end_to_end(tmp_path: Path) -> None:
    repo = create_language_fixture_repo(tmp_path)

    result = run_repodossier(repo, "full")

    assert result.returncode == 0, result.stderr + result.stdout

    full_text = (repo / "full.txt").read_text(encoding="utf-8")
    fence = chr(96) * 3

    for readable_language in [
        "TypeScript",
        "JavaScript",
        "HTML",
        "CSS",
        "Java",
        "C",
        "C++",
        "C#",
        "Python",
    ]:
        assert readable_language in full_text

    assert "## File: src/app.ts" in full_text
    assert f"{fence}typescript\nexport const value: string = 'ok';\n{fence}" in full_text

    assert "## File: src/main.js" in full_text
    assert f"{fence}javascript\nconsole.log('ok');\n{fence}" in full_text

    assert "## File: web/index.html" in full_text
    assert f"{fence}html\n<!DOCTYPE html>\n<html></html>\n{fence}" in full_text

    assert "## File: web/styles.css" in full_text
    assert f"{fence}css\nbody {{ margin: 0; color: black; }}\n{fence}" in full_text

    assert "## File: src/App.java" in full_text
    assert f"{fence}java\npublic class App {{}}\n{fence}" in full_text

    assert "## File: src/main.c" in full_text
    assert f"{fence}c\n#include <stdio.h>\nint main(void) {{ return 0; }}\n{fence}" in full_text

    assert "## File: src/main.cpp" in full_text
    assert f"{fence}cpp\n#include <iostream>\nint main() {{ return 0; }}\n{fence}" in full_text

    assert "## File: src/App.cs" in full_text
    assert f"{fence}csharp\nusing System;\npublic class App {{}}\n{fence}" in full_text

    assert "## File: include/user.h" in full_text
    assert f"{fence}cpp\nnamespace demo {{ class User {{}}; }}\n{fence}" in full_text

    assert "## File: scripts/python-tool" in full_text
    assert f"{fence}python\n#!/usr/bin/env python3\nprint('ok')\n{fence}" in full_text

    assert "## File: scripts/node-tool" in full_text
    assert f"{fence}javascript\n#!/usr/bin/env node\nconsole.log('ok');\n{fence}" in full_text


def test_cli_ai_export_tolerates_new_language_files_end_to_end(tmp_path: Path) -> None:
    repo = create_language_fixture_repo(tmp_path)

    result = run_repodossier(repo, "export-ai")

    assert result.returncode == 0, result.stderr + result.stdout

    ai_text = (repo / "ai.txt").read_text(encoding="utf-8")

    assert "# AI CONTEXT" in ai_text
    assert "## Symbol Index" in ai_text
    assert "## Import Graph" in ai_text
    assert "## Call Graph" in ai_text
    assert "Traceback" not in ai_text
    assert "Exception" not in ai_text


def test_cli_docs_export_keeps_documentation_scope_with_new_languages(tmp_path: Path) -> None:
    repo = create_language_fixture_repo(tmp_path)

    result = run_repodossier(repo, "export-docs")

    assert result.returncode == 0, result.stderr + result.stdout

    docs_text = (repo / "docs.txt").read_text(encoding="utf-8")

    assert "README.md" in docs_text
    assert "Documentation body." in docs_text
    assert "src/app.ts" not in docs_text
    assert "src/main.js" not in docs_text
    assert "web/index.html" not in docs_text
    assert "web/styles.css" not in docs_text
    assert "src/App.java" not in docs_text
    assert "src/main.c" not in docs_text
    assert "src/main.cpp" not in docs_text
    assert "src/App.cs" not in docs_text
    assert "include/user.h" not in docs_text
