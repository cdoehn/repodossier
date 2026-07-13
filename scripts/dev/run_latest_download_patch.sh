#!/usr/bin/env bash
set -u

if [ "${C_RUNNER_SELF_COPY:-0}" != "1" ]; then
  original_runner="${BASH_SOURCE[0]}"
  temp_runner="$(mktemp "${TMPDIR:-/tmp}/repodossier-c-runner.XXXXXX.sh")"
  cp "$original_runner" "$temp_runner"
  chmod +x "$temp_runner"
  C_RUNNER_SELF_COPY=1 C_RUNNER_ORIGINAL="$original_runner" C_RUNNER_TEMP_COPY="$temp_runner" exec bash "$temp_runner" "$@"
fi

if [ -n "${C_RUNNER_TEMP_COPY:-}" ]; then
  trap 'rm -f "$C_RUNNER_TEMP_COPY" 2>/dev/null || true' EXIT
fi

download_dir="${PATCH_DOWNLOAD_DIR:-$HOME/Downloads}"
done_dir="$download_dir/done"
failed_dir="$download_dir/failed"
applied_ledger="$done_dir/.applied_patch_hashes.tsv"
wait_seen="$download_dir/.repodossier-c-wait.seen"
max_age_seconds="${C_RUNNER_MAX_AGE_SECONDS:-3600}"
wait_sleep_seconds="${C_RUNNER_WAIT_SLEEP_SECONDS:-2}"
wait_fresh_seconds="${C_RUNNER_WAIT_FRESH_SECONDS:-30}"
show_progress_context=1
progress_context_explicit=0
if [ "${C_RUNNER_PROGRESS_CONTEXT+x}" = "x" ]; then
  progress_context_explicit=1
  case "${C_RUNNER_PROGRESS_CONTEXT:-1}" in
    0|false|False|FALSE|no|No|NO|off|Off|OFF)
      show_progress_context=0
      ;;
    *)
      show_progress_context=1
      ;;
  esac
fi
if [ "$#" -gt 0 ]; then
  c_runner_filtered_args=()
  for c_runner_arg in "$@"; do
    case "$c_runner_arg" in
      --no-progress-context|--no-context)
        show_progress_context=0
        progress_context_explicit=1
        ;;
      *)
        c_runner_filtered_args+=("$c_runner_arg")
        ;;
    esac
  done
  set -- "${c_runner_filtered_args[@]}"
fi
zip_extract_dir=""

cleanup_c_runner() {
  if [ -n "${C_RUNNER_TEMP_COPY:-}" ]; then
    rm -f "$C_RUNNER_TEMP_COPY" 2>/dev/null || true
  fi
  if [ -n "${zip_extract_dir:-}" ]; then
    rm -rf "$zip_extract_dir" 2>/dev/null || true
  fi
}
trap cleanup_c_runner EXIT

runner_source="${C_RUNNER_ORIGINAL:-${BASH_SOURCE[0]}}"
if [ -n "${C_RUNNER_TEMP_COPY:-}" ] && [ -x "${REPODOSSIER_REPO:-$(pwd)}/scripts/dev/run_latest_download_patch.sh" ]; then
  runner_source="${REPODOSSIER_REPO:-$(pwd)}/scripts/dev/run_latest_download_patch.sh"
fi
runner_dir="$(cd "$(dirname "$runner_source")" && pwd)"
runner_repo="$(cd "$runner_dir/../.." && pwd)"
progress_renderer="$runner_dir/show_progress_context.py"

C_USE_COLOR=1
if [ -n "${NO_COLOR:-}" ] || [ "${C_RUNNER_COLOR:-auto}" = "never" ]; then
  C_USE_COLOR=0
fi

if [ "$C_USE_COLOR" -eq 1 ]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_ACCENT=$'\033[38;5;45m'
  C_INFO=$'\033[38;5;39m'
  C_OK=$'\033[0;32m'
  C_WARN=$'\033[1;33m'
  C_ERR=$'\033[0;31m'
  C_PATH=$'\033[0;36m'
  C_STEP=$'\033[0;35m'
else
  C_RESET=''
  C_BOLD=''
  C_ACCENT=''
  C_INFO=''
  C_OK=''
  C_WARN=''
  C_ERR=''
  C_PATH=''
  C_STEP=''
fi

usage() {
  cat <<'USAGE'
Usage:
  c
  c /path/to/patch.sh
  c /path/to/patch.zip
  c --no-progress-context /path/to/patch.sh
  c --no-context /path/to/patch.zip
  c --dry-run [path/to/patch.sh]
  c --wait
  c --help

Dry-run mode:
  c --dry-run validates the selected patch through metadata, progress,
  freshness, repetition and bash syntax checks, but does not
  execute it and does not move it to done/failed.

Normal mode:
  c validates metadata, checks freshness and repetition, runs one patch script,
  moves it to done/failed, logs output, prints progress context near the end,
  and prints a full-width ERFOLG or FEHLSCHLAG banner as the final line.

Foreground wait mode:
  c --wait blocks in the current terminal, waits for the next fresh *.sh file
  directly in the download directory, runs it through normal c execution, and then waits
  again. The output stays visible in the terminal. Stop with Ctrl+C.

Wait mode safety:
  - foreground-only wait loop
  - no root execution
  - only *.sh or *.zip patch files directly in the download directory
  - only scripts modified within the last 30 seconds
  - valid repodossier-meta with roadmap and milestone progress
  - bash -n must pass
  - SHA-256 hash must not already be applied
  - each seen script/hash is started only once
USAGE
}

banner() {
  printf '\n'
  printf '%b\n' "${C_ACCENT}${C_BOLD}╔════════════════════════════════════════════════════════════╗${C_RESET}"
  printf '%b\n' "${C_ACCENT}${C_BOLD}║ c · RepoDossier Download Patch Runner                     ║${C_RESET}"
  printf '%b\n' "${C_ACCENT}${C_BOLD}╚════════════════════════════════════════════════════════════╝${C_RESET}"
}

section() {
  printf '\n%b\n' "${C_ACCENT}${C_BOLD}▶ c:${C_RESET} ${C_STEP}${C_BOLD}$1${C_RESET}"
}

info() {
  printf '%b\n' "${C_ACCENT}c${C_RESET} ${C_INFO}info${C_RESET}  $*"
}

action() {
  printf '%b\n' "${C_ACCENT}c${C_RESET} ${C_STEP}do${C_RESET}    $*"
}

success() {
  printf '%b\n' "${C_ACCENT}c${C_RESET} ${C_OK}ok${C_RESET}    $*"
}

warn() {
  printf '%b\n' "${C_ACCENT}c${C_RESET} ${C_WARN}warn${C_RESET}  $*"
}

error() {
  printf '%b\n' "${C_ACCENT}c${C_RESET} ${C_ERR}error${C_RESET} $*"
}

show_path() {
  printf '%b' "${C_PATH}$1${C_RESET}"
}

success_band() {
  local width
  local token
  local line

  width="$(tput cols 2>/dev/null || true)"
  case "$width" in
    ''|*[!0-9]*) width=80 ;;
  esac
  if [ "$width" -lt 24 ]; then
    width=24
  fi

  token="ERFOLG  "
  line=""
  while [ "${#line}" -lt "$width" ]; do
    line="${line}${token}"
  done
  line="${line:0:$width}"

  printf '%b\n' "${C_OK}${C_BOLD}${line}${C_RESET}"
}

failure_band() {
  local width
  local token
  local line

  width="$(tput cols 2>/dev/null || true)"
  case "$width" in
    ''|*[!0-9]*) width=80 ;;
  esac
  if [ "$width" -lt 24 ]; then
    width=24
  fi

  token="FEHLSCHLAG  "
  line=""
  while [ "${#line}" -lt "$width" ]; do
    line="${line}${token}"
  done
  line="${line:0:$width}"

  printf '%b\n' "${C_ERR}${C_BOLD}${line}${C_RESET}"
}

dry_run=0
mkdir -p "$download_dir" "$done_dir" "$failed_dir"

select_latest_script() {
  python3 - "$download_dir" <<'PY'
from pathlib import Path
import sys

downloads = Path(sys.argv[1]).expanduser()
if not downloads.exists():
    raise SystemExit(0)

candidates = [
    path
    for path in downloads.iterdir()
    if path.is_file()
    and path.suffix in {".sh", ".zip"}
    and not path.name.startswith(".")
]

if not candidates:
    raise SystemExit(0)

latest = max(candidates, key=lambda path: (path.stat().st_mtime, path.name))
print(latest)
PY
}

extract_zip_patch_script() {
  local archive_path="$1"

  zip_extract_dir="$(mktemp -d "$download_dir/.repodossier-c-zip.XXXXXX")"
  python3 - "$archive_path" "$zip_extract_dir" <<'PY'
from pathlib import Path
import os
import stat
import sys
import zipfile

archive = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).resolve()

try:
    with zipfile.ZipFile(archive) as zip_file:
        members = []
        for info in zip_file.infolist():
            name = info.filename
            path = Path(name)
            if info.is_dir():
                continue
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"unsafe zip entry: {name}")
            if path.name.startswith(".") or path.parts[:1] == ("__MACOSX",):
                continue
            if path.suffix == ".sh":
                members.append(info)

        if len(members) != 1:
            raise SystemExit(f"zip archive must contain exactly one .sh patch script, found {len(members)}")

        member = members[0]
        output = target / Path(member.filename).name
        output.write_bytes(zip_file.read(member))
        mode = output.stat().st_mode
        output.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(output)
except zipfile.BadZipFile as exc:
    raise SystemExit(f"invalid zip archive: {archive}") from exc
PY
}

unique_destination() {
  local target_dir="$1"
  local source_path="$2"
  local base
  local stem
  local ext
  local candidate
  local ts

  base="$(basename "$source_path")"
  stem="${base%.*}"
  ext="${base##*.}"

  if [ "$stem" = "$base" ]; then
    ext=""
  else
    ext=".$ext"
  fi

  candidate="$target_dir/$base"
  if [ ! -e "$candidate" ]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  ts="$(date +%Y%m%d_%H%M%S)"
  candidate="$target_dir/${stem}_${ts}${ext}"
  printf '%s\n' "$candidate"
}

move_script_to() {
  local target_dir="$1"
  local source_path="$2"
  local destination

  destination="$(unique_destination "$target_dir" "$source_path")"
  mv "$source_path" "$destination"
  printf '%s\n' "$destination"
}

script_age_seconds() {
  local script_path="$1"
  local now
  local modified

  now="$(date +%s)"
  modified="$(stat -c %Y "$script_path")"
  printf '%s\n' "$((now - modified))"
}

format_age() {
  local seconds="$1"
  local minutes="$((seconds / 60))"
  local rest="$((seconds % 60))"

  if [ "$minutes" -gt 0 ]; then
    printf '%sm %ss' "$minutes" "$rest"
  else
    printf '%ss' "$seconds"
  fi
}

hash_script() {
  sha256sum "$1" | awk '{print $1}'
}

find_applied_match() {
  local script_hash="$1"
  local candidate
  local candidate_hash

  if [ -f "$applied_ledger" ]; then
    if grep -Fq "$script_hash" "$applied_ledger"; then
      grep -F "$script_hash" "$applied_ledger" | tail -n 1
      return 0
    fi
  fi

  for candidate in "$done_dir"/*.sh; do
    [ -e "$candidate" ] || continue
    candidate_hash="$(hash_script "$candidate")"
    if [ "$candidate_hash" = "$script_hash" ]; then
      printf 'done-file\t%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

record_successful_application() {
  local script_hash="$1"
  local original_script="$2"
  local moved_to="$3"

  mkdir -p "$done_dir"
  touch "$applied_ledger"
  printf '%s\t%s\t%s\t%s\n' \
    "$script_hash" \
    "$(date --iso-8601=seconds)" \
    "$(basename "$original_script")" \
    "$moved_to" >> "$applied_ledger"
}

confirm_old_script() {
  local script_path="$1"
  local age="$2"
  local formatted_age
  local answer

  formatted_age="$(format_age "$age")"

  section "Sicherheitsprüfung"
  warn "Das Patchscript ist älter als $(format_age "$max_age_seconds"): $formatted_age."
  warn "Ältere Download-Patches können veraltet sein oder nicht mehr zum aktuellen Repo-Stand passen."
  info "Script: $(show_path "$script_path")"

  printf '%b' "${C_ACCENT}c${C_RESET} ${C_WARN}confirm${C_RESET} Trotzdem ausführen? [y/N] "
  if ! read -r answer; then
    answer=""
  fi

  case "${answer,,}" in
    y|yes|j|ja)
      success "Bestätigung erhalten. c führt das ältere Script aus."
      return 0
      ;;
    *)
      error "Abgebrochen. Das ältere Script wurde nicht ausgeführt und bleibt in Downloads."
      return 1
      ;;
  esac
}

confirm_already_applied_script() {
  local script_path="$1"
  local script_hash="$2"
  local match="$3"
  local answer

  section "Wiederholungsprüfung"
  error "Dieses Patchscript wurde bereits erfolgreich angewendet."
  error "Hash: $script_hash"
  error "Fundstelle: $match"
  warn "Erneutes Ausführen kann doppelte Commits, kaputte Imports oder unnötige Fixes erzeugen."
  info "Script bleibt ohne Bestätigung in Downloads: $(show_path "$script_path")"

  printf '%b' "${C_ACCENT}c${C_RESET} ${C_ERR}confirm${C_RESET} Trotzdem erneut ausführen? [y/N] "
  if ! read -r answer; then
    answer=""
  fi

  case "${answer,,}" in
    y|yes|j|ja)
      warn "Bestätigung erhalten. c führt das bereits angewendete Script erneut aus."
      return 0
      ;;
    *)
      error "Abgebrochen. Bereits angewendetes Script wurde nicht erneut ausgeführt."
      return 1
      ;;
  esac
}

wait_seen_key_exists() {
  local script_hash="$1"
  local script_path="$2"
  local key

  key="${script_hash}	${script_path}"
  [ -f "$wait_seen" ] && grep -Fqx "$key" "$wait_seen"
}

wait_record_seen() {
  local script_hash="$1"
  local script_path="$2"

  mkdir -p "$download_dir"
  touch "$wait_seen"
  printf '%s\t%s\n' "$script_hash" "$script_path" >> "$wait_seen"
}

wait_mark_existing_scripts() {
  local script_path
  local script_hash

  touch "$wait_seen"
  for script_path in "$download_dir"/*.sh "$download_dir"/*.zip; do
    [ -e "$script_path" ] || continue
    script_hash="$(hash_script "$script_path")"
    if ! wait_seen_key_exists "$script_hash" "$script_path"; then
      wait_record_seen "$script_hash" "$script_path"
    fi
  done
}

wait_candidate() {
  local script_path
  local script_hash
  local age

  for script_path in "$download_dir"/*.sh "$download_dir"/*.zip; do
    [ -e "$script_path" ] || continue

    case "$script_path" in
      "$download_dir"/*.sh|"$download_dir"/*.zip) ;;
      *) continue ;;
    esac

    script_hash="$(hash_script "$script_path")"
    if wait_seen_key_exists "$script_hash" "$script_path"; then
      continue
    fi

    age="$(script_age_seconds "$script_path")"
    if [ "$age" -lt 0 ]; then
      wait_record_seen "$script_hash" "$script_path"
      continue
    fi

    if [ "$age" -gt "$wait_fresh_seconds" ]; then
      wait_record_seen "$script_hash" "$script_path"
      warn "Warte-Modus überspringt altes Script: $(basename "$script_path") ($(format_age "$age") alt)."
      continue
    fi

    if find_applied_match "$script_hash" >/dev/null 2>&1; then
      wait_record_seen "$script_hash" "$script_path"
      warn "Warte-Modus überspringt bereits angewendetes Script: $(basename "$script_path")."
      continue
    fi

    printf '%s\n' "$script_path"
    return 0
  done

  return 1
}

wait_loop() {
  local script_path
  local script_hash
  local status

  if [ "$(id -u)" -eq 0 ]; then
    error "c --wait darf nicht als root gestartet werden."
    return 1
  fi

  mkdir -p "$download_dir" "$done_dir" "$failed_dir"
  touch "$wait_seen"

  banner
  section "Warte-Modus"
  info "c --wait läuft im Vordergrund. Ausgabe bleibt sichtbar."
  info "Beobachte: $(show_path "$download_dir")"
  info "Starte nur neue, maximal $(format_age "$wait_fresh_seconds") alte *.sh- oder *.zip-Dateien."
  info "Stoppen mit: Ctrl+C"

  wait_mark_existing_scripts

  trap 'echo; warn "Warte-Modus beendet."; exit 0' INT TERM

  while true; do
    if script_path="$(wait_candidate)"; then
      script_hash="$(hash_script "$script_path")"
      wait_record_seen "$script_hash" "$script_path"

      section "Neues Patchscript erkannt"
      info "Script: $(show_path "$script_path")"
      action "Führe über normalen c-Runner aus."

      C_RUNNER_WAIT_CHILD=1 "$runner_source" "$script_path"
      status=$?

      if [ "$status" -eq 0 ]; then
        success "Patchlauf abgeschlossen. Warte auf das nächste Script."
      else
        warn "Patchlauf endete mit Exit-Code $status. Warte trotzdem weiter."
      fi
    else
      sleep "$wait_sleep_seconds"
    fi
  done
}

read_display_progress_context_hint() {
  local script_path="$1"
  python3 - "$script_path" <<'PY'
from pathlib import Path
import json
import sys

prefix = '# ' + 'repodossier-' + 'meta:'
script = Path(sys.argv[1])
try:
    lines = script.read_text(encoding='utf-8', errors='replace').splitlines()
except OSError:
    raise SystemExit(0)
for line in lines:
    stripped = line.strip()
    if not stripped.startswith(prefix):
        continue
    payload = stripped[len(prefix):].strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        continue
    if data.get('type') != 'display':
        continue
    if data.get('progress_context') is False:
        print('0')
        raise SystemExit(0)
    if data.get('progress_context') is True:
        print('1')
        raise SystemExit(0)
PY
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

if [ "${1:-}" = "--dry-run" ]; then
  dry_run=1
  shift
fi

case "${1:-}" in
  --wait|--loop)
    wait_loop
    exit $?
    ;;
esac

if [ "$#" -gt 0 ]; then
  patch_script="$1"
else
  patch_script="$(select_latest_script)"
fi

if [ -z "${patch_script:-}" ]; then
  error "Kein Patch-Script in $download_dir gefunden."
  exit 1
fi

if [ ! -f "$patch_script" ]; then
  error "Patch-Script nicht gefunden: $patch_script"
  exit 1
fi

case "$patch_script" in
  "$download_dir"/*.sh|"$download_dir"/*.zip|/*) ;;
  *)
    patch_script="$(pwd)/$patch_script"
    ;;
esac

source_artifact="$patch_script"
source_artifact_is_zip=0
case "$source_artifact" in
  *.zip)
    source_artifact_is_zip=1
    patch_script="$(extract_zip_patch_script "$source_artifact")"
    ;;
esac

script_base="$(basename "$source_artifact")"
script_stem="${script_base%.*}"
timestamp="$(date +%Y%m%d_%H%M%S)"
run_log="$download_dir/${script_stem}_${timestamp}.log"

exec > >(tee -a "$run_log") 2>&1

banner

section "Start"
info "Downloads: $(show_path "$download_dir")"
info "Done-Ordner: $(show_path "$done_dir")"
info "Failed-Ordner: $(show_path "$failed_dir")"
if [ "$source_artifact_is_zip" -eq 1 ]; then
  info "Patcharchive: $(show_path "$source_artifact")"
  info "Patchscript: $(show_path "$patch_script")"
else
  info "Patchscript: $(show_path "$patch_script")"
fi
info "Logfile: $(show_path "$run_log")"
info "Startzeit: $(date --iso-8601=seconds)"




section "Metadatenprüfung"
action "Validiere repodossier-meta JSON-Kommentarzeilen."
python3 - "$patch_script" "$runner_repo" <<'PY_META_C_RUNNER_14B2'
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PREFIX = "# repodossier-meta:"
ALLOWED_TYPES = {"patch", "progress", "display"}
ALLOWED_PATCH_FIELDS = {"type", "id", "title", "commit", "fix_for", "requires_direct_bash"}
ALLOWED_PROGRESS_FIELDS = {"type", "panel", "status", "file", "start", "end", "anchor", "label"}
ALLOWED_DISPLAY_FIELDS = {"type", "context", "layout", "frame", "progress_context"}
ALLOWED_PANELS = {"roadmap", "milestone"}
ALLOWED_STATUSES = {"done", "active", "partial", "todo"}
ALLOWED_LAYOUTS = {"side-by-side", "stacked"}


def fmt(line_number: int | None, message: str) -> str:
    return message if line_number is None else f"line {line_number}: {message}"


def require_string(line_number: int, data: dict[str, Any], errors: list[str], key: str) -> None:
    value = data.get(key)
    if not isinstance(value, str):
        errors.append(fmt(line_number, f'missing or invalid string field "{key}"'))
    elif not value.strip():
        errors.append(fmt(line_number, f'field "{key}" must not be empty'))


def require_bool(line_number: int, data: dict[str, Any], errors: list[str], key: str) -> None:
    if key in data and not isinstance(data[key], bool):
        errors.append(fmt(line_number, f'field "{key}" must be a boolean'))


def require_int(line_number: int, data: dict[str, Any], errors: list[str], key: str, *, minimum: int = 1) -> None:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(fmt(line_number, f'missing or invalid integer field "{key}"'))
    elif value < minimum:
        errors.append(fmt(line_number, f'field "{key}" must be >= {minimum}'))


def parse_records(script_path: Path) -> tuple[list[tuple[int, dict[str, Any]]], list[str]]:
    records: list[tuple[int, dict[str, Any]]] = []
    errors: list[str] = []
    try:
        lines = script_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        return [], [f"cannot read script as UTF-8: {exc}"]
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith(PREFIX):
            continue
        payload = stripped[len(PREFIX):].strip()
        if not payload:
            errors.append(fmt(line_number, "empty repodossier-meta payload"))
            continue
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            errors.append(fmt(line_number, f"invalid JSON: {exc.msg}"))
            continue
        if not isinstance(decoded, dict):
            errors.append(fmt(line_number, "metadata payload must be a JSON object"))
            continue
        records.append((line_number, decoded))
    return records, errors


def validate_records(records: list[tuple[int, dict[str, Any]]], repo_root: Path) -> list[str]:
    errors: list[str] = []
    if not records:
        return ["missing required repodossier-meta block"]

    patch_records = [(line, data) for line, data in records if data.get("type") == "patch"]
    progress_records = [(line, data) for line, data in records if data.get("type") == "progress"]
    display_records = [(line, data) for line, data in records if data.get("type") == "display"]

    if len(patch_records) != 1:
        errors.append(f"expected exactly one patch metadata record, found {len(patch_records)}")
    if len(display_records) > 1:
        errors.append(f"expected at most one display metadata record, found {len(display_records)}")

    requires_direct_bash = any(data.get("requires_direct_bash") is True for _line, data in patch_records)
    display_progress_context_disabled = any(data.get("progress_context") is False for _line, data in display_records)
    if display_progress_context_disabled and progress_records:
        errors.append("display progress_context=false must not be combined with progress metadata records")
    if patch_records and not requires_direct_bash and not display_progress_context_disabled:
        panels = {data.get("panel") for _line, data in progress_records if isinstance(data.get("panel"), str)}
        if "roadmap" not in panels:
            errors.append("missing required roadmap progress metadata record")
        if "milestone" not in panels:
            errors.append("missing required milestone progress metadata record")

    for line_number, data in records:
        meta_type = data.get("type")
        if not isinstance(meta_type, str):
            errors.append(fmt(line_number, 'missing or invalid string field "type"'))
            continue
        if meta_type not in ALLOWED_TYPES:
            errors.append(fmt(line_number, f"type must be one of {sorted(ALLOWED_TYPES)}, got {meta_type!r}"))
            continue
        if meta_type == "patch":
            for key in sorted(set(data) - ALLOWED_PATCH_FIELDS):
                errors.append(fmt(line_number, f'unknown field "{key}"'))
            for key in ("id", "title", "commit"):
                require_string(line_number, data, errors, key)
            if "fix_for" in data:
                require_string(line_number, data, errors, "fix_for")
            require_bool(line_number, data, errors, "requires_direct_bash")
        elif meta_type == "progress":
            for key in sorted(set(data) - ALLOWED_PROGRESS_FIELDS):
                errors.append(fmt(line_number, f'unknown field "{key}"'))
            for key in ("panel", "status", "file"):
                require_string(line_number, data, errors, key)
            has_start = "start" in data
            has_end = "end" in data
            has_anchor = "anchor" in data
            if has_start != has_end:
                errors.append(fmt(line_number, '"start" and "end" must be provided together'))
            if not has_anchor and not (has_start and has_end):
                errors.append(fmt(line_number, 'progress metadata must provide either "start"/"end" or "anchor"'))
            if has_start:
                require_int(line_number, data, errors, "start")
            if has_end:
                require_int(line_number, data, errors, "end")
            if has_anchor:
                require_string(line_number, data, errors, "anchor")
            panel = data.get("panel")
            status = data.get("status")
            rel_file = data.get("file")
            if isinstance(panel, str) and panel not in ALLOWED_PANELS:
                errors.append(fmt(line_number, f"panel must be one of {sorted(ALLOWED_PANELS)}"))
            if isinstance(status, str) and status not in ALLOWED_STATUSES:
                errors.append(fmt(line_number, f"status must be one of {sorted(ALLOWED_STATUSES)}"))
            if isinstance(rel_file, str):
                rel_path = Path(rel_file)
                if rel_path.is_absolute() or "." in rel_path.parts:
                    errors.append(fmt(line_number, "file must be a safe repo-relative path"))
                else:
                    full_path = repo_root / rel_file
                    if not full_path.exists():
                        errors.append(fmt(line_number, f"file does not exist: {rel_file}"))
                    elif full_path.is_dir():
                        errors.append(fmt(line_number, f"file is a directory: {rel_file}"))
        elif meta_type == "display":
            for key in sorted(set(data) - ALLOWED_DISPLAY_FIELDS):
                errors.append(fmt(line_number, f'unknown field "{key}"'))
            if "context" in data:
                require_int(line_number, data, errors, "context", minimum=0)
                context = data.get("context")
                if isinstance(context, int) and context > 50:
                    errors.append(fmt(line_number, 'field "context" must be <= 50'))
            if "layout" in data:
                require_string(line_number, data, errors, "layout")
                layout = data.get("layout")
                if isinstance(layout, str) and layout not in ALLOWED_LAYOUTS:
                    errors.append(fmt(line_number, f"layout must be one of {sorted(ALLOWED_LAYOUTS)}"))
            if "frame" in data and not isinstance(data["frame"], bool):
                errors.append(fmt(line_number, 'field "frame" must be a boolean'))
            if "progress_context" in data and not isinstance(data["progress_context"], bool):
                errors.append(fmt(line_number, 'field "progress_context" must be a boolean'))
    return errors


script_path = Path(sys.argv[1]).expanduser().resolve()
repo_root = Path(sys.argv[2]).expanduser().resolve()
records, parse_errors = parse_records(script_path)
errors = parse_errors + validate_records(records, repo_root)
if errors:
    print("Metadata invalid:")
    for item in errors:
        print(f"  - {item}")
    raise SystemExit(10)
print("Metadata OK")
PY_META_C_RUNNER_14B2
metadata_status=$?
if [ "$metadata_status" -ne 0 ]; then
  error "Metadatenprüfung fehlgeschlagen. Patch wird nicht ausgeführt."
  info "Logfile bleibt erhalten: $(show_path "$run_log")"
  exit "$metadata_status"
fi
success "Metadaten OK."



display_progress_context_hint="$(read_display_progress_context_hint "$patch_script" || true)"
if [ "$progress_context_explicit" -eq 0 ]; then
  case "$display_progress_context_hint" in
    0)
      show_progress_context=0
      info "Dieses Patchscript wünscht keinen Progress Context."
      ;;
    1)
      show_progress_context=1
      ;;
  esac
fi


progress_context_output=""
if [ -x "$progress_renderer" ]; then
  progress_context_output="$(mktemp "${TMPDIR:-/tmp}/repodossier-progress-context.XXXXXX.txt")"
  python3 "$progress_renderer" --script "$patch_script" --repo "$runner_repo" > "$progress_context_output"
  progress_status=$?
  if [ "$progress_status" -ne 0 ]; then
    cat "$progress_context_output" || true
    rm -f "$progress_context_output"
    error "Progress-Kontext konnte nicht vorbereitet werden."
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    exit "$progress_status"
  fi
fi

script_hash="$(hash_script "$source_artifact")"
applied_match=""
if applied_match="$(find_applied_match "$script_hash")"; then
  if [ "${C_RUNNER_WAIT_CHILD:-0}" = "1" ]; then
    section "Wiederholungsprüfung"
    error "Dieses Patchscript wurde bereits erfolgreich angewendet."
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    rm -f "${progress_context_output:-}" 2>/dev/null || true
    exit 3
  fi

  if ! confirm_already_applied_script "$source_artifact" "$script_hash" "$applied_match"; then
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    rm -f "${progress_context_output:-}" 2>/dev/null || true
    exit 3
  fi
else
  section "Wiederholungsprüfung"
  success "Dieses Patchscript wurde noch nicht als erfolgreich angewendet erkannt."
fi

age_seconds="$(script_age_seconds "$source_artifact")"
if [ "$age_seconds" -gt "$max_age_seconds" ]; then
  if [ "${C_RUNNER_WAIT_CHILD:-0}" = "1" ]; then
    section "Sicherheitsprüfung"
    error "Warte-Kindprozess verweigert altes Patchscript: $(format_age "$age_seconds") alt."
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    rm -f "${progress_context_output:-}" 2>/dev/null || true
    exit 2
  fi

  if ! confirm_old_script "$source_artifact" "$age_seconds"; then
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    rm -f "${progress_context_output:-}" 2>/dev/null || true
    exit 2
  fi
else
  section "Sicherheitsprüfung"
  success "Patchscript ist frisch genug: $(format_age "$age_seconds") alt."
fi

section "Syntaxprüfung"
action "Prüfe Bash-Syntax mit: bash -n $(show_path "$patch_script")"
bash -n "$patch_script"
syntax_status=$?

if [ "$syntax_status" -ne 0 ]; then
  error "Syntaxprüfung fehlgeschlagen. Exit-Code: $syntax_status"
  if [ "$dry_run" -eq 1 ]; then
    info "Dry-run: Script bleibt unverändert in Downloads: $(show_path "$patch_script")"
    info "Logfile bleibt in Downloads: $(show_path "$run_log")"
    rm -f "${progress_context_output:-}" 2>/dev/null || true
    exit "$syntax_status"
  fi

  moved_to="$(move_script_to "$failed_dir" "$source_artifact")"
  info "Script verschoben nach: $(show_path "$moved_to")"
  info "Logfile bleibt in Downloads: $(show_path "$run_log")"
  rm -f "${progress_context_output:-}" 2>/dev/null || true
  exit "$syntax_status"
fi

success "Syntax OK."

if [ "$dry_run" -eq 1 ]; then
  section "Dry-run Abschluss"
  success "Dry-run erfolgreich. Patchscript wurde nicht ausgeführt."
  info "Script bleibt unverändert in Downloads: $(show_path "$patch_script")"
  info "Logfile bleibt in Downloads: $(show_path "$run_log")"
  info "Endzeit: $(date --iso-8601=seconds)"

  if [ -n "${progress_context_output:-}" ] && [ -s "$progress_context_output" ]; then
    section "Roadmap / Milestone"
    cat "$progress_context_output"
  fi
  rm -f "${progress_context_output:-}" 2>/dev/null || true

  printf '%b\n' "${C_OK}${C_BOLD}DRY-RUN OK${C_RESET}"
  exit 0
fi

section "Ausführung"
action "Starte Patchscript mit bash."
env -u C_RUNNER_WAIT_CHILD -u C_RUNNER_WATCH_CHILD -u C_RUNNER_SELF_COPY -u C_RUNNER_ORIGINAL -u C_RUNNER_TEMP_COPY bash "$patch_script"
status=$?

section "Abschluss"
info "Patchscript Exit-Code: $status"

if [ "$status" -eq 0 ]; then
  moved_to="$(move_script_to "$done_dir" "$source_artifact")"
  record_successful_application "$script_hash" "$source_artifact" "$moved_to"
  success "Patch erfolgreich."
  info "Script verschoben nach: $(show_path "$moved_to")"
  info "Applied-Ledger aktualisiert: $(show_path "$applied_ledger")"
else
  moved_to="$(move_script_to "$failed_dir" "$source_artifact")"
  error "Patch fehlgeschlagen."
  info "Script verschoben nach: $(show_path "$moved_to")"
fi

info "Logfile bleibt in Downloads: $(show_path "$run_log")"
info "Endzeit: $(date --iso-8601=seconds)"

if [ "$show_progress_context" -eq 1 ] && [ -n "${progress_context_output:-}" ] && [ -s "$progress_context_output" ]; then
  section "Roadmap / Milestone"
  cat "$progress_context_output"
fi
rm -f "${progress_context_output:-}" 2>/dev/null || true

if [ "$status" -eq 0 ]; then
  success_band
else
  failure_band
fi

exit "$status"
