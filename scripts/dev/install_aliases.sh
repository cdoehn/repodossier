#!/usr/bin/env bash
set -u

print_help() {
  cat <<'HELP'
Usage:
  scripts/dev/install_aliases.sh [--shell bash|zsh] [--rc-file PATH] [--repo PATH] [--dry-run]

Installs a managed alias block for RepoDossier development:

  rdrepo  cd into the repository
  c       run the download patch runner
  r       run the export runner

The script stores the current clone path in REPODOSSIER_REPO inside the user's shell rc file.
HELP
}

shell_name=""
rc_file=""
repo_path=""
dry_run=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h)
      print_help
      exit 0
      ;;
    --shell)
      shell_name="${2:-}"
      shift 2
      ;;
    --rc-file)
      rc_file="${2:-}"
      shift 2
      ;;
    --repo)
      repo_path="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      print_help >&2
      exit 2
      ;;
  esac
done

if [ -z "$repo_path" ]; then
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    repo_path="$(git rev-parse --show-toplevel)"
  else
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    repo_path="$(cd "$script_dir/../.." && pwd)"
  fi
fi

if [ ! -d "$repo_path/.git" ]; then
  echo "Not a git repository: $repo_path" >&2
  exit 1
fi

if [ -z "$shell_name" ]; then
  shell_name="$(basename "${SHELL:-bash}")"
fi

if [ -z "$rc_file" ]; then
  case "$shell_name" in
    zsh)
      rc_file="$HOME/.zshrc"
      ;;
    bash|sh)
      rc_file="$HOME/.bashrc"
      ;;
    *)
      rc_file="$HOME/.bashrc"
      ;;
  esac
fi

block_start="# >>> repodossier dev aliases >>>"
block_end="# <<< repodossier dev aliases <<<"

new_block="$(cat <<EOF
$block_start
export REPODOSSIER_REPO="$repo_path"
alias rdrepo='cd "$REPODOSSIER_REPO"'
alias c='bash "$REPODOSSIER_REPO/scripts/dev/run_latest_download_patch.sh"'
alias r='bash "$REPODOSSIER_REPO/scripts/dev/r.sh"'
$block_end
EOF
)"

if [ "$dry_run" -eq 1 ]; then
  echo "Would update: $rc_file"
  printf '%s\n' "$new_block"
  exit 0
fi

mkdir -p "$(dirname "$rc_file")"
touch "$rc_file"

python3 - "$rc_file" "$block_start" "$block_end" "$new_block" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

rc_path = Path(sys.argv[1])
start = sys.argv[2]
end = sys.argv[3]
new_block = sys.argv[4]

text = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""

if start in text and end in text:
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    text = before.rstrip() + "\n\n" + new_block + "\n" + after.lstrip()
else:
    separator = "\n\n" if text.strip() else ""
    text = text.rstrip() + separator + new_block + "\n"

rc_path.write_text(text, encoding="utf-8")
PY

echo "Installed RepoDossier aliases in: $rc_file"
echo "Run this now:"
echo "  source $rc_file"
echo
echo "Aliases:"
echo "  rdrepo"
echo "  c"
echo "  r"
