from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDERER = REPO_ROOT / "scripts" / "dev" / "show_progress_context.py"


def test_progress_renderer_outputs_side_by_side_status_context(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("\n".join(f"roadmap line {i}" for i in range(1, 9)) + "\n", encoding="utf-8")
    milestone.write_text("\n".join(f"milestone line {i}" for i in range(1, 9)) + "\n", encoding="utf-8")

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"done","file":"ROADMAP.md","start":2,"end":2}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":3,"end":3}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"partial","file":"ROADMAP.md","start":4,"end":4}',
                '# repodossier-meta: {"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","start":5,"end":5}',
                '# repodossier-meta: {"type":"display","context":1,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, str(RENDERER), "--script", str(script), "--repo", str(tmp_path)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "ROADMAP" in result.stdout
    assert "MILESTONE" in result.stdout
    assert "✓" in result.stdout
    assert "■" in result.stdout
    assert "~" in result.stdout
    assert "!" in result.stdout
    assert "roadmap line 3" in result.stdout
    assert "milestone line 5" in result.stdout


def test_progress_renderer_uses_priority_for_overlapping_ranges(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text("one\ntwo\nthree\n", encoding="utf-8")
    milestone = tmp_path / "MILESTONE.md"
    milestone.write_text("milestone one\n", encoding="utf-8")

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"todo","file":"ROADMAP.md","start":1,"end":3}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":2,"end":2}',
                '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"MILESTONE.md","start":1,"end":1}',
                '# repodossier-meta: {"type":"display","context":0,"layout":"stacked","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, str(RENDERER), "--script", str(script), "--repo", str(tmp_path)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "■   2  two" in result.stdout

def test_progress_renderer_aligns_active_blocks_side_by_side(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text("\n".join(f"roadmap line {i}" for i in range(1, 5)) + "\n", encoding="utf-8")
    milestone = tmp_path / "MILESTONE.md"
    milestone.write_text("\n".join(f"milestone line {i}" for i in range(1, 12)) + "\n", encoding="utf-8")

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":2,"end":2}',
                '# repodossier-meta: {"type":"progress","panel":"milestone","status":"active","file":"MILESTONE.md","start":8,"end":8}',
                '# repodossier-meta: {"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, str(RENDERER), "--script", str(script), "--repo", str(tmp_path)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert any(line.count("■") == 2 for line in result.stdout.splitlines())


def test_progress_renderer_uses_fixed_width_status_markers(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("one\ntwo\nthree\n", encoding="utf-8")
    milestone.write_text("one\ntwo\nthree\n", encoding="utf-8")

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"done","file":"ROADMAP.md","start":1,"end":1}',
                '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":2,"end":2}',
                '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"MILESTONE.md","start":1,"end":1}',
                '# repodossier-meta: {"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","start":2,"end":2}',
                '# repodossier-meta: {"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, str(RENDERER), "--script", str(script), "--repo", str(tmp_path)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "✓" in result.stdout
    assert "■" in result.stdout
    assert "~" in result.stdout
    assert "!" in result.stdout
    assert "🟩" not in result.stdout
    assert "🟪" not in result.stdout
    assert "🟨" not in result.stdout
    assert "🟥" not in result.stdout


def test_progress_renderer_resolves_heading_anchor_block(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text(
        "# Roadmap\n\n## Current Work\nfirst detail\nsecond detail\n\n## Later\nlater detail\n",
        encoding="utf-8",
    )
    milestone.write_text(
        "# Milestone\n\n## Active Task\nimportant detail\n\n## Later Task\nother detail\n",
        encoding="utf-8",
    )
    meta = "# " + "repodossier-meta: "

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","anchor":"## Current Work"}',
                meta + '{"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","anchor":"## Active Task"}',
                meta + '{"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    renderer = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "show_progress_context.py"
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, str(renderer), "--script", str(script), "--repo", str(tmp_path)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## Current Work" in result.stdout
    assert "first detail" in result.stdout
    assert "second detail" in result.stdout
    assert "later detail" not in result.stdout
    assert "## Active Task" in result.stdout
    assert "important detail" in result.stdout
    assert "other detail" not in result.stdout


def test_progress_renderer_resolves_plain_text_anchor_single_line(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("one\nanchor line\nthree\n", encoding="utf-8")
    milestone.write_text("alpha\nmilestone anchor\nomega\n", encoding="utf-8")
    meta = "# " + "repodossier-meta: "

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","anchor":"anchor line"}',
                meta + '{"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","anchor":"milestone anchor"}',
                meta + '{"type":"display","context":0,"layout":"side-by-side","frame":false}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    renderer = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "show_progress_context.py"
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, str(renderer), "--script", str(script), "--repo", str(tmp_path)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "anchor line" in result.stdout
    assert "milestone anchor" in result.stdout
    assert "three" not in result.stdout
    assert "omega" not in result.stdout
