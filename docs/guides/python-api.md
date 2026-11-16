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

found = core.summary(store)                   # what was done and which results are honest
print(found["records_by_status"], [row["protocol_id"] for row in found["protocols"]])
print([e["seq"] for e in core.log(store, type="record", tail=5)])
```

## Reference

Functions, return values and error classes are listed in the [Python API reference](../reference/python-api.md).

## The clock

Pass `clock=lambda: "2026-11-15T10:00:00Z"` to fix the timestamp in tests, or set `PROTOCOLITH_NOW`. The value
must be `YYYY-MM-DDTHH:MM:SSZ`.

## Stability

The core API follows semantic versioning from 1.0. Until then, names may change between minor releases; the
ledger format `v` is the stable contract and is covered by the [conformance vectors](../reference/conformance-vectors.md).
