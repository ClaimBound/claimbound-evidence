# Conformance vectors

The reference implementation is `protocolith.core`. Another implementation can claim compatibility by passing
the language-neutral vectors in `spec/vectors/`.

| File | Cases | What it tests |
| --- | --- | --- |
| `canonical.json` | 43 | Parse the input strictly (`input_text`, or `input_hex` for raw bytes) and compare with the canonical text, or with an error code. |
| `hashes.json` | 7 | `sha256` of the canonical bytes of a parsed input. |
| `ledgers.json` | 45 | Verify the ledger text (or the expanded `ledger_template`: `head` + `fill` repeated `count` times + `tail`) and compare `ok` and the sorted unique rule codes. |

Every rule R1 to R11 has at least one failing ledger vector, and there are vectors for the size and depth
limits and for valid flows (empty ledger, freeze only, full flow, new version). All files carry
`"format": "protocolith-vectors/1"`.

## Running them

The repository test `tests/core/test_vectors.py` runs every case against the reference implementation, and checks
that the committed files are identical to a fresh build by `scripts/build_core_vectors.py`:

```bash
uv run pytest -q tests/core/test_vectors.py
```

Ledger vectors that contain `issue` entries are checked with the reference card builder (rule R9), so an
implementation that does not render cards has to decide how to treat those cases.

## Changing them

A change to the vectors is a change to the specification and needs a version bump
([spec section 6](../spec/CORE_SPEC.md)). Regenerate with `scripts/build_core_vectors.py` and commit both the
script and the files.

## Status

There is one implementation. A second implementation that passes the vectors is one of the conditions for
version 1.0.0 and does not exist yet.
