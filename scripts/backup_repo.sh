#!/usr/bin/env bash
set -euo pipefail

# Backup the repository into backups/<name>.zip and snapshot dependency lists.
# - Excludes heavy build caches (node_modules, .next), VCS, and generated outputs.
# - Captures dependency manifests: npm tree (if available), pip freeze, and
#   common manifest files (package.json, package-lock.json, pyproject.toml, requirements*.txt).

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="backups"
DEPS_DIR="$BACKUP_DIR/deps_${TS}"
ARCHIVE="$BACKUP_DIR/biosteam_backup_${TS}.zip"

mkdir -p "$BACKUP_DIR" "$DEPS_DIR"

echo "[1/3] Snapshotting dependency information into $DEPS_DIR"

# Node (UI) dependency snapshots (without copying node_modules)
if [ -d "app/ui" ] && [ -f "app/ui/package.json" ]; then
  mkdir -p "$DEPS_DIR/ui"
  cp -f app/ui/package.json "$DEPS_DIR/ui/" || true
  [ -f app/ui/package-lock.json ] && cp -f app/ui/package-lock.json "$DEPS_DIR/ui/" || true
  [ -f app/ui/pnpm-lock.yaml ] && cp -f app/ui/pnpm-lock.yaml "$DEPS_DIR/ui/" || true
  [ -f app/ui/yarn.lock ] && cp -f app/ui/yarn.lock "$DEPS_DIR/ui/" || true
  if command -v npm >/dev/null 2>&1; then
    (
      cd app/ui
      # npm ls returns non-zero with peer warnings; tolerate failures.
      npm ls --all >"$DEPS_DIR/ui/npm_ls_${TS}.txt" 2>&1 || true
    )
  fi
fi

# Python dependency snapshots
if command -v python3 >/dev/null 2>&1; then
  python3 -V >"$DEPS_DIR/python_version_${TS}.txt" 2>&1 || true
  if python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip freeze >"$DEPS_DIR/pip_freeze_${TS}.txt" 2>&1 || true
  fi
fi

# Collect common manifest files for reproducibility
manifests=(
  "app/api/pyproject.toml"
  "pyproject.toml"
  "requirements.txt"
  "requirements-dev.txt"
  "requirements_test.txt"
  "pkgs/thermosteam/src/thermosteam/requirements.txt"
)
for f in "${manifests[@]}"; do
  if [ -f "$f" ]; then
    dest="$DEPS_DIR/$(dirname "$f")"
    mkdir -p "$dest"
    cp -f "$f" "$dest/"
  fi
done

echo "[2/3] Creating archive $ARCHIVE"

# Build zip, excluding heavy caches and generated outputs
zip -r "$ARCHIVE" . \
  -x \
  ".git/*" \
  "**/__pycache__/*" \
  "**/.ipynb_checkpoints/*" \
  "app/ui/.next/*" \
  "app/ui/node_modules/*" \
  "RunUI.app/*" \
  "scenarios/OPN_demo/results/*"

echo "[3/3] Archive details:"
ls -lh "$ARCHIVE" || true

echo "Top of archive contents:"
zipinfo -1 "$ARCHIVE" | head -n 20 || true

echo "Done. Backup written to: $ARCHIVE"

