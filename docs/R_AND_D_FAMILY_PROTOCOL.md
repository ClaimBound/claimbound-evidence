# R&D Family Protocol

ClaimBound evidence cards are intentionally small: one narrow claim, one frozen
protocol, one exact status. Real research often needs a connected sequence of
tracks before a final evidence card is justified. This document defines how to
run that sequence without turning exploration into selective reporting.

The protocol applies to ML, source audits, public-data checks, benchmark
claims, forecasts, reproducibility work and any other ClaimBound workflow where
multiple tracks test related hypotheses.

## Core Rule

An R&D family must separate:

- source and schema claims;
- availability and causality claims;
- diagnostic screening claims;
- frozen proof claims;
- economics, deployment or operational claims;
- reproduction and closure claims.

A diagnostic track may discover candidates or blockers. It must not be cited as
a positive proof, deployment or production result.

## Definitions

| Term | Meaning |
| --- | --- |
| R&D family | A set of related tracks that share a parent claim, source family, label family, method family or decision objective. |
| Claim list | The machine-readable list of claims the family may test, each with evidence required, gate and forbidden inference. |
| Diagnostic track | A track that inventories sources, schemas, features, labels or candidate behavior without making a positive result claim. |
| Proof track | A track with a frozen candidate, frozen source, frozen label or target, baselines, controls and acceptance gate. |
| Closure track | A track that stops, supersedes or narrows a family after evidence says continuing the same branch would be misleading. |
| Non-overlap boundary | The reason a proposed next family is genuinely new rather than a cosmetic repeat of a failed branch. |

## Required Family Ledger

Every multi-track family should keep a JSON ledger under `docs/track_families/`.
New scaffolds create a draft ledger automatically.

Minimum fields:

```json
{
  "family_id": "EXAMPLE_D001_FAMILY",
  "family_status": "DRAFT",
  "parent_claim": "Write the narrow parent hypothesis before protocol freeze.",
  "non_overlap_boundary": "What makes this family new relative to prior work.",
  "claim_scope": {
    "allowed": ["what the family may claim"],
    "forbidden": ["what the family must not claim"]
  },
  "track_budget": {
    "max_proof_tracks_per_hypothesis": 3
  },
  "stop_rules": ["when to stop or close the family"],
  "claim_list": [],
  "tracks": []
}
```

Validate the ledger:

```bash
uv run claimbound validate-family docs/track_families/EXAMPLE_D001_FAMILY_LEDGER.json
```

Equivalent script entrypoint:

```bash
uv run python scripts/claimbound_validate_family_ledger.py \
  docs/track_families/EXAMPLE_D001_FAMILY_LEDGER.json
```

`uv run claimbound validate-all` also validates every optional
`docs/track_families/*_FAMILY_LEDGER.json` file. It does not require historical
evidence cards or old draft scaffolds to have ledgers.

## How To Write A Claim List

Each claim should be small enough that a single track can pass, fail, block or
supersede it.

Required claim fields:

| Field | Meaning |
| --- | --- |
| `claim_id` | Stable ID, for example `EXAMPLE_D001-C003`. |
| `claim_class` | One of `source`, `availability`, `causality`, `diagnostic`, `predictive`, `economic`, `deployment`, `reproduction` or `closure`. |
| `status` | One of `DRAFT`, `FROZEN`, `PASSED`, `NEGATIVE`, `BLOCKED`, `SUPERSEDED` or `STOPPED`. |
| `claim_text` | One narrow sentence. Avoid broad result language. |
| `evidence_required` | Exact artifacts needed before the claim can move out of draft. |
| `acceptance_gate` | The frozen gate for pass, negative or blocked status. |
| `forbidden_inference` | What readers must not infer even if the claim passes. |
| `depends_on` | Earlier claims required before this one can run. |
| `unlocks` | Later claims this one may unlock. |

Good claim:

```json
{
  "claim_id": "TS_SIGNAL_D001-C002",
  "claim_class": "causality",
  "status": "FROZEN",
  "claim_text": "Candidate fields are known before the target interval closes.",
  "evidence_required": [
    "timestamped input snapshot",
    "replay hash",
    "same-interval exclusion check"
  ],
  "acceptance_gate": "All fields used by later proof tracks are stable before target resolution.",
  "forbidden_inference": [
    "causal availability does not prove predictive value",
    "causal availability does not prove economic value"
  ],
  "depends_on": ["TS_SIGNAL_D001-C001"],
  "unlocks": ["TS_SIGNAL_D001-C003"]
}
```

Weak claim:

```text
The model works and is ready to use.
```

That sentence mixes predictive, economic, deployment and operational claims. It
cannot be fairly tested by one ClaimBound track.

## Recommended Family Order

Use this sequence unless the protocol has a documented reason to differ:

1. Source boundary: official source, rights, payload policy and access path.
2. Schema or inventory: fields, documents, endpoints, prompts, metadata or
   inputs that actually exist.
3. Availability and causality: when each field or input is known, whether it is
   stable under replay and whether it leaks the target.
4. Diagnostic screening: candidate discovery only, with no positive result
   claim.
5. Frozen proof: one pre-registered candidate, label or target family, controls
   and acceptance gate.
6. Economics or deployment, when relevant: cost, latency, safety, operations and
   failure modes are separate claims.
7. Reproduction or closure: independent rerun, stopped branch, superseded
   branch or allowed non-overlapping next work.

## Stop Rules

The family ledger must make stopping normal, not exceptional.

Use stop rules such as:

- stop when source access, rights, hashes or coverage are insufficient;
- stop when a proof branch reaches its budget of negative or blocked tracks;
- stop when gross signal strength is materially smaller than the cost,
  latency, risk or operational drag it must overcome;
- stop when the next proposed track repeats the same source, label, mechanics or
  gate with only cosmetic changes;
- stop when bookkeeping defects prevent a fair result and rerun only after the
  defect is fixed and disclosed.

The default budget for proof tracks is three per `hypothesis_family`. A lower
budget is better when costs are high or the hypothesis is narrow.

## Diagnostic Versus Proof

Diagnostic tracks may search, inventory and rank candidates. Their allowed
outputs are:

- candidate discovered;
- blocker discovered;
- source/schema/coverage map;
- causal availability table;
- recommendation to freeze a later proof track;
- recommendation to close or split the family.

Diagnostic tracks must not output:

- passed empirical result;
- deployment readiness;
- production readiness;
- economic viability;
- broad method superiority.

Proof tracks are rarer. A proof track must have:

- frozen source and source version;
- frozen candidate;
- frozen target or label family;
- frozen baselines and controls;
- frozen scoring rule;
- frozen pass, negative, blocked and insufficient rules;
- minimum sample or coverage gate;
- forbidden after-result changes.

## Closure

When a family stops, add a closure decision to the ledger:

```json
{
  "closure_decision": {
    "decision": "STOP_CURRENT_BRANCH",
    "reason": "Repeated proof tracks were negative under the same hypothesis family.",
    "allowed_next_work": [
      "new source family",
      "new label family",
      "diagnostic-only inventory"
    ],
    "blocked_next_work": [
      "same-entry repeat",
      "same gate with cosmetic parameter changes"
    ]
  }
}
```

Closure is not failure. It is how ClaimBound prevents a weak family from
becoming a long sequence of selective reruns.

## Preflight Checks

Before running a track in a family, check:

- family ledger validates;
- claim IDs are unique;
- the track references known claim IDs;
- diagnostic tracks are not named as proof tracks;
- proof track count has not exceeded the family budget;
- required paths, environment notes, report paths and hashes are present;
- draft evidence cards do not contain result statuses;
- forbidden broad claim language is absent or appears only as a limitation;
- the next track is allowed by the previous closure decision, if one exists.

These checks catch bookkeeping defects early, before they consume research time
or create ambiguous evidence.
