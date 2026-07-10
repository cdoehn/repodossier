#!/usr/bin/env bash
set -euo pipefail

# Candidate wrapper for the future RepoDossier download runner migration.
# Default mode stays compatibility-safe and delegates to the productive legacy runner.
# The productive entry point run_latest_download_patch.sh is not changed by this candidate.

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
legacy_runner="$script_dir/run_latest_download_patch.sh"
mode="${PATCHHARBOR_DOWNLOAD_RUNNER_CANDIDATE_MODE:-compat}"

if [ "$mode" = "compat" ]; then
  exec "$legacy_runner" "$@"
fi

if [ "$mode" != "patchharbor" ]; then
  printf 'Unsupported PATCHHARBOR_DOWNLOAD_RUNNER_CANDIDATE_MODE: %s\n' "$mode" >&2
  exit 64
fi

if [ "$#" -eq 0 ]; then
  printf 'patchharbor candidate mode currently requires an explicit patch script path\n' >&2
  exit 64
fi

exec patchharbor run-script "$@"
