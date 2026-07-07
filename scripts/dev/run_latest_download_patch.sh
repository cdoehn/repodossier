#!/usr/bin/env bash
set -u

usage() {
  cat <<'USAGE'
Usage:
  c
  c /path/to/patch.sh
  c --help

Without arguments, runs the newest *.sh file directly in ~/Downloads.
The runner:
  1. finds the newest patch script in Downloads,
  2. checks bash syntax with bash -n,
  3. logs stdout and stderr to ~/Downloads/<script>_<timestamp>.log,
  4. moves the script to ~/Downloads/done on success,
  5. moves the script to ~/Downloads/failed on failure.
USAGE
}

download_dir="${PATCH_DOWNLOAD_DIR:-$HOME/Downloads}"
done_dir="$download_dir/done"
failed_dir="$download_dir/failed"

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
  echo "Kein Patch-Script in $download_dir gefunden."
  exit 1
fi

if [ ! -f "$patch_script" ]; then
  echo "Patch-Script nicht gefunden: $patch_script"
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

echo "== c: Download patch runner =="
echo "Patch script: $patch_script"
echo "Logfile: $run_log"
echo "Started: $(date --iso-8601=seconds)"
echo

echo "== Syntax check: bash -n =="
if ! bash -n "$patch_script"; then
  status=$?
  echo
  echo "Syntax check failed with status $status."
  moved_to="$(move_script_to "$failed_dir" "$patch_script")"
  echo "Moved failed script to: $moved_to"
  echo "Logfile remains at: $run_log"
  exit "$status"
fi

echo "Syntax OK."
echo

echo "== Execute patch script =="
bash "$patch_script"
status=$?

echo
echo "== Patch script finished =="
echo "Exit status: $status"

if [ "$status" -eq 0 ]; then
  moved_to="$(move_script_to "$done_dir" "$patch_script")"
  echo "Moved successful script to: $moved_to"
else
  moved_to="$(move_script_to "$failed_dir" "$patch_script")"
  echo "Moved failed script to: $moved_to"
fi

echo "Logfile remains at: $run_log"
echo "Finished: $(date --iso-8601=seconds)"

exit "$status"
