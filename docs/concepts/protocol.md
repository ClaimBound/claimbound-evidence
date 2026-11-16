# Protocol

A protocol is a JSON object that states, before a run, what will be checked and when the result counts as a pass.

Protocolith requires only two keys:

| Key | Rule |
| --- | --- |
| `protocol_id` | Letters, digits, `.`, `_`, `-`; starts with a letter or digit; at most 128 characters. |
| `version` | Letters, digits, `.`, `_`, `-`, `+`; starts with a letter or digit; at most 64 characters. |

Everything else is up to you: the question, the data source, the gate, the metric, how missing data is handled.
Protocolith does not interpret those keys and does not judge whether the protocol is a good one. What it
guarantees is that the protocol that was frozen cannot be changed without leaving a trace.

## What belongs in a protocol

Things you would be tempted to adjust after seeing the result:

- the source and the period or sample it covers;
- the metric and the exact gate (threshold, comparison);
- the baseline or control;
- what counts as a blocked source or insufficient coverage;
- the claim boundary you intend to publish.

## Identity

A protocol is identified by `protocol_sha256`, the SHA-256 of its [canonical JSON](canonical-json.md) bytes. Two
files that differ only in whitespace or key order have the same hash. A record names the protocol by this hash,
not by `protocol_id` and `version`.

## Versions

A protocol version is frozen once. To change a protocol, freeze a new version with `--supersedes OLD_HASH`; see
[freeze](freeze.md). Old records keep pointing at the hash they were run under.

## Constraints on content

Values are objects, arrays, strings, booleans, null and integers within +/- (2^53 - 1). Floats are not
accepted; write decimals as strings (`"0.001"`). Nesting depth is at most 64. A whole ledger line, including
the protocol, is at most 1,048,576 bytes.
