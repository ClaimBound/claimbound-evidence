# ClaimBound Evidence Card

A ClaimBound evidence card is the public unit of record for one narrow result.

It should be small enough to read, strict enough to validate, and complete
enough for another operator to decide whether rerunning the protocol is
possible.

## Required Fields

| Field | Purpose |
| --- | --- |
| `evidence_id` | Stable ID for this evidence record. |
| `registry_sequence` | Positive integer sequence in the public registry. |
| `record_type` | Required record category: `evidence_result`, `source_audit`, `protocol_registration` or `reproduction_attempt`. |
| `protocol_id` | ID of the frozen protocol. |
| `protocol_version` | Version or commit-bound protocol reference. |
| `domain` | Public domain under test, such as energy or air quality. |
| `claim_type` | Type of claim: forecast, signal, source audit, reproduction or blocked-source record. |
| `execution_mode` | Required provenance mode: `MANUAL_NO_AI` or `AUTOMATED_AI_ASSISTED`. |
| `result_status` | Exact status from `docs/RESULT_STATUS.md`. |
| `claim_boundary` | Plain-language limit on what the result does and does not show. |
| `official_source_name` | Human-readable source name. |
| `official_source_url` | URL for the official source or source documentation. |
| `access_date` | Date the source was accessed. |
| `source_rights_note` | Short note on rights, attribution and redistribution boundary. |
| `raw_payload_committed` | Must be `false` unless rights and repository policy explicitly allow it. |
| `raw_payload_manifest` | External hash manifest path, hash value or explanation when blocked. |
| `sanitized_report_path` | Public sanitized report or summary artifact. |
| `sanitized_report_sha256` | SHA-256 for the sanitized report. |
| `git_commit` | Commit containing the protocol and public evidence record. |
| `runner_command` | Exact command or manual-track reference used for the run. |
| `operator` | Person, organization or role that performed the run. Use `maintainer` for repository maintainer runs, `local operator` for blocked or scaffold-only records, and an external GitHub handle for independent reruns. |
| `created_at` | Date the evidence card was created. |
| `last_verified_date` | Latest date this card status or source boundary was verified. |
| `verification_count` | Number of recorded verifications or same-operator reruns represented by this card. |
| `verification_level` | Verification strength: `SINGLE_OPERATOR`, `SINGLE_OPERATOR_RERUN`, `INDEPENDENT_RERUN`, `MULTI_OPERATOR` or `NOT_EXECUTED`. See [verification levels](#verification-levels) below. |
| `reproduction_level` | Exact reproduction level from `docs/CLAIMS.md` when applicable. |
| `ai_assistance` | Whether AI assisted with code, protocol drafting, summarization or validation. |
| `manual_review` | Whether a human operator reviewed source rights, protocol boundary and final claim. |
| `known_limitations` | Important limitations and reasons not to overclaim. |

## Forecast-Specific Fields

Forecast evidence cards must also include:

| Field | Purpose |
| --- | --- |
| `forecast_question` | Exact question fixed before resolution. |
| `answer_timestamp` | When the model or method answer was recorded. |
| `forecast_deadline` | Last time the forecast could be made. |
| `resolution_deadline` | When the outcome should be resolvable. |
| `model_or_method` | System, model or fixed signal used. |
| `prompt_hash` | Hash of the prompt or input template, when an LLM is used. |
| `resolution_rule` | Exact rule for deciding the outcome. |
| `allowed_resolution_sources` | Official sources accepted for resolution. |
| `scoring_rule` | Pre-selected scoring rule. |

## Execution Modes

Use one exact mode:

| Mode | Meaning |
| --- | --- |
| `MANUAL_NO_AI` | Human operator performed the reproducible manual track without AI assistance. |
| `AUTOMATED_AI_ASSISTED` | An AI coding agent executed or prepared the AI track, with deterministic validation producing the status. |

The execution mode is provenance metadata. It does not make a result more or
less valid by itself. A result is valid only when the protocol, source boundary,
hashes, status and claim boundary validate.

## Verification Levels

`verification_level` records verification strength. It is separate from
`record_type`:

| Level | Meaning |
| --- | --- |
| `SINGLE_OPERATOR` | One operator run; no same-operator rerun recorded on this card yet. |
| `SINGLE_OPERATOR_RERUN` | The same operator re-ran or re-checked the frozen gate and updated this card (`verification_count` ≥ 2). This is **not** independent external verification. |
| `INDEPENDENT_RERUN` | A different operator reproduced the frozen gate under the rerun workflow. |
| `MULTI_OPERATOR` | Multiple independent operators recorded on one card. |
| `NOT_EXECUTED` | Scaffold or request only. |

`record_type` tells you whether the JSON row is the primary outcome or a linked
rerun attempt:

| `record_type` | Typical `verification_level` | Example |
| --- | --- | --- |
| `evidence_result` | `SINGLE_OPERATOR` or `SINGLE_OPERATOR_RERUN` | NASA POWER D-103 baseline card after a maintainer re-verify |
| `reproduction_attempt` | `SINGLE_OPERATOR_RERUN` | NASA POWER D-103 maintainer rerun card dated 2026-06-15 |
| `source_audit` | `SINGLE_OPERATOR` or `SINGLE_OPERATOR_RERUN` | Grok prompts source audit with `verification_count` = 2 |

A baseline `evidence_result` card may therefore show `SINGLE_OPERATOR_RERUN` when
the maintainer re-ran the gate and refreshed `last_verified_date` on the original
card. That is different from a separate `reproduction_attempt` sibling card,
which links back to the baseline without replacing it.

External adoption signal requires `INDEPENDENT_RERUN` or `MULTI_OPERATOR` from an
operator who is not the maintainer.

## Visual Status Colors

Rendered SVG cards use separate chips for `result_status`, `reproduction_level`
and `card_validity_level`. Colors are reading aids only; the JSON fields remain
the source of truth.

| Chip | Color | Typical value |
| --- | --- | --- |
| Result status | Green | `PASSED_UNDER_PROTOCOL`, `REPRODUCED_OUTCOME` |
| Result status | Red | `NEGATIVE_RESULT_UNDER_PROTOCOL` |
| Result status | Amber | `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE` |
| Reproduction | Yellow | `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT` |
| Reproduction | Green | `REPRODUCED_OUTCOME` |
| Reproduction | Blue | `not independently reproduced` |
| Validity | Green | `GREEN_VALIDATED` |
| Validity | Yellow | `YELLOW_LIMITED_REPRODUCIBILITY` |
| Validity | Gray | Draft, request or scaffold only |

Do not move source-byte drift into `result_status`. Drift belongs in
`reproduction_level` while `result_status` records the gate outcome.

## Required Interpretation

The card must make the allowed claim and forbidden claims clear.

Allowed:

```text
This protocol-bound record has status X under source Y, period Z and gate G.
```

Forbidden:

```text
This proves broad model superiority.
This proves deployment readiness.
This proves the raw source bytes will never drift.
This proves correctness outside the protocol boundary.
```

## Example

Current committed examples:

- [Anthropic system-card source audit](evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.json)
  and [visual SVG](evidence_cards/CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08.svg)
- [NASA POWER D-103 passed evidence card](evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json)
  and [visual SVG](evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg)
- [NOAA CO-OPS D-131 negative evidence card](evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.json)
  and [visual SVG](evidence_cards/CLAIMBOUND-NOAA-COOPS-D131-2026-04-30.svg)

Render visual cards from validated JSON:

```bash
uv run --extra dev python scripts/claimbound_render_evidence_card_svg.py \
  docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.json \
  docs/evidence_cards/CLAIMBOUND-NASA-POWER-D103-2026-04-29.svg
```

```json
{
  "evidence_id": "CLAIMBOUND-NASA-POWER-D103-2026-04-29",
  "registry_sequence": 8,
  "record_type": "evidence_result",
  "protocol_id": "NASA_POWER_D103",
  "protocol_version": "1.0.143",
  "domain": "renewable-energy-resource",
  "claim_type": "signal",
  "execution_mode": "MANUAL_NO_AI",
  "result_status": "PASSED_UNDER_PROTOCOL",
  "claim_boundary": "NASA POWER D-103 passed the frozen gate for the documented points, period, target, candidate, controls and acceptance rule only.",
  "official_source_name": "NASA POWER Daily point API",
  "official_source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
  "access_date": "2026-04-29",
  "source_rights_note": "Official public source. Raw payloads are not committed.",
  "raw_payload_committed": false,
  "raw_payload_manifest": "external SHA-256 manifest recorded outside the repository",
  "sanitized_report_path": "artifacts/nasa_power_d103_real_run_summary.json",
  "sanitized_report_sha256": "fill with report SHA-256",
  "git_commit": "fill with commit SHA",
  "runner_command": "uv run python scripts/claimbound_run_nasa_power_prereg.py ...",
  "operator": "maintainer",
  "created_at": "2026-05-01",
  "last_verified_date": "2026-06-15",
  "verification_count": 3,
  "verification_level": "SINGLE_OPERATOR_RERUN",
  "reproduction_level": "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT",
  "ai_assistance": "not used for outcome selection or gate changes",
  "manual_review": "source boundary and claim boundary reviewed by maintainer",
  "known_limitations": [
    "No universal forecasting edge is claimed.",
    "No deployment readiness is claimed.",
    "No raw-byte reproduction is claimed."
  ]
}
```

## Validation Rules

Evidence cards should fail validation when:

- `record_type` is missing or outside the allowed record categories;
- `registry_sequence` is missing, duplicated in the registry or not positive;
- `execution_mode` is missing or outside the allowed modes;
- `result_status` is not one of the documented statuses;
- `claim_boundary` is missing;
- `raw_payload_committed` is `true`;
- a forecast card lacks a resolution rule;
- a positive record has no baseline or control summary;
- a blocked record does not explain the block reason;
- a reproduction record does not state the reproduction level;
- AI assistance is not disclosed;
- verification metadata is missing or uses an unknown level;
- the card contains broad claims outside the protocol boundary.

Run the local validator:

```bash
uv run python scripts/claimbound_validate_evidence_card.py path/to/evidence_card.json
uv run python scripts/claimbound_validate_registry.py
```

The validator is deterministic. It does not try to infer hidden AI use from
writing style. It requires explicit provenance fields and rejects incomplete or
overbroad records.

## Sharing And Registry

To share a result, link directly to its JSON evidence card in
`docs/evidence_cards/`. A visual card can be rendered from the same data with
`scripts/claimbound_render_evidence_card_svg.py`.

The public registry index is stored in `docs/registry/evidence_index.json`.
It is intended to remain freely readable and to expose aggregate counts by
status, domain and source. The registry stores card metadata and sanitized
report references, not raw payloads.
