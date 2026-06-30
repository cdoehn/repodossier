#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

if command -v pipx >/dev/null 2>&1; then
  PIPX_RUNNER=(pipx)
elif "$PYTHON_BIN" -m pipx --version >/dev/null 2>&1; then
  PIPX_RUNNER=("$PYTHON_BIN" -m pipx)
else
  echo "Fehler: pipx ist nicht installiert."
  echo "Installiere pipx und starte dieses Release-Validierungsskript erneut."
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Fehler: git ist für die pipx Release Validation erforderlich."
  exit 2
fi

WORK_DIR="$(mktemp -d)"
export PIPX_HOME="$WORK_DIR/pipx-home"
export PIPX_BIN_DIR="$WORK_DIR/pipx-bin"
mkdir -p "$PIPX_HOME" "$PIPX_BIN_DIR"

cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

echo "== pipx release validation =="
echo "Project: $ROOT_DIR"
echo "PIPX_HOME: $PIPX_HOME"
echo "PIPX_BIN_DIR: $PIPX_BIN_DIR"

echo
echo "== Install package with isolated pipx home =="
"${PIPX_RUNNER[@]}" install "$ROOT_DIR"

CLI="$PIPX_BIN_DIR/repocontext"
if [ ! -x "$CLI" ]; then
  echo "Fehler: repocontext wurde nicht im temporären pipx bin dir gefunden."
  find "$WORK_DIR" -maxdepth 4 -type f -name "repocontext" -print || true
  exit 1
fi

echo
echo "== CLI help checks =="
"$CLI" --help
"$CLI" full --help
"$CLI" export-ai --help
"$CLI" export-docs --help
"$CLI" changed --help

echo
echo "== Optional version check =="
if "$CLI" --version >/dev/null 2>&1; then
  "$CLI" --version
else
  echo "Hinweis: repocontext --version ist noch nicht verfügbar. Das wird im Release-Version-Schritt geprüft."
fi

SMOKE_REPO="$WORK_DIR/smoke-repo"
mkdir -p "$SMOKE_REPO/src" "$SMOKE_REPO/scripts" "$SMOKE_REPO/docs"

cat > "$SMOKE_REPO/README.md" <<'EOF'
# pipx smoke repo

This repository validates RepoContext from a pipx-installed command.
EOF

cat > "$SMOKE_REPO/pyproject.toml" <<'EOF'
[project]
name = "pipx-smoke-repo"
version = "0.1.0"
EOF

cat > "$SMOKE_REPO/src/example.py" <<'EOF'
import math

class PipxGreeter:
    def greet(self, name: str) -> str:
        return f"Hello, {name}"

def circle_area(radius: float) -> float:
    return math.pi * radius * radius
EOF

cat > "$SMOKE_REPO/scripts/build.sh" <<'EOF'
#!/usr/bin/env bash

say_hello() {
  echo "hello from pipx smoke"
}

main() {
  say_hello
}

main "$@"
EOF

cat > "$SMOKE_REPO/docs/SPEC.md" <<'EOF'
# pipx smoke spec

This spec should be included in documentation exports.
EOF

cd "$SMOKE_REPO" || exit 1

git init
git config user.email "pipx-smoke@example.invalid"
git config user.name "RepoContext pipx Smoke"
git add .
git commit -m "Initial pipx smoke repo"

echo
echo "== Export checks from pipx-installed CLI =="
"$CLI" full
test -s full.txt

"$CLI" export-ai
test -s ai.txt

"$CLI" export-docs
test -s docs.txt

cat >> src/example.py <<'EOF'

def changed_by_pipx_validation() -> str:
    return "changed"
EOF

"$CLI" changed
test -s changed.txt
grep -q "changed_by_pipx_validation" changed.txt

echo
echo "== Reinstall check =="
"${PIPX_RUNNER[@]}" uninstall repocontext
"${PIPX_RUNNER[@]}" install "$ROOT_DIR"
"$CLI" --help

echo
echo "pipx release validation passed."
