from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/dev/run_patchharbor_patch.sh"


def find_patchharbor_repo() -> Path | None:
    candidates: list[Path] = []
    env_value = os.environ.get("PATCHHARBOR_TARGET_REPO")
    if env_value:
        candidates.append(Path(env_value).expanduser())
    candidates.extend(
        [
            ROOT.parent / "patch-harbor",
            ROOT.parent / "patchharbor",
        ]
    )
    for candidate in candidates:
        if (candidate / "src/patchharbor").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate.resolve()
    return None


class PatchHarborRunnerWrapperSmokeTests(unittest.TestCase):
    def test_wrapper_can_drive_real_patchharbor_no_execute_smoke(self) -> None:
        target = find_patchharbor_repo()
        if target is None:
            self.skipTest("PatchHarbor target repository not available for smoke test")

        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            sentinel = temp / "sentinel.txt"
            script = temp / "patch.sh"
            script.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env bash
                    # patchharbor-meta: {"type":"patch","id":"PATCHHARBOR.SOURCE.SMOKE","title":"Source smoke","commit":"Source smoke"}
                    # patchharbor-meta: {"type":"progress","panel":"roadmap","status":"active","file":"docs/example.md","label":"Roadmap"}
                    # patchharbor-meta: {"type":"progress","panel":"milestone","status":"active","file":"docs/example.md","label":"Milestone"}
                    # patchharbor-meta: {"type":"display","context":2,"layout":"side-by-side","frame":false}
                    set -euo pipefail
                    printf smoke > "$PATCHHARBOR_SENTINEL"
                    """
                ),
                encoding="utf-8",
            )

            shim = temp / "patchharbor"
            shim.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "PYTHONPATH=\"$PATCHHARBOR_TARGET_REPO/src${PYTHONPATH:+:$PYTHONPATH}\" "
                "exec python3 -m patchharbor \"$@\"\n",
                encoding="utf-8",
            )
            shim.chmod(0o755)

            env = os.environ.copy()
            env["PATCHHARBOR_TARGET_REPO"] = str(target)
            env["PATCHHARBOR_SENTINEL"] = str(sentinel)
            env["PATH"] = str(temp) + os.pathsep + env.get("PATH", "")

            result = subprocess.run(
                [
                    str(WRAPPER),
                    str(script),
                    "--no-execute",
                    "--max-age-seconds",
                    "20",
                    "--env",
                    f"PATCHHARBOR_SENTINEL={sentinel}",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PatchHarbor run-script", result.stdout)
            self.assertIn("runner status: passed", result.stdout)
            self.assertIn("phase execute: skipped", result.stdout)
            self.assertFalse(sentinel.exists())

    def test_wrapper_no_execute_smoke_does_not_create_lifecycle_directories(self) -> None:
        target = find_patchharbor_repo()
        if target is None:
            self.skipTest("PatchHarbor target repository not available for smoke test")

        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            script = temp / "patch.sh"
            script.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env bash
                    # patchharbor-meta: {"type":"patch","id":"PATCHHARBOR.SOURCE.LIFECYCLE","title":"Lifecycle smoke","commit":"Lifecycle smoke"}
                    # patchharbor-meta: {"type":"progress","panel":"roadmap","status":"active","file":"docs/example.md","label":"Roadmap"}
                    # patchharbor-meta: {"type":"progress","panel":"milestone","status":"active","file":"docs/example.md","label":"Milestone"}
                    # patchharbor-meta: {"type":"display","context":2,"layout":"side-by-side","frame":false}
                    set -euo pipefail
                    true
                    """
                ),
                encoding="utf-8",
            )

            shim = temp / "patchharbor"
            shim.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "PYTHONPATH=\"$PATCHHARBOR_TARGET_REPO/src${PYTHONPATH:+:$PYTHONPATH}\" "
                "exec python3 -m patchharbor \"$@\"\n",
                encoding="utf-8",
            )
            shim.chmod(0o755)

            env = os.environ.copy()
            env["PATCHHARBOR_TARGET_REPO"] = str(target)
            env["PATH"] = str(temp) + os.pathsep + env.get("PATH", "")

            result = subprocess.run(
                [str(WRAPPER), str(script), "--no-execute", "--max-age-seconds", "20"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((temp / "done").exists())
            self.assertFalse((temp / "failed").exists())

    def test_smoke_test_file_does_not_store_private_local_values(self) -> None:
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
            with self.subTest(value=value):
                self.assertNotIn(value, text)


if __name__ == "__main__":
    unittest.main()
