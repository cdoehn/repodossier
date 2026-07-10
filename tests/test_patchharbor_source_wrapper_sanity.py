from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/dev/run_patchharbor_patch.sh"


def find_patchharbor_repo() -> Path:
    candidates: list[Path] = []
    env_value = os.environ.get("PATCHHARBOR_TARGET_REPO")
    if env_value:
        candidates.append(Path(env_value).expanduser())
    candidates.extend([ROOT.parent / "patch-harbor", ROOT.parent / "patchharbor"])
    for candidate in candidates:
        if (candidate / "src/patchharbor").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate.resolve()
    raise AssertionError("PatchHarbor target repository not available for sanity test")


def write_target_patch(path: Path, sentinel: Path) -> None:
    meta = "# " + "patchharbor-" + "meta: "
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                f'{meta}{{"type":"patch","id":"PATCHHARBOR.SANITY","title":"Sanity","commit":"Sanity"}}',
                f'{meta}{{"type":"progress","panel":"roadmap","status":"active","file":"docs/example.md","label":"Roadmap"}}',
                f'{meta}{{"type":"progress","panel":"milestone","status":"active","file":"docs/example.md","label":"Milestone"}}',
                f'{meta}{{"type":"display","context":2,"layout":"side-by-side","frame":false}}',
                "set -euo pipefail",
                f'printf "ran" > "{sentinel}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_source_wrapper_invokes_real_patchharbor_cli_in_no_execute_mode() -> None:
    target = find_patchharbor_repo()

    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        sentinel = temp / "sentinel.txt"
        patch = temp / "sanity_patch.sh"
        write_target_patch(patch, sentinel)

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
            [str(WRAPPER), str(patch), "--no-execute", "--max-age-seconds", "20"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PatchHarbor run-script" in result.stdout
        assert "runner status: passed" in result.stdout
        assert "phase metadata: passed" in result.stdout
        assert "phase execute: skipped" in result.stdout
        assert not sentinel.exists()


def test_source_wrapper_sanity_test_has_no_private_values() -> None:
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
        assert value not in text
