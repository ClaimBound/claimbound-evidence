# Python API

The API is the `protocolith.core` package. It uses only the standard library and mirrors the CLI.

```python
from pathlib import Path

from protocolith import core

store = core.Store(".protocolith")          # or a path; operations accept str or Path too
protocol = core.decode(Path("protocol.json").read_bytes())
entry = core.freeze(store, protocol)
print(entry["seq"], entry["hash"])

core.record(store, core.decode(Path("record.json").read_bytes()))
verdict = core.verify(store)
assert verdict.ok
result = core.issue(store, 1)
print(result["json_path"], result["card"]["result_status"])
print(core.head(store))
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `freeze(store, protocol, *, supersedes=None, clock=None)` | the new entry (dict) | `protocol` must be an object |
| `record(store, body, *, clock=None)` | the new entry | |
| `deviation(store, body, *, clock=None)` | the new entry | |
| `verify(store, expect_head=None)` | `Verdict` | `expect_head="SEQ:HASH"` adds the anchored-head check; never raises for a bad ledger; raises `EnvError` (`NO_LEDGER`) for a missing one |
| `entries(store)` | list of entries | raises `VerificationFailed` if the ledger does not verify |
| `head(store)` | `{"count", "hash", "seq"}` | `hash` and `seq` are `None` for an empty ledger |
| `issue(store, seq, *, out=None, clock=None)` | `{"card", "entry", "json_path", "svg_path"}` | |
| `repair_truncate_partial_tail(store)` | bytes removed | see [repair](repair-and-crash-recovery.md) |
| `scan(data, card_hasher=None)` | `(Verdict, Verifier)` | verify bytes without a store |
| `encode(value)`, `decode(raw)`, `sha256_hex(value)` | bytes, value, str | [canonical JSON](../concepts/canonical-json.md) |
| `resolve_store(path)` | `Store` | explicit path, then `PROTOCOLITH_STORE`, then `.protocolith` |

`Verdict` has `ok`, `count`, `head_seq`, `head_hash`, `violations`, `codes` and `to_dict()`.

## Errors

All errors derive from `ProtocolithError` and carry `code`, `message` and `violations`.

| Class | CLI exit code | Meaning |
| --- | --- | --- |
| `InputError` | 2 | bad input or a rejected operation; nothing was written |
| `VerificationFailed` | 1 | the stored ledger does not verify |
| `EnvError` | 3 | I/O or environment problem (`NO_LEDGER`, `LOCK_TIMEOUT`, `IO_ERROR`) |
| `CanonError` | | invalid JSON input for `decode` or `encode` |

```python
try:
    core.freeze(store, protocol)
except core.InputError as exc:
    print(exc.code, exc.message)             # e.g. DUPLICATE_FREEZE
```

## The clock

Pass `clock=lambda: "2026-11-15T10:00:00Z"` to fix the timestamp in tests, or set `PROTOCOLITH_NOW`. The value
must be `YYYY-MM-DDTHH:MM:SSZ`.

## Stability

The core API follows semantic versioning from 1.0. Until then, names may change between minor releases; the
ledger format `v` is the stable contract and is covered by the [conformance vectors](../reference/conformance-vectors.md).
