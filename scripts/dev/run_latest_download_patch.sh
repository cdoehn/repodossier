#!/usr/bin/env bash
set -u

if [ "${C_RUNNER_SELF_COPY:-0}" != "1" ]; then
  self_copy="$(mktemp "${TMPDIR:-/tmp}/repodossier-c-runner.XXXXXX.sh")"
  cp "$0" "$self_copy"
  chmod +x "$self_copy"
  C_RUNNER_SELF_COPY=1 C_RUNNER_TEMP_COPY="$self_copy" exec "$self_copy" "$@"
fi

if [ -n "${C_RUNNER_TEMP_COPY:-}" ]; then
  trap 'rm -f "$C_RUNNER_TEMP_COPY"' EXIT
fi

download_dir="${PATCH_DOWNLOAD_DIR:-$HOME/Downloads}"
done_dir="$download_dir/done"
failed_dir="$download_dir/failed"
applied_ledger="$done_dir/.applied_patch_hashes.tsv"
max_age_seconds="${C_RUNNER_MAX_AGE_SECONDS:-3600}"

runner_source="${BASH_SOURCE[0]}"
if [ -n "${C_RUNNER_TEMP_COPY:-}" ] && [ -x "$HOME/market_research/repo_dossier/scripts/dev/run_latest_download_patch.sh" ]; then
  runner_source="$HOME/market_research/repo_dossier/scripts/dev/run_latest_download_patch.sh"
fi
runner_dir="$(cd "$(dirname "$runner_source")" && pwd)"
runner_repo="$(cd "$runner_dir/../.." && pwd)"
metadata_validator="$runner_dir/validate_patch_metadata.py"
progress_renderer="$runner_dir/show_progress_context.py"

watch_pidfile="$download_dir/.repodossier-c-watch.pid"
watch_lockdir="$download_dir/.repodossier-c-watch.lock"
watch_seen="$download_dir/.repodossier-c-watch.seen"
watch_log="$download_dir/c-watch.log"
watch_sleep_seconds="${C_RUNNER_WATCH_SLEEP_SECONDS:-2}"
watch_fresh_seconds="${C_RUNNER_WATCH_FRESH_SECONDS:-30}"

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
  c --watch-up
  c --watch-down
  c --watch-status
  c --help

Normal mode:
  c validates metadata, checks freshness and repetition, runs one patch script,
  moves it to done/failed, logs output, prints progress context near the end,
  and prints a full-width green ERFOLG banner as the final line on success.

Watch mode:
  c --watch-up starts a background watcher for ~/Downloads/*.sh.
  c --watch-down stops it.
  c --watch-status shows whether it is running.

Automatic watch execution is intentionally strict:
  - no root execution
  - only scripts directly in Downloads
  - only scripts modified within the last 30 seconds
  - valid repodossier-meta with roadmap and milestone progress
  - bash -n must pass
  - SHA-256 hash must not already be applied
  - each seen script/hash is started only once
  - lockfile prevents duplicate watcher instances
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

mkdir -p "$download_dir" "$done_dir" "$failed_dir"

is_pid_running() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1
}

watch_current_pid() {
  if [ -f "$watch_pidfile" ]; then
    cat "$watch_pidfile" 2>/dev/null || true
  fi
}

watch_status() {
  local pid
  pid="$(watch_current_pid)"
  if is_pid_running "$pid"; then
    success "c watch läuft. PID: $pid"
    info "Downloads: $(show_path "$download_dir")"
    info "Logfile: $(show_path "$watch_log")"
    return 0
  fi

  warn "c watch läuft nicht."
  return 1
}

watch_up() {
  local pid

  if [ "$(id -u)" -eq 0 ]; then
    error "c watch darf nicht als root gestartet werden."
    return 1
  fi

  mkdir -p "$download_dir" "$done_dir" "$failed_dir"
  pid="$(watch_current_pid)"
  if is_pid_running "$pid"; then
    success "c watch läuft bereits. PID: $pid"
    return 0
  fi

  rm -f "$watch_pidfile"
  rm -rf "$watch_lockdir"

  action "Starte c watch im Hintergrund."
  nohup "$runner_source" --watch-loop >> "$watch_log" 2>&1 &
  pid="$!"
  sleep 0.2

  if is_pid_running "$pid"; then
    success "c watch gestartet. PID: $pid"
    info "Logfile: $(show_path "$watch_log")"
    info "Stoppen mit: c --watch-down"
    return 0
  fi

  error "c watch konnte nicht gestartet werden."
  info "Logfile: $(show_path "$watch_log")"
  return 1
}

watch_down() {
  local pid
  local waited

  pid="$(watch_current_pid)"
  if ! is_pid_running "$pid"; then
    warn "c watch läuft nicht."
    rm -f "$watch_pidfile"
    rm -rf "$watch_lockdir"
    return 0
  fi

  action "Stoppe c watch. PID: $pid"
  kill "$pid" >/dev/null 2>&1 || true

  waited=0
  while is_pid_running "$pid" && [ "$waited" -lt 30 ]; do
    sleep 0.1
    waited=$((waited + 1))
  done

  if is_pid_running "$pid"; then
    warn "c watch reagiert nicht auf SIGTERM; sende SIGKILL."
    kill -9 "$pid" >/dev/null 2>&1 || true
  fi

  rm -f "$watch_pidfile"
  rm -rf "$watch_lockdir"
  success "c watch gestoppt."
}

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
    and path.suffix == ".sh"
    and not path.name.startswith(".")
]

if not candidates:
    raise SystemExit(0)

latest = max(candidates, key=lambda path: (path.stat().st_mtime, path.name))
print(latest)
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

watch_seen_key_exists() {
  local script_hash="$1"
  local script_path="$2"
  local key

  key="${script_hash}	${script_path}"
  [ -f "$watch_seen" ] && grep -Fqx "$key" "$watch_seen"
}

watch_record_seen() {
  local script_hash="$1"
  local script_path="$2"

  mkdir -p "$download_dir"
  touch "$watch_seen"
  printf '%s\t%s\n' "$script_hash" "$script_path" >> "$watch_seen"
}

watch_validate_candidate() {
  local script_path="$1"
  local age
  local script_hash

  [ -f "$script_path" ] || return 1

  case "$script_path" in
    "$download_dir"/*.sh) ;;
    *) return 1 ;;
  esac

  if [ "$(id -u)" -eq 0 ]; then
    echo "watch skip: root execution is forbidden"
    return 1
  fi

  age="$(script_age_seconds "$script_path")"
  if [ "$age" -lt 0 ] || [ "$age" -gt "$watch_fresh_seconds" ]; then
    return 1
  fi

  script_hash="$(hash_script "$script_path")"

  if watch_seen_key_exists "$script_hash" "$script_path"; then
    return 1
  fi

  if find_applied_match "$script_hash" >/dev/null 2>&1; then
    watch_record_seen "$script_hash" "$script_path"
    echo "watch skip: already applied $(basename "$script_path")"
    return 1
  fi

  if ! bash -n "$script_path"; then
    echo "watch skip: bash syntax failed $(basename "$script_path")"
    return 1
  fi

  if [ ! -x "$metadata_validator" ]; then
    echo "watch skip: metadata validator missing"
    return 1
  fi

  if ! python3 "$metadata_validator" --script "$script_path" --repo "$runner_repo" --quiet; then
    echo "watch skip: metadata invalid $(basename "$script_path")"
    return 1
  fi

  return 0
}

watch_loop() {
  local script_path
  local script_hash
  local status

  mkdir -p "$download_dir" "$done_dir" "$failed_dir"

  if [ "$(id -u)" -eq 0 ]; then
    echo "$(date --iso-8601=seconds) c-watch refused to run as root"
    exit 1
  fi

  if ! mkdir "$watch_lockdir" 2>/dev/null; then
    echo "$(date --iso-8601=seconds) c-watch lock exists: $watch_lockdir"
    exit 1
  fi

  echo "$$" > "$watch_pidfile"
  trap 'rm -f "$watch_pidfile"; rm -rf "$watch_lockdir"; exit 0' TERM INT EXIT

  echo "$(date --iso-8601=seconds) c-watch started"
  echo "$(date --iso-8601=seconds) downloads=$download_dir fresh_seconds=$watch_fresh_seconds sleep=$watch_sleep_seconds"

  while true; do
    for script_path in "$download_dir"/*.sh; do
      [ -e "$script_path" ] || continue

      if watch_validate_candidate "$script_path"; then
        script_hash="$(hash_script "$script_path")"
        watch_record_seen "$script_hash" "$script_path"
        echo "$(date --iso-8601=seconds) c-watch auto-run $(basename "$script_path")"

        C_RUNNER_WATCH_CHILD=1 "$runner_source" "$script_path"
        status=$?
        echo "$(date --iso-8601=seconds) c-watch finished $(basename "$script_path") status=$status"
      fi
    done

    sleep "$watch_sleep_seconds"
  done
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

case "${1:-}" in
  --watch-up|--daemon-up)
    banner
    watch_up
    exit $?
    ;;
  --watch-down|--daemon-down)
    banner
    watch_down
    exit $?
    ;;
  --watch-status|--daemon-status)
    banner
    watch_status
    exit $?
    ;;
  --watch-loop)
    watch_loop
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
  "$download_dir"/*.sh|/*) ;;
  *)
    patch_script="$(pwd)/$patch_script"
    ;;
esac

script_base="$(basename "$patch_script")"
script_stem="${script_base%.sh}"
timestamp="$(date +%Y%m%d_%H%M%S)"
run_log="$download_dir/${script_stem}_${timestamp}.log"

exec > >(tee -a "$run_log") 2>&1

banner

section "Start"
info "Downloads: $(show_path "$download_dir")"
info "Done-Ordner: $(show_path "$done_dir")"
info "Failed-Ordner: $(show_path "$failed_dir")"
info "Patchscript: $(show_path "$patch_script")"
info "Logfile: $(show_path "$run_log")"
info "Startzeit: $(date --iso-8601=seconds)"

section "Metadatenprüfung"
if [ ! -x "$metadata_validator" ]; then
  error "Metadata-Validator fehlt oder ist nicht ausführbar: $metadata_validator"
  info "Logfile bleibt erhalten: $(show_path "$run_log")"
  exit 10
fi

action "Validiere repodossier-meta JSON-Kommentarzeilen."
python3 "$metadata_validator" --script "$patch_script" --repo "$runner_repo"
metadata_status=$?
if [ "$metadata_status" -ne 0 ]; then
  error "Metadatenprüfung fehlgeschlagen. Patch wird nicht ausgeführt."
  info "Logfile bleibt erhalten: $(show_path "$run_log")"
  exit "$metadata_status"
fi
success "Metadaten OK."

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

script_hash="$(hash_script "$patch_script")"
applied_match=""
if applied_match="$(find_applied_match "$script_hash")"; then
  if [ "${C_RUNNER_WATCH_CHILD:-0}" = "1" ]; then
    section "Wiederholungsprüfung"
    error "Dieses Patchscript wurde bereits erfolgreich angewendet."
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    exit 3
  fi

  if ! confirm_already_applied_script "$patch_script" "$script_hash" "$applied_match"; then
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    exit 3
  fi
else
  section "Wiederholungsprüfung"
  success "Dieses Patchscript wurde noch nicht als erfolgreich angewendet erkannt."
fi

age_seconds="$(script_age_seconds "$patch_script")"
if [ "$age_seconds" -gt "$max_age_seconds" ]; then
  if [ "${C_RUNNER_WATCH_CHILD:-0}" = "1" ]; then
    section "Sicherheitsprüfung"
    error "Watch-Kindprozess verweigert altes Patchscript: $(format_age "$age_seconds") alt."
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    exit 2
  fi

  if ! confirm_old_script "$patch_script" "$age_seconds"; then
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
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
  moved_to="$(move_script_to "$failed_dir" "$patch_script")"
  info "Script verschoben nach: $(show_path "$moved_to")"
  info "Logfile bleibt in Downloads: $(show_path "$run_log")"
  rm -f "${progress_context_output:-}" 2>/dev/null || true
  exit "$syntax_status"
fi

success "Syntax OK."

section "Ausführung"
action "Starte Patchscript mit bash."
bash "$patch_script"
status=$?

section "Abschluss"
info "Patchscript Exit-Code: $status"

if [ "$status" -eq 0 ]; then
  moved_to="$(move_script_to "$done_dir" "$patch_script")"
  record_successful_application "$script_hash" "$patch_script" "$moved_to"
  success "Patch erfolgreich."
  info "Script verschoben nach: $(show_path "$moved_to")"
  info "Applied-Ledger aktualisiert: $(show_path "$applied_ledger")"
else
  moved_to="$(move_script_to "$failed_dir" "$patch_script")"
  error "Patch fehlgeschlagen."
  info "Script verschoben nach: $(show_path "$moved_to")"
fi

info "Logfile bleibt in Downloads: $(show_path "$run_log")"
info "Endzeit: $(date --iso-8601=seconds)"

if [ "$status" -eq 0 ] && [ -n "${progress_context_output:-}" ] && [ -s "$progress_context_output" ]; then
  section "Roadmap / Milestone"
  cat "$progress_context_output"
fi
rm -f "${progress_context_output:-}" 2>/dev/null || true

if [ "$status" -eq 0 ]; then
  success_band
fi

exit "$status"
