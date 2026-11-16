# Architecture

Protocolith has a small core and a larger body of older evidence-card tooling. This page describes the core.
The older repository-level description is in [ARCHITECTURE](../ARCHITECTURE.md) and is kept in the archive.

## Layers

```text
CLI (protocolith.cli, core/commands.py)   MCP server (core/mcp.py)   Python API (protocolith.core)
                         \                        |                       /
                          +---------------  core/ops.py  ----------------+
                                              |
        rules.py (Verifier, rules R1-R11)   issue.py (card)   store.py (files, lock)
                                              |
                  ledger.py (entry format)  canonical.py (PCJ-1)  clock.py  errors.py
```

All three interfaces call the same operations in `core/ops.py`, so they have the same semantics.

## Modules of `protocolith.core`

| Module | Role |
| --- | --- |
| `canonical.py` | Strict JSON parser and canonical serialiser (PCJ-1), `sha256_hex` |
| `ledger.py` | Constants (`MAX_ENTRY_BYTES`, `RESULT_STATUSES`), entry hashing and line serialisation |
| `rules.py` | `Verifier`: an incremental checker fed one line at a time; `scan` verifies a whole file |
| `store.py` | Store directory, advisory lock, durable append, truncate |
| `_lock_posix.py`, `_lock_windows.py` | `fcntl.flock` and `msvcrt.locking` wrappers, chosen at import time |
| `ops.py` | `freeze`, `record`, `deviation`, `verify`, `entries`, `log`, `show`, `summary`, `head`, `init`, `issue`, `repair_truncate_partial_tail` |
| `views.py` | Read-only views over a loaded ledger: filtered log, one entry with context, summary |
| `schema.py` | JSON Schema (draft 2020-12) derived from the rules |
| `capture.py` | Environment and input-file fragment for a record `outcome` |
| `issue.py` | Build, validate and write the card; uses the evidence-card validator and SVG renderer of the package |
| `commands.py` | CLI glue and exit codes |
| `mcp.py` | stdio JSON-RPC server: eleven tools and read-only resources |
| `atlas.py`, `atlas_assets/`, `atlas_i18n/` | Offline HTML atlas builder; page template, style and script; the English UI catalog |
| `errors.py`, `clock.py` | Error classes with stable codes; injectable UTC clock |

## Write path

1. Take the exclusive lock.
2. Load the whole ledger and verify it. If it does not verify, stop with `VERIFICATION_FAILED`.
3. Build the next entry from the verifier state (`seq`, `prev`, timestamp) and feed it to the same `Verifier`.
   Any violation rejects the operation before a byte is written.
4. Append the line (`write`, `flush`, `fsync`; when the file is created, the directory is synced too where the platform supports it).
5. Release the lock.

`issue` additionally renders the card files before appending the `issue` line, writing each atomically
(temporary file, `fsync`, `os.replace`).

## Design decisions

- **Reads are lock-friendly.** Readers take the same lock when they can open the lock file and read without it
  otherwise (for example a read-only copy).
- **Nothing is ever rewritten.** The only operation that shortens the file is `repair`, and only for a partial
  last line.
- **Standard library only.** The core imports nothing outside the standard library and the package's own
  evidence-card validator and SVG renderer. The package declares no runtime dependencies.
- **Closed vocabularies.** Entry types, statuses and body keys are closed sets, so an entry means one thing.
- **Specification first.** The normative text is the [core specification](../spec/CORE_SPEC.md); the vectors
  in `spec/vectors/` tie the code to it.

## Not in the core

Running experiments, fetching data, scheduling, storing raw payloads and judging protocols. The runners for
public sources (weather, tide and similar) are older components outside the core; see the
[archive](../archive/README.md).
