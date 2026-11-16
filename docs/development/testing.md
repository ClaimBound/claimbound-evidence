# Testing and coverage policy

## Commands

```bash
uv sync --extra dev
uv run ruff check src tests
uv run mypy                       # strict type check of protocolith.core
uv run --extra dev pytest -q -n auto
uv run pytest -q tests/core                       # the core only
uv run pytest -q tests/test_readme_examples.py    # README commands
```

Slow and performance tests are excluded by default; run them with `-m 'slow or perf'`.

## Coverage policy

- The reference implementation, `protocolith.core`, is held at **100% line and branch coverage**.
- The two platform-specific lock modules carry `# pragma: no cover` as a whole, because each runs only on its
  own platform; both are exercised in CI on their platform.
- Coverage is configured with `branch = true` and `source = ["protocolith.core"]` in `pyproject.toml`, so a
  plain `--cov` run reports the core.

```bash
uv run --extra dev pytest tests/core tests/core_hardening -q --cov=protocolith.core --cov-branch --cov-report=term-missing
```

Whether a threshold is enforced as a failing check in CI is not configured in the repository today
(`--fail-under` is not set); the 100% figure is a maintained property, checked by running the command above.

## What the test suites cover

| Suite | Covers |
| --- | --- |
| `tests/core/test_canonical.py` | PCJ-1 parsing and serialisation |
| `tests/core/test_rules.py` | each rule R1 to R11 and the limits |
| `tests/core/test_ops.py` | the operations, locking, durability and repair |
| `tests/core/test_core_cli.py` | CLI exit codes and output |
| `tests/core/test_mcp.py` | the MCP server |
| `tests/core/test_vectors.py` | the conformance vectors, and that the committed vectors equal a fresh build |
| `tests/test_readme_examples.py` | every command and snippet shown in the README |
| `tests/test_docs_site.py` | the generated CLI reference and the documentation build |
| `tests/test_publication_guard.py` | tracked text contains no forbidden tokens, absolute home paths or raw payload files |

## Platforms and versions in CI

`.github/workflows/tests.yml` runs on Ubuntu, Windows and macOS. The matrix covers Python 3.11, 3.12, 3.13, 3.14
and 3.15, with 3.11, 3.12 and 3.15 on all three systems and 3.13 and 3.14 on Ubuntu. A separate `core-coverage` job runs
`tests/core` on all three systems with `--cov=protocolith.core --cov-branch --cov-fail-under=100`, so the 100% figure is
enforced in CI; each platform-specific lock module is excluded on the other platforms by its own pragma.

## Honesty rules for tests

Tests that depend on the outcome of an evidence run must not change a blocked or insufficient result into a pass.
`BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE`, `NEGATIVE_RESULT_UNDER_PROTOCOL` and source drift are first-class
outcomes; see [AGENTS.md](../../AGENTS.md).

## Mutation score

Measured on 2026-11-16 with `scripts/mutation_core.sh` (mutmut 3.8.1) over `canonical.py`, `ledger.py` and `rules.py`: 826 of 911 mutants
killed (90.7 percent), 85 survived (mostly error-message text and equivalent mutants). The target for the core is at least 90 percent.
