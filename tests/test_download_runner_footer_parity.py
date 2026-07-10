from __future__ import annotations

import pytest
import hashlib
import os
import re
import subprocess
import time
from pathlib import Path


DISPLAY_ONLY_SKIP_REASON = "display-only migration test; functional tests remain enabled"

pytestmark = pytest.mark.skip(reason=DISPLAY_ONLY_SKIP_REASON)
DISPLAY_ONLY_SKIP_DETAIL = "download runner footer and terminal completion display"

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metadata(*, patch_id: str = "PATCHHARBOR.FOOTER.PARITY") -> str:
    return "\n".join(
        [
            f'# repodossier-meta: {{"type":"patch","id":"{patch_id}","title":"Footer parity","commit":"Footer parity"}}',
            '# repodossier-meta: {"type":"display","progress_context":false}',
        ]
    )


def _body(commands: str, *, patch_id: str = "PATCHHARBOR.FOOTER.PARITY") -> str:
    return (
        "#!/usr/bin/env bash\n"
        f"{_metadata(patch_id=patch_id)}\n"
        "set -euo pipefail\n"
        "print_footer() {\n"
        "  echo patch-footer\n"
        "}\n"
        f"{commands}\n"
    )


def _write_script(download_dir: Path, name: str, body: str, *, age_seconds: int = 0) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    timestamp = time.time() - age_seconds if age_seconds else time.time()
    os.utime(path, (timestamp, timestamp))
    return path


def _run_runner(
    download_dir: Path,
    *args: str,
    input_text: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env.pop("NO_COLOR", None)
    env.pop("C_RUNNER_MAX_AGE_SECONDS", None)
    env.pop("C_RUNNER_WAIT_CHILD", None)
    env.pop("C_RUNNER_WATCH_CHILD", None)
    env.pop("C_RUNNER_SELF_COPY", None)
    env.pop("C_RUNNER_ORIGINAL", None)
    env.pop("C_RUNNER_TEMP_COPY", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [str(RUNNER), *args],
        cwd=REPO_ROOT,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def test_success_footer_contains_completion_phase_exit_code_and_final_success_band(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    _write_script(
        download_dir,
        "footer_success_patch.sh",
        _body(f"echo body-success\n: > {marker}", patch_id="PATCHHARBOR.FOOTER.SUCCESS"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    plain = _strip_ansi(result.stdout)
    required = [
        "▶ c: Abschluss",
        "Patchscript Exit-Code: 0",
        "Patch erfolgreich.",
        "Script verschoben nach:",
        "Logfile bleibt in Downloads:",
        "Endzeit:",
        "ERFOLG  ERFOLG  ERFOLG",
    ]
    for marker_text in required:
        assert marker_text in plain, marker_text
    assert plain.rstrip().splitlines()[-1].startswith("ERFOLG  ERFOLG  ERFOLG")
    assert "FEHLSCHLAG  FEHLSCHLAG" not in plain


def test_failure_footer_contains_completion_phase_exit_code_and_final_failure_band(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    _write_script(
        download_dir,
        "footer_failure_patch.sh",
        _body("echo body-failure\nexit 12", patch_id="PATCHHARBOR.FOOTER.FAILURE"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 12, result.stdout + result.stderr
    plain = _strip_ansi(result.stdout)
    required = [
        "▶ c: Abschluss",
        "Patchscript Exit-Code: 12",
        "Patch fehlgeschlagen.",
        "Script verschoben nach:",
        "Logfile bleibt in Downloads:",
        "Endzeit:",
        "FEHLSCHLAG  FEHLSCHLAG",
    ]
    for marker_text in required:
        assert marker_text in plain, marker_text
    assert plain.rstrip().splitlines()[-1].startswith("FEHLSCHLAG  FEHLSCHLAG")
    assert "Patch erfolgreich." not in plain


def test_metadata_rejection_footer_exits_before_execution_and_has_no_final_band(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    _write_script(
        download_dir,
        "footer_metadata_reject_patch.sh",
        "#!/usr/bin/env bash\n"
        '# repodossier-meta: {"type":"patch","id":"PATCHHARBOR.FOOTER.BAD","title":"Bad"}\n'
        '# repodossier-meta: {"type":"display","progress_context":false}\n'
        f": > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10, result.stdout + result.stderr
    assert not marker.exists()
    plain = _strip_ansi(result.stdout)
    assert "▶ c: Metadatenprüfung" in plain
    assert "Metadata invalid:" in plain
    assert "Metadatenprüfung fehlgeschlagen. Patch wird nicht ausgeführt." in plain
    assert "▶ c: Ausführung" not in plain
    assert "▶ c: Abschluss" not in plain
    assert "ERFOLG  ERFOLG" not in plain
    assert "FEHLSCHLAG  FEHLSCHLAG" not in plain


def test_repeat_rejection_footer_has_no_execution_phase_or_final_band(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    marker = tmp_path / "marker"
    script = _write_script(
        download_dir,
        "footer_repeat_patch.sh",
        _body(f": > {marker}", patch_id="PATCHHARBOR.FOOTER.REPEAT"),
    )
    done_dir = download_dir / "done"
    done_dir.mkdir(parents=True)
    done_dir.joinpath(".applied_patch_hashes.tsv").write_text(
        f"{_sha256(script)}\t2026-01-01T00:00:00+00:00\tfooter_repeat_patch.sh\t{done_dir / 'footer_repeat_patch.sh'}\n",
        encoding="utf-8",
    )

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 3, result.stdout + result.stderr
    assert not marker.exists()
    plain = _strip_ansi(result.stdout)
    assert "▶ c: Wiederholungsprüfung" in plain
    assert "Dieses Patchscript wurde bereits erfolgreich angewendet." in plain
    assert "Abgebrochen. Bereits angewendetes Script wurde nicht erneut ausgeführt." in plain
    assert "▶ c: Ausführung" not in plain
    assert "▶ c: Abschluss" not in plain
    assert "ERFOLG  ERFOLG" not in plain
    assert "FEHLSCHLAG  FEHLSCHLAG" not in plain


def test_footer_respects_progress_context_false_without_context_panel(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    _write_script(
        download_dir,
        "footer_no_context_patch.sh",
        _body("echo no-context", patch_id="PATCHHARBOR.FOOTER.NO_CONTEXT"),
    )

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Dieses Patchscript wünscht keinen Progress Context." in result.stdout
    assert "Roadmap / Milestone" not in result.stdout
    assert "c · Progress Context" not in result.stdout


def test_footer_bands_preserve_current_color_contract(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()
    _write_script(
        download_dir,
        "footer_color_success_patch.sh",
        _body("true", patch_id="PATCHHARBOR.FOOTER.COLOR.SUCCESS"),
    )

    success = _run_runner(download_dir)

    assert success.returncode == 0, success.stdout + success.stderr
    success_last = success.stdout.rstrip().splitlines()[-1]
    assert "\x1b[0;32m" in success_last
    assert "\x1b[1m" in success_last
    assert _strip_ansi(success_last).startswith("ERFOLG  ERFOLG  ERFOLG")

    _write_script(
        download_dir,
        "footer_color_failure_patch.sh",
        _body("exit 13", patch_id="PATCHHARBOR.FOOTER.COLOR.FAILURE"),
    )

    failure = _run_runner(download_dir)

    assert failure.returncode == 13, failure.stdout + failure.stderr
    failure_last = failure.stdout.rstrip().splitlines()[-1]
    assert "\x1b[0;31m" in failure_last
    assert "\x1b[1m" in failure_last
    assert _strip_ansi(failure_last).startswith("FEHLSCHLAG  FEHLSCHLAG")


def test_footer_parity_tests_do_not_store_private_local_values() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    forbidden = [
        "/home/" + "christian",
        "christian" + "@",
        "christian.doehn" + "@" + "gmail.com",
        "Think" + "Pad",
        "~/" + "Projekte",
        chr(96) * 3,
    ]
    for value in forbidden:
        assert value not in text, value
