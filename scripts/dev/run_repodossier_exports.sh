#!/usr/bin/env bash
set -u

repo_candidate="$HOME/market_research/repo_dossier"

C_USE_COLOR=1
if [ -n "${NO_COLOR:-}" ]; then
  C_USE_COLOR=0
fi

if [ "$C_USE_COLOR" -eq 1 ]; then
  C_RESET=$'\033[0m'
  C_OK=$'\033[0;32m'
  C_INFO=$'\033[38;5;39m'
  C_WARN=$'\033[1;33m'
  C_ERR=$'\033[0;31m'
  C_ACCENT=$'\033[38;5;45m'
  C_BOLD=$'\033[1m'
else
  C_RESET=''
  C_OK=''
  C_INFO=''
  C_WARN=''
  C_ERR=''
  C_ACCENT=''
  C_BOLD=''
fi

usage() {
  cat <<'USAGE'
Usage:
  r [mode ...]
  r --dry-run [mode ...]
  r --list-modes
  r --help

Modes:
  all       run full, ai, docs and changed exports
  full      run repodossier full
  ai        run repodossier export-ai
  docs      run repodossier export-docs
  changed   run repodossier changed

Compatibility aliases:
  quick     same as ai
  doc       same as docs
  changes   same as changed

Without an explicit mode, r defaults to all.
USAGE
}

section() {
  printf '\n%b▶ r:%b %b%s%b\n' "$C_ACCENT$C_BOLD" "$C_RESET" "$C_BOLD" "$1" "$C_RESET"
}

info() {
  printf '%br%b %binfo%b  %s\n' "$C_ACCENT" "$C_RESET" "$C_INFO" "$C_RESET" "$1"
}

success() {
  printf '%br%b %bok%b    %s\n' "$C_ACCENT" "$C_RESET" "$C_OK" "$C_RESET" "$1"
}

error() {
  printf '%br%b %berror%b %s\n' "$C_ACCENT" "$C_RESET" "$C_ERR" "$C_RESET" "$1"
}

find_repo_root() {
  local root=""

  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    root="$(git rev-parse --show-toplevel)"
  else
    cd "$repo_candidate" || {
      error "RepoDossier-Verzeichnis nicht gefunden: $repo_candidate"
      return 1
    }
    root="$(git rev-parse --show-toplevel)" || return 1
  fi

  case "$root" in
    */repo_dossier) ;;
    *)
      error "Falsches Repository: $root"
      return 1
      ;;
  esac

  cd "$root" || return 1
  info "Repo root: $root"
}

normalize_mode() {
  case "$1" in
    all) echo "all" ;;
    full) echo "full" ;;
    ai|quick) echo "ai" ;;
    docs|doc) echo "docs" ;;
    changed|changes) echo "changed" ;;
    *)
      return 1
      ;;
  esac
}

command_for_mode() {
  case "$1" in
    full) echo "repodossier full" ;;
    ai) echo "repodossier export-ai" ;;
    docs) echo "repodossier export-docs" ;;
    changed) echo "repodossier changed" ;;
    *)
      return 1
      ;;
  esac
}

expand_modes() {
  local mode
  local normalized

  if [ "$#" -eq 0 ]; then
    set -- all
  fi

  for mode in "$@"; do
    normalized="$(normalize_mode "$mode")" || {
      error "Unbekannter r-Modus: $mode"
      echo "Erlaubt: all, full, ai, docs, changed"
      return 2
    }

    if [ "$normalized" = "all" ]; then
      printf '%s\n' full ai docs changed
    else
      printf '%s\n' "$normalized"
    fi
  done | awk '!seen[$0]++'
}

run_mode() {
  local mode="$1"
  local command
  command="$(command_for_mode "$mode")" || return 2

  section "$mode"
  info "Befehl: $command"

  if [ "$dry_run" -eq 1 ]; then
    success "Dry-run: nicht ausgeführt."
    return 0
  fi

  if ! command -v repodossier >/dev/null 2>&1; then
    error "repodossier ist nicht im PATH. Aktiviere .venv oder installiere das Paket."
    return 127
  fi

  $command
}

dry_run=0

case "${1:-}" in
  --help|-h)
    usage
    exit 0
    ;;
  --list-modes)
    printf '%s\n' all full ai docs changed quick doc changes
    exit 0
    ;;
  --dry-run)
    dry_run=1
    shift
    ;;
esac

find_repo_root || exit 1

mapfile -t modes < <(expand_modes "$@")
expand_status=$?
if [ "$expand_status" -ne 0 ]; then
  exit "$expand_status"
fi

section "Start"
if [ "$dry_run" -eq 1 ]; then
  info "Dry-run aktiv."
fi
info "Modi: ${modes[*]}"

status=0
for mode in "${modes[@]}"; do
  run_mode "$mode" || status=$?
  if [ "$status" -ne 0 ]; then
    break
  fi
done

if [ "$status" -eq 0 ]; then
  section "Abschluss"
  success "r abgeschlossen."
else
  section "Abschluss"
  error "r fehlgeschlagen. Exit-Code: $status"
fi

exit "$status"
