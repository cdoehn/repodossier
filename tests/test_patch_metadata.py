from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "dev" / "validate_patch_metadata.py"


def _write_script(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_validate_patch_metadata_accepts_patch_display_and_progress(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
            '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"scripts/dev/patch-rules.md","start":1,"end":1}',
            '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"scripts/dev/patch-rules.md","start":2,"end":2}',
            '# repodossier-meta: {"type":"display","context":2,"layout":"side-by-side","frame":false}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Metadata OK" in result.stdout


def test_validate_patch_metadata_rejects_missing_patch_record(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"display","context":2}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "expected exactly one patch" in result.stdout


def test_validate_patch_metadata_rejects_unknown_status(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
            '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"unknown","file":"scripts/dev/patch-rules.md","start":1,"end":1}',
            '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"scripts/dev/patch-rules.md","start":2,"end":2}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "status must be one of" in result.stdout


def test_validate_patch_metadata_rejects_missing_file(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
            '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"done","file":"missing.md","start":1,"end":1}',
            '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"scripts/dev/patch-rules.md","start":2,"end":2}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "file does not exist" in result.stdout

def test_validate_patch_metadata_rejects_missing_progress_records(tmp_path: Path) -> None:
    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            '# repodossier-meta: {"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
            '# repodossier-meta: {"type":"display","context":2}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(REPO_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "missing required roadmap progress metadata record" in result.stdout
    assert "missing required milestone progress metadata record" in result.stdout


def test_patch_metadata_accepts_progress_anchor_records(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("# Roadmap\n\n## Current Work\nbody\n", encoding="utf-8")
    milestone.write_text("# Milestone\n\n## Active Task\nbody\n", encoding="utf-8")
    meta = "# " + "repodossier-meta: "

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","anchor":"## Current Work"}',
                meta + '{"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","anchor":"## Active Task"}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    validator = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "validate_patch_metadata.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--script", str(script), "--repo", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Metadata OK" in result.stdout


def test_patch_metadata_rejects_missing_progress_location(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("# Roadmap\n", encoding="utf-8")
    milestone.write_text("# Milestone\n", encoding="utf-8")
    meta = "# " + "repodossier-meta: "

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md"}',
                meta + '{"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","anchor":"# Milestone"}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    validator = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "validate_patch_metadata.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--script", str(script), "--repo", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert 'progress metadata must provide either "start"/"end" or "anchor"' in result.stdout


def test_patch_metadata_rejects_missing_anchor_text(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("# Roadmap\n", encoding="utf-8")
    milestone.write_text("# Milestone\n", encoding="utf-8")
    meta = "# " + "repodossier-meta: "

    script = tmp_path / "patch.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                meta + '{"type":"patch","id":"DEV.X","title":"Demo","commit":"Demo commit"}',
                meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","anchor":"## Missing"}',
                meta + '{"type":"progress","panel":"milestone","status":"todo","file":"MILESTONE.md","anchor":"# Milestone"}',
                "echo ok",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    validator = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "validate_patch_metadata.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--script", str(script), "--repo", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "anchor not found in file" in result.stdout




def test_validate_patch_metadata_accepts_display_progress_context_false_without_progress_records(tmp_path: Path) -> None:
    meta = "# " + "repodossier-" + "meta: "

    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            meta + '{"type":"patch","id":"DEV.DISPLAY","title":"Demo","commit":"Demo commit"}',
            meta + '{"type":"display","context":2,"layout":"side-by-side","frame":false,"progress_context":false}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Metadata OK" in result.stdout

def test_validate_patch_metadata_rejects_non_boolean_display_progress_context(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("# Roadmap\nbody\n", encoding="utf-8")
    milestone.write_text("# Milestone\nbody\n", encoding="utf-8")
    meta = "# " + "repodossier-" + "meta: "

    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            meta + '{"type":"patch","id":"DEV.DISPLAY","title":"Demo","commit":"Demo commit"}',
            meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":1,"end":2}',
            meta + '{"type":"progress","panel":"milestone","status":"partial","file":"MILESTONE.md","start":1,"end":2}',
            meta + '{"type":"display","context":2,"layout":"side-by-side","frame":false,"progress_context":"no"}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert 'field "progress_context" must be a boolean' in result.stdout


def test_validate_patch_metadata_rejects_display_progress_context_false_with_progress_records(tmp_path: Path) -> None:
    roadmap = tmp_path / "ROADMAP.md"
    milestone = tmp_path / "MILESTONE.md"
    roadmap.write_text("# Roadmap\nbody\n", encoding="utf-8")
    milestone.write_text("# Milestone\nbody\n", encoding="utf-8")
    meta = "# " + "repodossier-" + "meta: "

    target = _write_script(
        tmp_path / "patch.sh",
        [
            "#!/usr/bin/env bash",
            meta + '{"type":"patch","id":"DEV.DISPLAY","title":"Demo","commit":"Demo commit"}',
            meta + '{"type":"progress","panel":"roadmap","status":"active","file":"ROADMAP.md","start":1,"end":2}',
            meta + '{"type":"progress","panel":"milestone","status":"partial","file":"MILESTONE.md","start":1,"end":2}',
            meta + '{"type":"display","context":2,"layout":"side-by-side","frame":false,"progress_context":false}',
            "echo ok",
        ],
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--script", str(target), "--repo", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 10
    assert "display progress_context=false must not be combined with progress metadata records" in result.stdout
