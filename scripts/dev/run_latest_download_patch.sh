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
  c --help

Patch scripts must include one patch metadata record, for example:
  # repodossier-meta: {"type":"patch","id":"DEV.6","title":"Add progress renderer","commit":"Add patch metadata progress renderer"}

Optional progress records render Roadmap/Milestone context before execution:
  # repodossier-meta: {"type":"progress","panel":"roadmap","status":"active","file":"planning/ROADMAP.md","start":10,"end":20}
  # repodossier-meta: {"type":"progress","panel":"milestone","status":"partial","file":"planning/MILESTONE4.md","start":30,"end":40}
  # repodossier-meta: {"type":"display","context":4,"layout":"side-by-side","frame":false}

Status colors:
  done=green, active=purple, partial=yellow, todo=red.

On success, c prints a final bold green ERFOLG line as the last output line.
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

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

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

if [ -x "$progress_renderer" ]; then
  section "Roadmap / Milestone"
  python3 "$progress_renderer" --script "$patch_script" --repo "$runner_repo"
  progress_status=$?
  if [ "$progress_status" -ne 0 ]; then
    error "Progress-Kontext konnte nicht gerendert werden."
    info "Logfile bleibt erhalten: $(show_path "$run_log")"
    exit "$progress_status"
  fi
fi

script_hash="$(hash_script "$patch_script")"
applied_match=""
if applied_match="$(find_applied_match "$script_hash")"; then
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

if [ "$status" -eq 0 ]; then
  printf '%b\n' "${C_OK}${C_BOLD}ERFOLG${C_RESET}"
fi

exit "$status"
