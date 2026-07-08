#!/usr/bin/env bash
set -u
runner_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$runner_dir/run_repodossier_exports.sh" "$@"
