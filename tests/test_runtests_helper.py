from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTESTS = ROOT / "runtests"
WRAPPER = ROOT / "scripts" / "dev" / "runtests.sh"
DOC = ROOT / "docs" / "runtests.md"


class RepoDossierRunTestsHelperTests(unittest.TestCase):
    def test_runtests_script_exists_and_is_executable(self) -> None:
        self.assertTrue(RUNTESTS.is_file())
        self.assertTrue(os.access(RUNTESTS, os.X_OK))

    def test_dev_wrapper_exists_and_is_executable(self) -> None:
        self.assertTrue(WRAPPER.is_file())
        self.assertTrue(os.access(WRAPPER, os.X_OK))

    def test_scripts_are_bash_syntax_valid(self) -> None:
        for script in [RUNTESTS, WRAPPER]:
            with self.subTest(script=script):
                result = subprocess.run(
                    ["bash", "-n", str(script)],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_does_not_create_virtual_environment(self) -> None:
        before_exists = (ROOT / ".venv").exists()
        result = subprocess.run(
            [str(RUNTESTS), "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--no-install", result.stdout)
        self.assertIn("--recreate-venv", result.stdout)
        self.assertIn("RUNTESTS_NO_INSTALL", result.stdout)
        self.assertEqual((ROOT / ".venv").exists(), before_exists)

    def test_runtests_documentation_covers_install_logs_and_safety(self) -> None:
        self.assertTrue(DOC.is_file())
        text = DOC.read_text(encoding="utf-8")
        required = [
            "./runtests",
            "--no-install",
            "--recreate-venv",
            "--python python3.12",
            "pyproject.toml",
            ".runtests/",
            "wl-copy",
            "install anything globally",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_runtests_documentation_contains_validation_markers(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        required = [
            "python -m venv",
            "python -m pytest",
            "tests/test_runtests_helper.py",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_runtests_log_directory_is_gitignored(self) -> None:
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".runtests/", text)

    def test_runtests_files_do_not_store_private_local_values_or_fences(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [RUNTESTS, WRAPPER, DOC, Path(__file__).resolve()]
        )
        forbidden = [
            "/home/" + "exampleuser",
            "example.user" + "@" + "example.invalid",
            "Example" + "Laptop",
            "Example" + "Machine",
            "~/" + "Projects",
            chr(96) * 3,
        ]
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, text)


if __name__ == "__main__":
    unittest.main()
