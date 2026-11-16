#!/usr/bin/env bash
# Mutation testing of the PCJ-1 core with mutmut. Time-boxed and resumable: rerun to continue.
# Usage: scripts/mutation_core.sh [max_seconds]   (default 1200)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${MUTATION_WORKDIR:-${TMPDIR:-/tmp}/protocolith-mutation}"
LIMIT="${1:-1200}"
mkdir -p "$WORK"
if [ ! -d "$WORK/src" ]; then
  cp -R "$ROOT/src" "$WORK/src"
  mkdir -p "$WORK/spec" "$WORK/scripts" && cp -R "$ROOT/spec/vectors" "$WORK/spec/" && cp "$ROOT/scripts/build_core_vectors.py" "$WORK/scripts/"
  mkdir -p "$WORK/tests" && cp -R "$ROOT/tests/core" "$WORK/tests/core"
  cp "$ROOT/tests/core_hardening/test_core_regressions.py" "$ROOT/tests/core_hardening/hardening_support.py" "$WORK/tests/core/"
  cat > "$WORK/pyproject.toml" <<'EOF'
[tool.mutmut]
paths_to_mutate = ["src/protocolith/core/canonical.py", "src/protocolith/core/ledger.py", "src/protocolith/core/rules.py"]
tests_dir = ["tests/core/"]
pytest_add_cli_args = ["-k", "not subprocess and not process and not mcp_command"]
also_copy = ["src/protocolith/", "spec/", "scripts/"]

[tool.pytest.ini_options]
addopts = "-q -p no:cacheprovider"
EOF
fi
cd "$WORK"
# mutmut resumes from its mutants/ directory; timeout stops it cleanly after LIMIT seconds.
timeout "$LIMIT" uv run --no-sync --python "$ROOT/.venv/bin/python" --with mutmut mutmut run || echo "time box reached or run ended; rerun to resume"
uv run --no-sync --python "$ROOT/.venv/bin/python" --with mutmut mutmut results | tail -40 || true
