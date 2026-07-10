#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CYAN='\033[38;5;45m'
INFO='\033[38;5;39m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

ALL_MODES=(all full ai docs changed)
PATCHHARBOR_PLAN_FILE=""

cleanup_patchharbor_plan() {
  if [ -n "${PATCHHARBOR_PLAN_FILE:-}" ] && [ -e "$PATCHHARBOR_PLAN_FILE" ]; then
    rm -f "$PATCHHARBOR_PLAN_FILE"
  fi
}
trap cleanup_patchharbor_plan EXIT

log_info() {
  printf "${CYAN}r${NC} ${INFO}info${NC}  %s\n" "$1"
}

log_do() {
  printf "${CYAN}r${NC} ${PURPLE}do${NC}    %s\n" "$1"
}

log_ok() {
  printf "${CYAN}r${NC} ${GREEN}ok${NC}    %s\n" "$1"
}

log_error() {
  printf "${CYAN}r${NC} ${RED}error${NC} %s\n" "$1"
}

print_help() {
  cat <<'HELP'
Usage:
  scripts/dev/run_repodossier_exports.sh [--dry-run] [--list-modes] [all] [full] [ai|quick|export-ai] [docs|doc] [changed|changes]

Runs RepoDossier exports for the current Git repository and copies common export
artifacts to the download directory.

Default modes:
  normal run: full ai
  dry-run:    full ai docs changed

Modes:
  full       runs: repodossier full
  ai         runs: repodossier export-ai
  quick      alias for: ai
  export-ai  alias for: ai
  docs       runs: repodossier export-docs
  doc        alias for: docs
  changed    runs: repodossier changed
  changes    alias for: changed
  all        alias for: full ai docs changed

Environment:
  REPODOSSIER_BIN       RepoDossier executable, default: repodossier
  PATCH_DOWNLOAD_DIR    Download directory, default: $HOME/Downloads
  PATCHHARBOR_REPO      PatchHarbor repository, default: sibling patch-harbor when available
HELP
}

print_modes() {
  printf '%s\n' "${ALL_MODES[@]}"
}

normalize_mode() {
  case "$1" in
    all)
      printf 'all\n'
      ;;
    full)
      printf 'full\n'
      ;;
    ai|quick|export-ai)
      printf 'ai\n'
      ;;
    docs|doc)
      printf 'docs\n'
      ;;
    changed|changes)
      printf 'changed\n'
      ;;
    *)
      return 1
      ;;
  esac
}

resolve_patchharbor_src() {
  local configured="${PATCHHARBOR_REPO:-}"
  local source_root=""
  local candidate=""

  if [ -n "$configured" ] && [ -f "$configured/src/patchharbor/export_planning.py" ]; then
    printf '%s\n' "$configured/src"
    return 0
  fi

  if source_root="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
    candidate="$(cd "$source_root/.." && pwd)/patch-harbor"
    if [ -f "$candidate/src/patchharbor/export_planning.py" ]; then
      printf '%s\n' "$candidate/src"
      return 0
    fi
  fi

  return 1
}

prepare_patchharbor_export_plan() {
  local patchharbor_src=""
  local plan_file=""

  if ! patchharbor_src="$(resolve_patchharbor_src)"; then
    log_info "PatchHarbor export plan: nicht verfügbar, verwende Source-Kompatibilitätsmodus"
    return 0
  fi

  if ! plan_file="$(mktemp "${TMPDIR:-/tmp}/patchharbor-export-plan.XXXXXX")"; then
    log_info "PatchHarbor export plan: temporäre Datei nicht verfügbar, verwende Source-Kompatibilitätsmodus"
    return 0
  fi

  if PYTHONPATH="$patchharbor_src${PYTHONPATH:+:$PYTHONPATH}" python3 - "$plan_file" "$REPODOSSIER_BIN" "$DRY_RUN" "${MODES[@]}" <<'PYEOF'
from __future__ import annotations

from pathlib import Path
import sys

from patchharbor.export_display import format_export_command
from patchharbor.export_model import ExportArtifact, ExportJob
from patchharbor.export_planning import create_export_plan

plan_file = Path(sys.argv[1])
repodossier_bin = sys.argv[2]
dry_run = sys.argv[3] == "1"
requested_names = tuple(sys.argv[4:])

jobs = (
    ExportJob("full", (repodossier_bin, "full"), artifacts=(ExportArtifact("full.txt"),), description="RepoDossier full export"),
    ExportJob("ai", (repodossier_bin, "export-ai"), artifacts=(ExportArtifact("ai.txt"),), description="RepoDossier AI export"),
    ExportJob("docs", (repodossier_bin, "export-docs"), artifacts=(ExportArtifact("docs.txt"),), description="RepoDossier docs export"),
    ExportJob("changed", (repodossier_bin, "changed"), artifacts=(ExportArtifact("changed.txt"),), description="RepoDossier changed export"),
)
plan = create_export_plan(jobs, requested_names=requested_names, dry_run=dry_run, output_directory="downloads")
lines = [f"{job.name}\t{format_export_command(job.command)}" for job in plan.selected_jobs]
plan_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
PYEOF
  then
    PATCHHARBOR_PLAN_FILE="$plan_file"
    log_info "PatchHarbor export plan: aktiv"
  else
    if [ -e "$plan_file" ]; then
      rm -f "$plan_file"
    fi
    PATCHHARBOR_PLAN_FILE=""
    log_info "PatchHarbor export plan: nicht nutzbar, verwende Source-Kompatibilitätsmodus"
  fi
}

planned_command_for_mode() {
  local mode="$1"
  local fallback="$2"
  local planned=""

  if [ -n "${PATCHHARBOR_PLAN_FILE:-}" ] && [ -f "$PATCHHARBOR_PLAN_FILE" ]; then
    planned="$(awk -F '\t' -v wanted="$mode" '$1 == wanted { print $2; found=1; exit } END { if (!found) exit 1 }' "$PATCHHARBOR_PLAN_FILE" 2>/dev/null || true)"
    if [ -n "$planned" ]; then
      printf '%s\n' "$planned"
      return 0
    fi
  fi

  printf '%s\n' "$fallback"
}

DRY_RUN=0
LIST_MODES=0
MODES=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h)
      print_help
      exit 0
      ;;
    --list-modes)
      LIST_MODES=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    *)
      if normalized="$(normalize_mode "$1")"; then
        if [ "$normalized" = "all" ]; then
          MODES+=(full ai docs changed)
        else
          MODES+=("$normalized")
        fi
        shift
      else
        log_error "Unbekannter r-Modus: $1"
        print_help
        exit 2
      fi
      ;;
  esac
done

if [ "$LIST_MODES" -eq 1 ]; then
  print_modes
  exit 0
fi

if [ "${#MODES[@]}" -eq 0 ]; then
  if [ "$DRY_RUN" -eq 1 ]; then
    MODES=(full ai docs changed)
  else
    MODES=(full ai)
  fi
fi

if ! REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  log_error "Kein Git-Repository: $(pwd)"
  exit 1
fi

cd "$REPO_ROOT" || exit 1

DOWNLOAD_DIR="${PATCH_DOWNLOAD_DIR:-$HOME/Downloads}"
REPODOSSIER_BIN="${REPODOSSIER_BIN:-repodossier}"

echo "${CYAN}${BOLD}r · RepoDossier Export Runner${NC}"
log_info "Repo: $REPO_ROOT"
log_info "Downloads: $DOWNLOAD_DIR"
log_info "Modi: ${MODES[*]}"

if ! command -v "$REPODOSSIER_BIN" >/dev/null 2>&1; then
  log_error "RepoDossier-Befehl nicht gefunden: $REPODOSSIER_BIN"
  exit 1
fi

prepare_patchharbor_export_plan

mkdir -p "$DOWNLOAD_DIR"

copy_if_exists() {
  local source_file="$1"
  local target_file="$2"

  if [ -f "$source_file" ]; then
    cp -f "$source_file" "$target_file"
    log_ok "Kopiert: $target_file"
  fi
}

run_mode() {
  local mode="$1"
  local command_text=""

  case "$mode" in
    full)
      log_do "Exportiere full"
      if [ "$DRY_RUN" -eq 1 ]; then
        command_text="$(planned_command_for_mode full "$REPODOSSIER_BIN full")"
        log_info "Befehl: $command_text"
      else
        "$REPODOSSIER_BIN" full
        local status=$?
        if [ "$status" -ne 0 ]; then
          log_error "full fehlgeschlagen. Exit-Code: $status"
          exit "$status"
        fi
        copy_if_exists "full.txt" "$DOWNLOAD_DIR/full.txt"
      fi
      ;;
    ai)
      log_do "Exportiere ai"
      if [ "$DRY_RUN" -eq 1 ]; then
        command_text="$(planned_command_for_mode ai "$REPODOSSIER_BIN export-ai")"
        log_info "Befehl: $command_text"
      else
        "$REPODOSSIER_BIN" export-ai
        local status=$?
        if [ "$status" -ne 0 ]; then
          log_error "ai fehlgeschlagen. Exit-Code: $status"
          exit "$status"
        fi
        copy_if_exists "ai.txt" "$DOWNLOAD_DIR/ai.txt"
      fi
      ;;
    docs)
      log_do "Exportiere docs"
      if [ "$DRY_RUN" -eq 1 ]; then
        command_text="$(planned_command_for_mode docs "$REPODOSSIER_BIN export-docs")"
        log_info "Befehl: $command_text"
      else
        "$REPODOSSIER_BIN" export-docs
        local status=$?
        if [ "$status" -ne 0 ]; then
          log_error "docs fehlgeschlagen. Exit-Code: $status"
          exit "$status"
        fi
        copy_if_exists "docs.txt" "$DOWNLOAD_DIR/docs.txt"
      fi
      ;;
    changed)
      log_do "Exportiere changed"
      if [ "$DRY_RUN" -eq 1 ]; then
        command_text="$(planned_command_for_mode changed "$REPODOSSIER_BIN changed")"
        log_info "Befehl: $command_text"
      else
        "$REPODOSSIER_BIN" changed
        local status=$?
        if [ "$status" -ne 0 ]; then
          log_error "changed fehlgeschlagen. Exit-Code: $status"
          exit "$status"
        fi
        copy_if_exists "changed.txt" "$DOWNLOAD_DIR/changed.txt"
      fi
      ;;
    *)
      log_error "Unbekannter r-Modus: $mode"
      exit 2
      ;;
  esac
}

for mode in "${MODES[@]}"; do
  run_mode "$mode"
done

if [ "$DRY_RUN" -eq 0 ]; then
  if [ -f "scripts/dev/patch-rules.md" ]; then
    copy_if_exists "scripts/dev/patch-rules.md" "$DOWNLOAD_DIR/patch-rules.md"
  else
    copy_if_exists "$SCRIPT_DIR/patch-rules.md" "$DOWNLOAD_DIR/patch-rules.md"
  fi
else
  log_info "Dry-run: keine Dateien geschrieben."
fi

log_ok "r abgeschlossen."
