#!/usr/bin/env bash
set -u

download_dir="${PATCH_DOWNLOAD_DIR:-$HOME/Downloads}"
repodossier_bin="${REPODOSSIER_BIN:-repodossier}"

runner_source="${BASH_SOURCE[0]}"
runner_dir="$(cd "$(dirname "$runner_source")" && pwd)"
patch_rules_source="$runner_dir/patch-rules.md"

R_USE_COLOR=1
if [ -n "${NO_COLOR:-}" ] || [ "${R_RUNNER_COLOR:-auto}" = "never" ]; then
  R_USE_COLOR=0
fi

if [ "$R_USE_COLOR" -eq 1 ]; then
  R_RESET=$'\033[0m'
  R_BOLD=$'\033[1m'
  R_ACCENT=$'\033[38;5;82m'
  R_INFO=$'\033[38;5;120m'
  R_OK=$'\033[0;32m'
  R_WARN=$'\033[1;33m'
  R_ERR=$'\033[0;31m'
  R_PATH=$'\033[0;36m'
  R_STEP=$'\033[0;35m'
else
  R_RESET=''
  R_BOLD=''
  R_ACCENT=''
  R_INFO=''
  R_OK=''
  R_WARN=''
  R_ERR=''
  R_PATH=''
  R_STEP=''
fi

usage() {
  cat <<'USAGE'
Usage:
  r
  r --help

Runs RepoDossier in the current git repository:
  1. detects the current git repository root,
  2. runs: repodossier full
  3. runs: repodossier export-ai
  4. copies full.txt to ~/Downloads/full.txt, overwriting existing files,
  5. copies ai.txt to ~/Downloads/ai.txt, overwriting existing files,
  6. copies scripts/dev/patch-rules.md to ~/Downloads/patch-rules.md when available.
USAGE
}

banner() {
  printf '\n'
  printf '%b\n' "${R_ACCENT}${R_BOLD}r · RepoDossier Export Runner${R_RESET}"
  printf '%b\n' "${R_ACCENT}─────────────────────────────${R_RESET}"
}

section() {
  printf '\n%b\n' "${R_ACCENT}${R_BOLD}▶ r:${R_RESET} ${R_STEP}${R_BOLD}$1${R_RESET}"
}

info() {
  printf '%b\n' "${R_ACCENT}r${R_RESET} ${R_INFO}info${R_RESET}  $*"
}

action() {
  printf '%b\n' "${R_ACCENT}r${R_RESET} ${R_STEP}do${R_RESET}    $*"
}

success() {
  printf '%b\n' "${R_ACCENT}r${R_RESET} ${R_OK}ok${R_RESET}    $*"
}

warn() {
  printf '%b\n' "${R_ACCENT}r${R_RESET} ${R_WARN}warn${R_RESET}  $*"
}

error() {
  printf '%b\n' "${R_ACCENT}r${R_RESET} ${R_ERR}error${R_RESET} $*"
}

show_path() {
  printf '%b' "${R_PATH}$1${R_RESET}"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

banner

section "Repo-Erkennung"
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  error "Aktuelles Verzeichnis liegt nicht in einem Git-Repository."
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root" || exit 1

info "Aktuelles Repo: $(show_path "$repo_root")"
info "Downloads: $(show_path "$download_dir")"
info "RepoDossier-Binary: $repodossier_bin"
info "Patch-Rules-Quelle: $(show_path "$patch_rules_source")"

mkdir -p "$download_dir"

if ! command -v "$repodossier_bin" >/dev/null 2>&1; then
  error "RepoDossier-Befehl nicht gefunden: $repodossier_bin"
  error "Installiere repodossier oder setze REPODOSSIER_BIN."
  exit 1
fi

section "Export full.txt"
action "Führe aus: $repodossier_bin full"
"$repodossier_bin" full
full_status=$?
if [ "$full_status" -ne 0 ]; then
  error "repodossier full fehlgeschlagen. Exit-Code: $full_status"
  exit "$full_status"
fi

if [ ! -f "$repo_root/full.txt" ]; then
  error "full.txt wurde nicht erzeugt: $repo_root/full.txt"
  exit 1
fi
success "full.txt erzeugt."

section "Export ai.txt"
action "Führe aus: $repodossier_bin export-ai"
"$repodossier_bin" export-ai
ai_status=$?
if [ "$ai_status" -ne 0 ]; then
  error "repodossier export-ai fehlgeschlagen. Exit-Code: $ai_status"
  exit "$ai_status"
fi

if [ ! -f "$repo_root/ai.txt" ]; then
  error "ai.txt wurde nicht erzeugt: $repo_root/ai.txt"
  exit 1
fi
success "ai.txt erzeugt."

section "Kopieren nach Downloads"
cp -f "$repo_root/full.txt" "$download_dir/full.txt"
cp -f "$repo_root/ai.txt" "$download_dir/ai.txt"

success "Kopiert: $(show_path "$download_dir/full.txt")"
success "Kopiert: $(show_path "$download_dir/ai.txt")"

if [ -f "$patch_rules_source" ]; then
  cp -f "$patch_rules_source" "$download_dir/patch-rules.md"
  success "Kopiert: $(show_path "$download_dir/patch-rules.md")"
else
  warn "Patch-Rules nicht gefunden, daher nicht kopiert: $(show_path "$patch_rules_source")"
fi

info "Vorhandene Dateien in Downloads wurden überschrieben."

section "Abschluss"
success "RepoDossier-Exports für aktuelles Repo fertig."

exit 0
