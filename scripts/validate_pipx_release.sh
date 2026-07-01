#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

if ! "$PYTHON_BIN" -m pipx --version >/dev/null 2>&1; then
  echo "Fehler: pipx ist für ${PYTHON_BIN} nicht verfügbar."
  echo "Installiere pipx für diesen Python-Kontext und starte die Release-Validierung erneut."
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Fehler: git ist für die pipx Release Validation erforderlich."
  exit 2
fi

WORK_DIR="$(mktemp -d)"
export PIPX_HOME="$WORK_DIR/pipx-home"
export PIPX_BIN_DIR="$WORK_DIR/pipx-bin"
export PATH="$PIPX_BIN_DIR:$PATH"
mkdir -p "$PIPX_HOME" "$PIPX_BIN_DIR"

cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

echo "== Build checkout path =="
echo "Repository: $REPO_ROOT"
echo "Python: $PYTHON_BIN"
echo "PIPX_HOME: $PIPX_HOME"
echo "PIPX_BIN_DIR: $PIPX_BIN_DIR"

echo
echo "== Install with isolated pipx =="
"$PYTHON_BIN" -m pipx uninstall repodossier 2>/dev/null || true
"$PYTHON_BIN" -m pipx install "$REPO_ROOT"

REPODOSSIER_CLI="$PIPX_BIN_DIR/repodossier"
REPOCONTEXT_CLI="$PIPX_BIN_DIR/repocontext"

if [ ! -x "$REPODOSSIER_CLI" ]; then
  echo "Fehler: repodossier wurde nicht im temporären pipx bin dir gefunden."
  find "$WORK_DIR" -maxdepth 5 -type f -name "repodossier" -print || true
  exit 1
fi

if [ ! -x "$REPOCONTEXT_CLI" ]; then
  echo "Fehler: repocontext wurde nicht im temporären pipx bin dir gefunden."
  find "$WORK_DIR" -maxdepth 5 -type f -name "repocontext" -print || true
  exit 1
fi

echo
echo "== Check repodossier CLI =="
repodossier --help
repodossier --version

echo
echo "== Check repocontext legacy CLI =="
repocontext --help
repocontext --version

echo
echo "== Create sample git repository =="
SAMPLE_REPO="$WORK_DIR/sample_repo"
mkdir -p "$SAMPLE_REPO/src" "$SAMPLE_REPO/scripts" "$SAMPLE_REPO/docs"
cd "$SAMPLE_REPO"

git init
git config user.email "test@example.invalid"
git config user.name "RepoDossier Test"

cat > README.md <<'EOF'
# Sample Repository

This repository validates RepoDossier from an isolated pipx installation.
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "sample-repository"
version = "0.1.0"
dependencies = [
    "PyYAML>=6.0",
]
EOF

cat > src/demo.py <<'EOF'
import math


class Demo:
    def greet(self, name: str) -> str:
        return f"Hello, {name}"


def circle_area(radius: float) -> float:
    return math.pi * radius * radius
EOF

cat > scripts/demo.sh <<'EOF'
#!/usr/bin/env bash

say_hello() {
  echo "hello"
}

say_hello
EOF

cat > docs/usage.md <<'EOF'
# Usage

Run the sample command.
EOF

git add README.md pyproject.toml src/demo.py scripts/demo.sh docs/usage.md
git commit -m "Initial sample project"

echo
echo "== Smoke full export =="
repodossier full
test -s full.txt
grep -q "AI Quick Start" full.txt
grep -q "Repository Statistics" full.txt

echo
echo "== Smoke AI export =="
repodossier export-ai
test -s ai.txt
grep -q "Project summary" ai.txt

echo
echo "== Smoke docs export =="
repodossier export-docs
test -s docs.txt
grep -q "Documentation" docs.txt

echo
echo "== Smoke changed export =="
printf '\n# changed\n' >> README.md
repodossier changed
test -s changed.txt
grep -q "Changed" changed.txt
grep -q "README.md" changed.txt

echo
echo "== Smoke legacy alias export =="
rm -f ai.txt
repocontext export-ai
test -s ai.txt
grep -q "Project summary" ai.txt

echo
echo "pipx release validation completed successfully."
