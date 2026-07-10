from __future__ import annotations

import os
import re
import signal
import subprocess
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "dev" / "run_latest_download_patch.sh"


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", value)


def _meta() -> str:
    return "\n".join(
        [
            '# repodossier-meta: {"type":"patch","id":"TEST","title":"Test patch","commit":"Test patch"}',
            '# repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"scripts/dev/patch-rules.md","start":1,"end":1}',
            '# repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"scripts/dev/patch-rules.md","start":2,"end":2}',
            '# repodossier-meta: {"type":"display","context":1,"layout":"side-by-side","frame":false}',
        ]
    )


def _write_script(download_dir: Path, name: str, body: str, *, age_seconds: int = 0) -> Path:
    path = download_dir / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)

    if age_seconds:
        timestamp = time.time() - age_seconds
        os.utime(path, (timestamp, timestamp))

    return path


def _script_body(commands: str) -> str:
    return f"#!/usr/bin/env bash\n{_meta()}\n{commands}\n"


def _preflight_script_body(commands: str) -> str:
    return (
        f"#!/usr/bin/env bash\n{_meta()}\n"
        "print_footer() {\n"
        "  echo footer\n"
        "}\n"
        f"{commands}\n"
        "python3 -m py_compile scripts/dev/lint_patch_script.py\n"
    )


def _run_runner(download_dir: Path, *args: str, input_text: str | None = None):
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env.pop("NO_COLOR", None)
    env.pop("C_RUNNER_WAIT_CHILD", None)
    env.pop("C_RUNNER_WATCH_CHILD", None)
    env.pop("C_RUNNER_SELF_COPY", None)
    env.pop("C_RUNNER_ORIGINAL", None)
    env.pop("C_RUNNER_TEMP_COPY", None)

    return subprocess.run(
        [str(RUNNER), *args],
        cwd=REPO_ROOT,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_runner_env(download_dir: Path, *args: str, env_extra: dict[str, str] | None = None):
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
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
        text=True,
        capture_output=True,
        check=False,
    )


def _logs(download_dir: Path) -> list[Path]:
    return sorted(download_dir.glob("*.log"))


def test_c_runner_help_mentions_wait_not_daemon(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    result = _run_runner(download_dir, "--help")

    assert result.returncode == 0
    assert "c --wait" in result.stdout
    assert "--watch-up" not in result.stdout
    assert "--watch-down" not in result.stdout
    assert "--watch-status" not in result.stdout
    assert "daemon" not in result.stdout.lower()


def test_c_runner_executes_newest_script_and_moves_to_done(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    old_marker = tmp_path / "old_marker"
    latest_marker = tmp_path / "latest_marker"

    _write_script(download_dir, "older_patch.sh", _script_body(f"echo old\n: > {old_marker}"), age_seconds=30)
    latest = _write_script(download_dir, "latest_patch.sh", _script_body(f"echo latest\n: > {latest_marker}"))

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert latest_marker.exists()
    assert not old_marker.exists()
    assert not latest.exists()
    assert (download_dir / "done" / "latest_patch.sh").exists()
    assert (download_dir / "older_patch.sh").exists()
    assert "Metadaten OK" in result.stdout
    assert "latest" in result.stdout
    assert "\x1b[" in result.stdout
    assert (download_dir / "done" / ".applied_patch_hashes.tsv").exists()
    assert len(_logs(download_dir)) == 1


def test_c_runner_prints_success_banner_as_last_line(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    _write_script(download_dir, "success_banner_patch.sh", _script_body(f": > {marker}"))

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()

    last_line = result.stdout.rstrip().splitlines()[-1]
    plain = _strip_ansi(last_line)
    assert plain.startswith("ERFOLG  ERFOLG  ERFOLG")
    assert "ERFOLG" in plain
    assert "\x1b[0;32m" in last_line
    assert "\x1b[1m" in last_line


def test_c_runner_prints_progress_context_near_success_footer(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    _write_script(download_dir, "footer_context_patch.sh", _script_body(f": > {marker}"))

    result = _run_runner(download_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()

    output = result.stdout
    execution_index = output.index("Starte Patchscript mit bash")
    context_index = output.rindex("c · Progress Context")
    success_index = output.rindex("ERFOLG")

    assert context_index > execution_index
    assert context_index < success_index


def test_c_runner_rejects_invalid_metadata_before_execution(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    bad = _write_script(
        download_dir,
        "bad_meta_patch.sh",
        f"#!/usr/bin/env bash\n# repodossier-meta: {{\"type\":\"patch\",\"id\":\"BAD\"}}\n: > {marker}\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode == 10
    assert bad.exists()
    assert not marker.exists()
    assert "Metadatenprüfung fehlgeschlagen" in result.stdout


def test_c_runner_moves_failed_script_to_failed_and_keeps_log(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    failing = _write_script(download_dir, "failing_patch.sh", _script_body("echo before-fail\nexit 7"))

    result = _run_runner(download_dir)

    assert result.returncode == 7
    assert not failing.exists()
    assert (download_dir / "failed" / "failing_patch.sh").exists()
    assert "Patch fehlgeschlagen" in result.stdout
    assert "before-fail" in _logs(download_dir)[0].read_text(encoding="utf-8")


def test_c_runner_refuses_old_script_without_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    old_script = _write_script(
        download_dir,
        "old_patch.sh",
        _script_body(f": > {marker}"),
        age_seconds=61 * 60,
    )

    result = _run_runner(download_dir, input_text="n\n")

    assert result.returncode == 2
    assert old_script.exists()
    assert not marker.exists()
    assert "älter" in result.stdout


def test_c_runner_executes_old_script_after_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    old_script = _write_script(download_dir, "old_confirmed_patch.sh", _script_body(f": > {marker}"), age_seconds=61 * 60)

    result = _run_runner(download_dir, input_text="y\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists()
    assert not old_script.exists()
    assert (download_dir / "done" / "old_confirmed_patch.sh").exists()


def test_c_runner_failed_syntax_moves_script_to_failed(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    broken = _write_script(
        download_dir,
        "broken_patch.sh",
        f"#!/usr/bin/env bash\n{_meta()}\nif true; then\necho broken\n",
    )

    result = _run_runner(download_dir)

    assert result.returncode != 0
    assert not broken.exists()
    assert (download_dir / "failed" / "broken_patch.sh").exists()
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout


def test_c_runner_warns_red_and_refuses_already_applied_script(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "marker"
    body = _script_body(f"echo applied\n: > {marker}")

    first = _write_script(download_dir, "first_patch.sh", body)
    first_result = _run_runner(download_dir)

    assert first_result.returncode == 0, first_result.stdout + first_result.stderr
    assert not first.exists()

    marker.unlink()
    duplicate = _write_script(download_dir, "duplicate_patch.sh", body)
    duplicate_result = _run_runner(download_dir, input_text="n\n")

    assert duplicate_result.returncode == 3
    assert duplicate.exists()
    assert not marker.exists()
    assert "bereits erfolgreich angewendet" in duplicate_result.stdout
    assert "\x1b[0;31m" in duplicate_result.stdout


def test_c_runner_can_rerun_already_applied_script_after_confirmation(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    counter = tmp_path / "counter"
    body = _script_body(
        f"current=0\nif [ -f {counter} ]; then current=$(cat {counter}); fi\necho $((current + 1)) > {counter}"
    )

    first_result = _run_runner(download_dir, str(_write_script(download_dir, "first_patch.sh", body)))
    assert first_result.returncode == 0, first_result.stdout + first_result.stderr

    _write_script(download_dir, "duplicate_patch.sh", body)
    duplicate_result = _run_runner(download_dir, input_text="y\n")

    assert duplicate_result.returncode == 0, duplicate_result.stdout + duplicate_result.stderr
    assert counter.read_text(encoding="utf-8").strip() == "2"
    assert (download_dir / "done" / "duplicate_patch.sh").exists()


def test_c_wait_runs_fresh_new_script_in_foreground_and_keeps_waiting(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "wait_marker"
    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env["C_RUNNER_WAIT_SLEEP_SECONDS"] = "0.1"
    env["C_RUNNER_WAIT_FRESH_SECONDS"] = "30"

    process = subprocess.Popen(
        [str(RUNNER), "--wait"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        time.sleep(0.4)
        _write_script(download_dir, "wait_patch.sh", _script_body(f"echo visible-wait-output\n: > {marker}"))

        deadline = time.time() + 8
        while time.time() < deadline and not marker.exists():
            time.sleep(0.1)

        assert marker.exists()
        assert (download_dir / "done" / "wait_patch.sh").exists()

        time.sleep(0.4)
        assert process.poll() is None
    finally:
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)

    assert "Warte-Modus" in stdout
    assert "visible-wait-output" in stdout
    assert "Warte auf das nächste Script" in stdout
    assert "watch" not in stdout.lower()
    assert stderr == ""


def test_c_wait_marks_existing_scripts_seen_before_waiting(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "old_marker"
    existing = _write_script(download_dir, "already_there.sh", _script_body(f": > {marker}"))

    env = os.environ.copy()
    env["PATCH_DOWNLOAD_DIR"] = str(download_dir)
    env["C_RUNNER_WAIT_SLEEP_SECONDS"] = "0.1"
    env["C_RUNNER_WAIT_FRESH_SECONDS"] = "30"

    process = subprocess.Popen(
        [str(RUNNER), "--wait"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        time.sleep(0.8)
        assert existing.exists()
        assert not marker.exists()
    finally:
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)

    assert "Warte-Modus" in stdout
    assert stderr == ""

def test_c_runner_dry_run_checks_without_executing_or_moving(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "dry_run_marker"
    script = _write_script(
        download_dir,
        "dry_run_patch.sh",
        _preflight_script_body(f": > {marker}"),
    )

    result = _run_runner(download_dir, "--dry-run")

    assert result.returncode == 0, result.stdout + result.stderr
    assert script.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "dry_run_patch.sh").exists()
    assert not (download_dir / "failed" / "dry_run_patch.sh").exists()
    assert "Preflight OK" in result.stdout
    assert "Dry-run erfolgreich" in result.stdout
    assert "c · Progress Context" in result.stdout
    assert result.stdout.rstrip().endswith("DRY-RUN OK\x1b[0m") or result.stdout.rstrip().endswith("DRY-RUN OK")


def test_c_runner_dry_run_rejects_preflight_failure_without_moving(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    marker = tmp_path / "bad_dry_run_marker"
    script = _write_script(
        download_dir,
        "bad_dry_run_patch.sh",
        f"#!/usr/bin/env bash\n{_meta()}\n: > {marker}\n",
    )

    result = _run_runner(download_dir, "--dry-run")

    assert result.returncode == 20
    assert script.exists()
    assert not marker.exists()
    assert not (download_dir / "done" / "bad_dry_run_patch.sh").exists()
    assert not (download_dir / "failed" / "bad_dry_run_patch.sh").exists()
    assert "Preflight-Linter hat das Patchscript beanstandet" in result.stdout
    assert "missing-footer" in result.stdout


def test_c_runner_dry_run_accepts_explicit_script_path(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    first_marker = tmp_path / "first_marker"
    second_marker = tmp_path / "second_marker"
    first = _write_script(
        download_dir,
        "first_dry_run_patch.sh",
        _preflight_script_body(f": > {first_marker}"),
        age_seconds=10,
    )
    _write_script(
        download_dir,
        "second_dry_run_patch.sh",
        _preflight_script_body(f": > {second_marker}"),
    )

    result = _run_runner(download_dir, "--dry-run", str(first))

    assert result.returncode == 0, result.stdout + result.stderr
    assert first.exists()
    assert not first_marker.exists()
    assert not second_marker.exists()
    assert "first_dry_run_patch.sh" in result.stdout



def test_c_runner_dry_run_syntax_failure_does_not_move_script(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    broken = _write_script(
        download_dir,
        "dry_run_broken_patch.sh",
        f"#!/usr/bin/env bash\n{_meta()}\nprint_footer() {{ echo footer; }}\npython3 -m py_compile scripts/dev/lint_patch_script.py\nif true; then\necho broken\n",
    )

    result = _run_runner(download_dir, "--dry-run")

    assert result.returncode != 0
    assert broken.exists()
    assert not (download_dir / "done" / "dry_run_broken_patch.sh").exists()
    assert not (download_dir / "failed" / "dry_run_broken_patch.sh").exists()
    assert "Syntaxprüfung fehlgeschlagen" in result.stdout
    assert "Dry-run: Script bleibt unverändert" in result.stdout


def test_c_runner_does_not_leak_internal_env_to_patch_scripts(tmp_path: Path) -> None:
    download_dir = tmp_path / "Downloads"
    download_dir.mkdir()

    env_marker = tmp_path / "runner_env"
    script = _write_script(
        download_dir,
        "env_leak_patch.sh",
        _script_body(f"env | grep '^C_RUNNER_' > {env_marker} || true"),
    )

    result = _run_runner(download_dir, str(script))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (download_dir / "done" / "env_leak_patch.sh").exists()
    assert env_marker.read_text(encoding="utf-8") == ""


def test_c_runner_has_self_copy_guard_for_self_updates() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert 'C_RUNNER_SELF_COPY=1' in text
    assert 'exec bash "$temp_runner" "$@"' in text
    assert 'runner_source="${C_RUNNER_ORIGINAL:-${BASH_SOURCE[0]}}"' in text
    assert '-u C_RUNNER_SELF_COPY -u C_RUNNER_ORIGINAL -u C_RUNNER_TEMP_COPY bash "$patch_script"' in text
