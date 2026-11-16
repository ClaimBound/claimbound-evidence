# Canonical JSON (PCJ-1)

All hashes are computed over canonical bytes, so the same data hashes the same in every language and on every
platform.

## Rules

- UTF-8, no byte-order mark, no whitespace between tokens, no trailing newline in the hashed bytes.
- Object keys are unique and sorted by Unicode code point. Duplicate keys in input are an error.
- Allowed values: object, array, string, boolean, null, and integers in [-(2^53 - 1), 2^53 - 1].
- **No floats.** Write decimals as strings (`"0.001"`). `-0` is the integer `0`.
- Strings may contain any Unicode except lone surrogates. Escapes are only `\"`, `\\`, `\b`, `\f`, `\n`, `\r`,
  `\t` and `\u00XX` for other control characters below U+0020; everything else is written literally.
- Nesting depth is at most 64 (the top-level container counts as 1).

`sha256(x)` is the lowercase 64-character hex SHA-256 of the canonical bytes of `x`.

## What it means for your files

Your `protocol.json` and `record.json` may be pretty-printed. They are parsed strictly (a byte-order mark,
duplicate keys, floats or numbers beyond the integer range are errors) and re-serialised canonically before
hashing and storing.

| Input | Result |
| --- | --- |
| `{"b":1,"a":2}` | stored as `{"a":2,"b":1}` |
| `{"t": 0.5}` | rejected, `FLOAT_NOT_ALLOWED` |
| `{"a":1,"a":2}` | rejected, `DUPLICATE_KEY` |
| file starting with a byte-order mark | rejected, `BAD_JSON` |

## Specification and vectors

The normative text is section 2 of the [core specification](../spec/CORE_SPEC.md). Language-neutral test cases
are in `spec/vectors/canonical.json`; see [conformance vectors](../reference/conformance-vectors.md).
In Python: `protocolith.core.encode`, `decode` and `sha256_hex`.
