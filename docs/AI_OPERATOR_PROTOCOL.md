# AI Operator Protocol

AI tools may assist ClaimBound work only when they make the evidence trail more
auditable. They must never decide the result after seeing the outcome.

For the compact control-layer rulebook behind this protocol, see
[12 AI Life Rules](TWELVE_AI_LIFE_CONTROLS.md). The rules explain how AI-assisted claims
and actions should be bounded, sourced, frozen, blocked, reviewed and
tombstoned.

## Allowed AI Assistance

AI tools may help with:

- drafting protocol text before source data is inspected;
- checking whether a protocol has missing fields;
- drafting a family ledger with claim IDs, proof surface, track modes, budgets,
  tombstone requirements and stop rules;
- writing parsers and tests;
- generating validation code;
- summarizing already computed machine-readable reports;
- checking consistency between evidence cards and result-status rules;
- suggesting clearer claim-boundary language;
- finding broken links or missing citations;
- preparing reproduction instructions.

## Required AI Constraints

When AI assistance is used, the operator must ensure:

- the protocol is frozen before outcome inspection;
- related-track family and frontier ledgers are validated before they are cited;
- data selection rules are deterministic or manually recorded before scoring;
- thresholds are not tuned after seeing results;
- every automated run writes logs and hashes;
- every output status comes from code or a manual checklist, not from model
  opinion;
- any AI-written text is reviewed against the evidence card and claim boundary;
- failures, blocked sources and insufficient coverage remain publishable.

## Prohibited AI Actions

AI tools must not:

- choose favorable data after seeing outcomes;
- replace a failed run with a different subset;
- change acceptance gates after seeing the result;
- alter raw payloads;
- fabricate hashes, citations, commands or source-rights notes;
- infer a positive status from narrative text;
- hide deviations;
- convert a blocked or negative result into a positive claim;
- create unsupported deployment, superiority or broad forecasting claims;
- approve its own evidence card without deterministic validation or human
  review.

## Automated Mode

Automated operation must use a staged workflow:

1. Freeze protocol.
2. Validate the family and frontier ledgers when related tracks are involved.
3. Record source boundary.
4. Fetch or reference raw payloads outside the repository.
5. Hash raw payloads or record why this is blocked.
6. Run parser and runner.
7. Produce a sanitized report.
8. Validate status, claim boundary and evidence-card fields.
9. Publish the exact status.

The automated system must stop and record a blocked or invalid state when:

- source rights are unclear;
- raw payload hashing fails;
- required fields are missing;
- a proof track exceeds the family budget;
- the protocol was changed after outcome inspection;
- negative controls invalidate the candidate;
- the evidence card contains a broad unsupported claim.

## AI Disclosure

Every completed public record should state whether AI assistance was used for:

- protocol drafting;
- code generation;
- source review support;
- report summarization;
- evidence-card drafting.

Disclosure is not a substitute for validation. AI assistance is allowed only
when the final evidence record remains inspectable without trusting the AI tool.

## Evidence Card Provenance

Every evidence card must include `execution_mode`.

Allowed values are:

- `MANUAL_NO_AI`;
- `AUTOMATED_AI_ASSISTED`.

Use `MANUAL_NO_AI` for the reproducible manual track. Use
`AUTOMATED_AI_ASSISTED` only when an AI coding agent executes or prepares the
track under this protocol and deterministic validation produces the public
status. If a required source-access step cannot be completed by the AI agent,
stop with a blocker or switch to the manual track instead of creating a third
execution mode.

This is a self-declared provenance field, but it is not trusted alone. The
project relies on deterministic validation, frozen protocols, hashes, command
logs, manual review and independent reruns to make manipulation visible.
