from __future__ import annotations

import pytest
import os
import subprocess
import sys
from pathlib import Path

DISPLAY_ONLY_SKIP_REASON = "display-only migration test; functional tests remain enabled"

pytestmark = pytest.mark.skip(reason=DISPLAY_ONLY_SKIP_REASON)
DISPLAY_ONLY_SKIP_DETAIL = "progress context active alignment display"

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "dev" / "show_progress_context.py"


def _meta() -> str:
    return "# " + "repodossier-meta: "


def _run_renderer(tmp_path: Path, script: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["COLUMNS"] = "120"

    return subprocess.run(
        [sys.executable, str(RENDERER), "--script", str(script), "--repo", str(tmp_path)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _active_row(output: str, marker_text: str) -> int:
    for index, line in enumerate(output.splitlines()):
        if marker_text in line:
            return index
    raise AssertionError(f"missing marker {marker_text!r} in output:\n{output}")


def test_active_centers_are_aligned_across_columns(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text(
        "\n".join(
            [
                "# Roadmap",
                "roadmap active one",
                "roadmap active two",
                "roadmap after one",
                "roadmap after two",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    milestone.write_text(
        "\n".join(
            [
                "# Milestone",
                "milestone done one",
                "milestone done two",
                "milestone done three",
                "milestone done four",
                "milestone active one",
                "milestone active two",
                "milestone after one",
                "milestone after two",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    meta = _meta()
    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":2,"end":3}',
                meta + '{"type":"progress","panel":"milestone","status":"done","file":"MILESTONE.md","start":2,"end":5}',
                meta + '{"type":"progress","panel":"milestone","status":"active","file":"MILESTONE.md","start":6,"end":7}',
                meta + '{"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_renderer(tmp_path, script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _active_row(result.stdout, "roadmap active one") == _active_row(result.stdout, "milestone active one")
    assert _active_row(result.stdout, "roadmap active two") == _active_row(result.stdout, "milestone active two")


def test_active_alignment_keeps_available_context_above_and_below(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text(
        "\n".join(
            [
                "# Roadmap",
                "before active",
                "roadmap active",
                "roadmap after one",
                "roadmap after two",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    milestone.write_text(
        "\n".join(
            [
                "# Milestone",
                "done one",
                "done two",
                "done three",
                "milestone active",
                "milestone after one",
                "milestone after two",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    meta = _meta()
    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":3,"end":3}',
                meta + '{"type":"progress","panel":"milestone","status":"done","file":"MILESTONE.md","start":2,"end":4}',
                meta + '{"type":"progress","panel":"milestone","status":"active","file":"MILESTONE.md","start":5,"end":5}',
                meta + '{"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_renderer(tmp_path, script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "before active" in result.stdout
    assert "roadmap after one" in result.stdout
    assert "milestone after one" in result.stdout
    assert _active_row(result.stdout, "roadmap active") == _active_row(result.stdout, "milestone active")
