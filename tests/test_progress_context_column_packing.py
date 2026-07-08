from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "dev" / "show_progress_context.py"


def _metadata_prefix() -> str:
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


def test_progress_context_packs_each_panel_independently(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text(
        "\n".join(
            [
                "# Roadmap",
                "done one",
                "done two",
                "active starts immediately",
                "active continues",
                "roadmap fill one",
                "roadmap fill two",
                "roadmap fill three",
                "roadmap fill four",
                "roadmap fill five",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    milestone.write_text(
        "\n".join(["# Milestone", *[f"long done {number}" for number in range(1, 13)]])
        + "\n",
        encoding="utf-8",
    )

    meta = _metadata_prefix()
    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo"}',
                meta + '{"type":"progress","panel":"roadmap","status":"done","file":"ROADMAP.md","start":2,"end":3}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":4,"end":5}',
                meta + '{"type":"progress","panel":"milestone","status":"done","file":"MILESTONE.md","start":2,"end":13}',
                meta + '{"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_renderer(tmp_path, script)

    assert result.returncode == 0, result.stdout + result.stderr
    done_index = result.stdout.index("done two")
    active_index = result.stdout.index("active starts immediately")
    milestone_tail_index = result.stdout.index("long done 12")

    assert done_index < active_index < milestone_tail_index


def test_progress_context_fills_shorter_panel_with_available_following_text(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text(
        "\n".join(
            [
                "# Roadmap",
                "selected",
                "fill after one",
                "fill after two",
                "fill after three",
                "fill after four",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    milestone.write_text(
        "\n".join(["# Milestone", "selected", "more one", "more two", "more three", "more four"])
        + "\n",
        encoding="utf-8",
    )

    meta = _metadata_prefix()
    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":2,"end":2}',
                meta + '{"type":"progress","panel":"milestone","status":"done","file":"MILESTONE.md","start":2,"end":6}',
                meta + '{"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_renderer(tmp_path, script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "fill after one" in result.stdout
    assert "fill after two" in result.stdout
    assert "more four" in result.stdout


def test_progress_context_keeps_anchor_support(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("# Roadmap\n\n## Current\nbody\n\n## Later\nlater\n", encoding="utf-8")
    milestone.write_text("# Milestone\n\n## Active\nimportant\n\n## Later\nother\n", encoding="utf-8")

    meta = _metadata_prefix()
    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","anchor":"## Current"}',
                meta + '{"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","anchor":"## Active"}',
                meta + '{"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_renderer(tmp_path, script)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## Current" in result.stdout
    assert "body" in result.stdout
    assert "later" not in result.stdout
    assert "## Active" in result.stdout
    assert "important" in result.stdout
    assert "other" not in result.stdout
