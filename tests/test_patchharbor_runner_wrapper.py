from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/dev/run_patchharbor_patch.sh"


class PatchHarborRunnerWrapperTests(unittest.TestCase):
    def test_wrapper_file_exists_and_is_executable(self) -> None:
        self.assertTrue(WRAPPER.exists())
        self.assertTrue(os.access(WRAPPER, os.X_OK))

    def test_existing_source_runner_and_exports_are_preserved(self) -> None:
        preserved = [
            ROOT / "scripts/dev/run_latest_download_patch.sh",
            ROOT / "scripts/dev/install_aliases.sh",
            ROOT / "scripts/dev/r.sh",
            ROOT / "scripts/dev/run_repodossier_exports.sh",
            ROOT / "scripts/dev/repo_patch_helper.py",
            ROOT / "scripts/dev/show_progress_context.py",
        ]
        for path in preserved:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), str(path))

    def test_wrapper_is_thin_explicit_patchharbor_runner_bridge(self) -> None:
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("#!/usr/bin/env bash", text)
        self.assertIn("set -euo pipefail", text)
        self.assertIn('exec patchharbor run-script "$@"', text)
        self.assertNotIn("done", text)
        self.assertNotIn("failed", text)
        self.assertNotIn("install_aliases", text)
        self.assertNotIn("run_repodossier_exports", text)

    def test_wrapper_has_valid_bash_syntax(self) -> None:
        result = subprocess.run(["bash", "-n", str(WRAPPER)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_wrapper_delegates_to_patchharbor_and_forwards_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            log = temp / "args.txt"
            stub = temp / "patchharbor"
            stub.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$@\" > \"$PATCHHARBOR_STUB_LOG\"\n",
                encoding="utf-8",
            )
            stub.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = str(temp) + os.pathsep + env.get("PATH", "")
            env["PATCHHARBOR_STUB_LOG"] = str(log)

            result = subprocess.run(
                [str(WRAPPER), "example.sh", "--no-execute", "--env", "KEY=VALUE"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                log.read_text(encoding="utf-8").splitlines(),
                ["run-script", "example.sh", "--no-execute", "--env", "KEY=VALUE"],
            )

    def test_wrapper_patch_does_not_create_alias_or_shell_files(self) -> None:
        self.assertFalse((ROOT / ".bashrc").exists())
        self.assertFalse((ROOT / ".zshrc").exists())
        self.assertFalse((ROOT / "scripts/dev/c.sh").exists())

    def test_wrapper_files_do_not_store_private_local_values(self) -> None:
        checked = [
            ROOT / "scripts/dev/run_patchharbor_patch.sh",
            ROOT / "tests/test_patchharbor_runner_wrapper.py",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in checked)
        forbidden = [
            "/home/" + "christian",
            "christian" + "@",
            "christian.doehn" + "@" + "gmail.com",
            "Think" + "Pad",
            "~/" + "Projekte",
            chr(96) * 3,
        ]
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, text)


if __name__ == "__main__":
    unittest.main()
