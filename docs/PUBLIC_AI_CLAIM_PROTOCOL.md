# Public AI Claim Protocol

Rules for auditing what a public AI source (documentation, model card, system
card, API reference, repository) says. A source-audit card records the source
and its boundary. It is not an evaluation of the model.

This protocol sits under the [AI Operator Protocol](AI_OPERATOR_PROTOCOL.md) and
the [Scaffold Automation Plan](SCAFFOLD_AUTOMATION_PLAN.md). Scaffolds created
for these tracks are GRAY DRAFT / NOT_EVIDENCE until an operator runs and
validates them.

Machine-readable form: `specs/public_ai_claim_metadata.schema.json`, checked by
`claimbound_evidence.public_ai_protocol.validate_public_ai_claim_metadata`.

## 1. Source-Audit Rules

- Audit only public, officially published sources. Name the publisher, URL,
  access date and capture method.
- Freeze the claim list and the source boundary before reading outcomes.
- Record a source rights and attribution note. If rights are unclear, stop
  (`rights_unclear`).
- Hash the captured source content (`content_sha256`). Keep raw captures local
  (`raw_payload_committed: false`).
- Record what the source states, quote at most a short fragment, and record
  what it does not state. Absence in the source is not a negative finding.
- Do not substitute a different source after seeing the result of a blocked or
  insufficient one. `BLOCKED_SOURCE` and `INSUFFICIENT_COVERAGE` are valid
  published outcomes.
- Re-access of a changed source is a new record (source drift), not an edit.

## 2. Model And API Metadata Fields

Under `model`:

| Field | Rule |
| --- | --- |
| `provider` | Organization named by the source. |
| `model_name` | Exact name as written in the source. |
| `model_version` | Exact version or snapshot id, or `NOT_STATED`. Never guessed. |
| `api_endpoint` | Optional; only if the source documents it. |
| `api_metadata_source` | `documented`, `observed` or `not_stated`. |

If model identity cannot be verified from the source, stop
(`model_identity_unverifiable`) instead of inferring it.

## 3. Prompt And Transcript Hash Policy

- Store `prompt_sha256` and `transcript_sha256` (lowercase sha256 hex) of the
  exact bytes used. Use `NOT_APPLICABLE` only when no prompt or transcript
  exists.
- Never commit raw prompts or raw transcripts: `raw_prompt_committed` and
  `raw_transcript_committed` must be `false`. Raw text stays in a local run
  root outside the repository.
- Never fabricate or recompute a hash from edited text. A missing hash is a
  stop (`hash_missing`).

## 4. Screenshot-Only Limits

A screenshot proves only that something was displayed at capture time.

- Set `screenshot_only: true`, `claim_class: source_audit_screenshot_limited`
  and record `screenshot_sha256`.
- A screenshot-only record cannot support claims about text beyond what is
  visible, about other pages, or about later states of the source.
- Prefer an HTTP capture, a manual copy of the text or an archive snapshot.
  If only a screenshot exists, the honest outcome is usually
  `INSUFFICIENT_COVERAGE` (stop rule `screenshot_only_coverage`).

## 5. Stop Rules

Stop and record the exact outcome when any of these occur:

`source_blocked`, `rights_unclear`, `hash_missing`,
`model_identity_unverifiable`, `screenshot_only_coverage`,
`protocol_changed_after_outcome`.

A triggered stop rule cannot end with `audit_outcome: recorded` (screenshot-only
records are the only documented exception, and stay limited).

## 6. What A Source-Audit Card Must NOT Imply

Every record lists these in `forbidden_implications`, and the claim boundary
must not state or suggest any of them:

- `model_safety`: that the model is safe, aligned or low-risk;
- `model_quality`: that the model is accurate, capable or reliable;
- `runtime_behavior`: that deployed behavior matches what the documentation says;
- `benchmark_superiority`: that the model is better than another model or
  leads a benchmark.

A source-audit card shows only that the public source says, or does not say,
specific things on the access date. Nothing here is a legal, safety or
deployment certification.

## 7. Validation

```python
from claimbound_evidence.public_ai_protocol import validate_public_ai_claim_metadata

problems = validate_public_ai_claim_metadata(metadata)
```

An empty list means the metadata conforms. The validator checks shape and
honesty constraints; it never assigns a result status.
