#!/usr/bin/env bash
# Local release gate: every check that must pass before a tag is cut.
# Resumable: steps that already passed for the current HEAD are skipped
# (state in .release_gate/<HEAD>.done, git-ignored). Use --fresh to redo all.
# Usage: scripts/release_gate.sh [--fresh]   (run from the repo root, any OS with bash)
set -uo pipefail

cd "$(git rev-parse --show-toplevel)"
HEAD_SHA="$(git rev-parse HEAD)"
STATE_DIR=".release_gate"
DONE="$STATE_DIR/$HEAD_SHA.done"
LOG="$STATE_DIR/$HEAD_SHA.log"
mkdir -p "$STATE_DIR"
[ "${1:-}" = "--fresh" ] && : > "$DONE"
touch "$DONE"
: "${UV_CACHE_DIR:=${TMPDIR:-/tmp}/uv-cache}"
export UV_CACHE_DIR

START=$(date +%s)
TOTAL=9
N=0
FAILED=0

step() { # name, command...
  local name="$1"; shift
  N=$((N + 1))
  if grep -qx "$name" "$DONE"; then
    printf '[%d/%d] SKIP (already passed) %s\n' "$N" "$TOTAL" "$name"
    return
  fi
  printf '[%d/%d] RUN  %s ... ' "$N" "$TOTAL" "$name"
  if "$@" >>"$LOG" 2>&1; then
    echo "ok ($(( $(date +%s) - START ))s elapsed)"
    echo "$name" >> "$DONE"
  else
    echo "FAIL  (see $LOG)"
    FAILED=1
    return 1
  fi
}

check_clean_main() {
  [ -z "$(git status --porcelain)" ] || { echo "working tree not clean"; return 1; }
  git fetch origin main --quiet || return 1
  [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "HEAD != origin/main"; return 1; }
}

check_versions() {
  python3 - <<'PY'
import json, re, sys, pathlib
py = re.search(r'^version\s*=\s*"([^"]+)"', pathlib.Path("pyproject.toml").read_text(), re.M).group(1)
rv = re.search(r'^repo_semver:\s*([^\s]+)', pathlib.Path("specs/repo_version.yaml").read_text(), re.M).group(1)
cff = re.search(r'^version:\s*"?([^"\n]+)"?', pathlib.Path("CITATION.cff").read_text(), re.M).group(1)
cl = pathlib.Path("CHANGELOG.md").read_text()
badge = pathlib.Path("docs/assets/badge_release.svg").read_text()
errs = []
if rv != py: errs.append(f"repo_version.yaml {rv} != pyproject {py}")
if cff != py: errs.append(f"CITATION.cff {cff} != pyproject {py}")
if py not in cl: errs.append("CHANGELOG has no entry for " + py)
if py not in badge: errs.append("badge_release.svg does not mention " + py)
json.loads(pathlib.Path(".zenodo.json").read_text())
if errs:
    print("\n".join(errs)); sys.exit(1)
print("versions consistent:", py)
PY
}

wheel_smoke() {
  local tmp; tmp="$(mktemp -d)"
  python3 -m venv "$tmp/v" || return 1
  "$tmp/v/bin/pip" install --quiet dist/*.whl || return 1
  "$tmp/v/bin/claimbound" --version || return 1
  "$tmp/v/bin/claimbound" doctor || return 1
  rm -rf "$tmp"
}

step "tree clean and equal to origin/main" check_clean_main || true
step "versions consistent (pyproject, spec, CITATION.cff, CHANGELOG, badge, .zenodo.json)" check_versions || true
step "uv sync" uv sync --extra dev || true
step "ruff" uv run ruff check src tests || true
step "claimbound validate-all" uv run claimbound validate-all || true
step "pytest" uv run --extra dev pytest -q -n auto || true
step "build sdist+wheel (clean dist)" bash -c 'rm -rf dist && uv build' || true
step "twine check" uvx twine check dist/* || true
step "wheel installs in clean venv, doctor ok" wheel_smoke || true

echo "elapsed: $(( $(date +%s) - START ))s; log: $LOG"
if [ "$FAILED" -ne 0 ]; then echo "RELEASE GATE: FAILED"; exit 1; fi
sha256sum dist/* 2>/dev/null || shasum -a 256 dist/*
echo "RELEASE GATE: PASSED for $HEAD_SHA"
