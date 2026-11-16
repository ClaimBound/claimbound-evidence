# Python API reference

The API is the `protocolith.core` package. For a worked example see the [Python API guide](../guides/python-api.md).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `freeze(store, protocol, *, supersedes=None, clock=None)` | the new entry (dict) | `protocol` must be an object |
| `record(store, body, *, clock=None)` | the new entry | |
| `deviation(store, body, *, clock=None)` | the new entry | |
| `verify(store, expect_head=None)` | `Verdict` | `expect_head="SEQ:HASH"` adds the anchored-head check; never raises for a bad ledger; raises `EnvError` (`NO_LEDGER`) for a missing one |
| `entries(store)` | list of entries | raises `VerificationFailed` if the ledger does not verify |
| `log(store, *, protocol=None, type=None, status=None, tail=None)` | list of entries | filtered `entries`; unknown `protocol` is `UNKNOWN_PROTOCOL` |
| `show(store, seq)` | `{"entry", "protocol", "points_at", "pointed_by"}` | unknown `seq` is `DANGLING_REF` |
| `summary(store, protocol=None)` | dict (see [spec 5.1](../spec/CORE_SPEC.md)) | does not raise for a ledger that fails verification: `ok` is false and `problems` lists why |
| `init(store)` | `{"created", "path"}` | creates an empty ledger; harmless to repeat |
| `capture(files=(), *, env=False, base=None)` | `{"environment", "inputs"}` | hashes files inside `base` (default the working directory); `BAD_PATH` otherwise |
| `schema_for(name)` | JSON Schema dict | `freeze`, `record`, `deviation`, `issue` or `entry` |
| `head(store)` | `{"count", "hash", "seq"}` | `hash` and `seq` are `None` for an empty ledger |
| `issue(store, seq, *, out=None, clock=None)` | `{"card", "entry", "json_path", "svg_path"}` | |
| `repair_truncate_partial_tail(store)` | bytes removed | see [repair](../guides/repair-and-crash-recovery.md) |
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

The operations are the same as the CLI commands and the [MCP tools](mcp.md).
