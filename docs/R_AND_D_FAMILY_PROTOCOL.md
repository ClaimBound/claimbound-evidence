# R&D Family Protocol v2

ClaimBound evidence cards are intentionally small: one narrow claim, one frozen
protocol, one exact status. Real research often needs a connected sequence of
tracks before a final evidence card is justified. This document defines how to
run that sequence without turning exploration into selective reporting.

The protocol applies to ML, source audits, public-data checks, benchmark
claims, forecasts, reproducibility work, software-development evidence tracks
and any other ClaimBound workflow where multiple tracks test related
hypotheses.

Status: v2 family-orchestration protocol. This document does not migrate
historical cards, change evidence-card schemas or create a new empirical
result.

The objective-order rule remains separate: objective-order documents say what
must be proven first; this protocol says how related families are scheduled,
stopped, tombstoned and summarized. For the difference between result cards,
v2 family/frontier ledgers and v3 tree overlays, see
[Protocol layers: v2 and v3](PROTOCOL_LAYERS_V2_V3.md).

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
| Family DAG | Directed acyclic graph of family contracts, tracks and dependencies. |
| Frontier | Machine-readable set of currently runnable tracks whose dependencies passed. |
| Tombstone | Immutable stop record for a failed, closed or poisoned branch. |
| Proof surface | Reusable claim-support tuple: source, selection, target, candidate, decision rule, target metric and gates. |
| Context capsule | Compact state summary read by later tracks before they inspect long reports. |

## Required Family Ledger

Every multi-track family should keep a JSON ledger under `docs/track_families/`.
New scaffolds create a draft ledger automatically.

Minimum fields:

```json
{
  "family_id": "EXAMPLE_D001_FAMILY",
  "protocol_version": "claimbound-rnd-family-v2",
  "family_status": "DRAFT",
  "family_type": "feature_signal_family",
  "parent_claim": "Write the narrow parent hypothesis before protocol freeze.",
  "non_overlap_boundary": "What makes this family new relative to prior work.",
  "proof_surface": {
    "source_surface": "official source or source family",
    "selection_surface": "split, cohort, prompt set or selection rule",
    "label_or_target_surface": "target, label or resolution rule",
    "candidate_or_method_surface": "candidate method, model or checklist",
    "decision_rule": "fixed pass, negative, blocked and insufficient rules",
    "target_metric": "primary metric or checklist gate",
    "acceptance_gates": ["gate fixed before scoring"]
  },
  "proof_surface_hash": "NOT_COMPUTED_UNTIL_FREEZE",
  "allowed_next_tracks": ["source_audit", "diagnostic", "proof_after_freeze", "closure"],
  "blocked_claim_flags": ["deployment_readiness", "correctness_outside_protocol"],
  "context_budget": {
    "max_context_lines": 80,
    "capsule_required": true
  },
  "claim_scope": {
    "allowed": ["what the family may claim"],
    "forbidden": ["what the family must not claim"]
  },
  "track_budget": {
    "max_proof_tracks_per_hypothesis": 3
  },
  "stop_rules": ["when to stop or close the family"],
  "claim_list": [],
  "tracks": [],
  "frontier": {
    "current_frontier": [],
    "consumed_tombstones": [],
    "tombstone_required_before_descendants": true
  }
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

Frontier ledgers are optional and additive:

```bash
uv run claimbound validate-frontier docs/track_families/EXAMPLE_D001_FRONTIER.json
uv run python scripts/claimbound_validate_family_frontier.py \
  docs/track_families/EXAMPLE_D001_FRONTIER.json
```

`validate-all` validates optional `docs/track_families/*_FRONTIER.json` files
when they exist. Existing cards and old drafts do not need frontier ledgers.

## Family Types

Future family ledgers must declare one general type:

| Family type | Use |
| --- | --- |
| `source_boundary_family` | Source, rights, lineage, access, coverage or causality checks. |
| `feature_signal_family` | Feature, signal, label, forecast or target diagnostics before proof. |
| `evaluation_family` | Frozen candidate, benchmark, scorer or checklist evaluation. |
| `reproduction_family` | Independent rerun or reproduction attempt. |
| `systems_performance_family` | Runtime, parity or acceleration work that does not change the claim. |
| `safety_policy_family` | Safety, governance, policy or compliance checks. |
| `product_decision_family` | User, product or operational decision validation under frozen gates. |
| `publication_audit_family` | Evidence digest, source audit or publication-readiness review. |

The family type does not make a result stronger. It only routes the family
through appropriate stop rules and closure expectations.

## Family DAG And Frontier

Protocol v2 treats related R&D as a DAG:

```text
family contract
  -> source and causality
  -> cheap diagnostic
  -> frozen proof
  -> robustness or reproduction
  -> closure
```

The graph must be acyclic. A stopped or tombstoned family may be cited only as
negative evidence, baseline context or excluded design space. It must not be
reused as a fresh success proof.

A frontier ledger records only currently relevant state:

```json
{
  "protocol_version": "claimbound-rnd-family-v2",
  "families": [
    {
      "family_id": "EXAMPLE_D001_FAMILY",
      "family_type": "feature_signal_family",
      "status": "alive",
      "current_frontier": ["EXAMPLE_D001-T002"],
      "blocked_claim_flags": ["deployment_readiness"],
      "consumed_tombstones": ["STOP_OLD_BRANCH"],
      "proof_surface_hashes": ["NOT_COMPUTED_UNTIL_FREEZE"]
    }
  ],
  "tombstones": [
    {
      "family_id": "OLD_BRANCH",
      "decision": "STOP_OLD_BRANCH",
      "poisoned_proof_surface_hashes": ["0000000000000000000000000000000000000000000000000000000000000000"],
      "blocked_future_work": ["reuse_old_surface_as_success"],
      "non_overlap_requirements": ["new source, target, method or decision surface"]
    }
  ]
}
```

The frontier is not evidence by itself. It is a compact scheduler and audit
index for future tracks.

## Proof Surface Hash

Every frozen proof track should compute a deterministic `proof_surface_hash`
over the fields that make a result reusable:

- source surface;
- selection surface;
- label, target or resolution surface;
- candidate or method surface;
- decision rule;
- target metric;
- acceptance gates.

If a family fails robustness or closes as negative, the hash becomes poisoned
for future success claims. A later family may cite it only as negative evidence,
baseline context, excluded design space or meta-audit input.

## Tombstones

When a family stops, the closure decision should produce a tombstone. Minimum
tombstone fields:

- `family_id`;
- `decision`;
- `reason`;
- `poisoned_proof_surface_hashes`;
- `allowed_future_work`;
- `blocked_future_work`;
- `non_overlap_requirements`.

Tombstones are append-only. Editing a tombstone to rescue a stopped branch is a
protocol violation.

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

Every family must close. A positive aggregate result can still close with a
limited boundary or become tombstoned if robustness, reproduction, source or
policy gates fail.

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

## Bounded Context

Every active family should keep a compact context capsule:

- contract summary;
- current frontier status;
- pass, fail and blocked gates;
- source-artifact hashes;
- tombstones consumed;
- allowed next tracks;
- blocked reuse keys;
- one-paragraph interpretation.

Later tracks should read the capsule first and inspect full evidence cards only
when auditing a claim. This reduces context use without weakening the evidence
trail.

## Parallel Scheduling

Independent families may run in parallel only when all are true:

- no shared writable artifact path;
- no shared holdout, pilot, source-selection or scoring surface;
- no ancestor or descendant dependency between tracks;
- no unresolved tombstone required by either family;
- each family has a frozen contract.

Allowed parallelism:

- contract-only family seeds;
- source validation across independent sources or audiences;
- candidate evaluation inside one frozen track;
- row-level label or target computation;
- metric aggregation over independent blocks;
- report verification after artifacts are immutable.

Blocked parallelism:

- two tracks writing the same family ledger;
- proof before candidate, target and gate are frozen;
- closure before robustness or reproduction finishes;
- descendants of a family with a pending kill gate;
- threshold, model, prompt or report-text search over holdout outcomes.

Schedulers should prefer cheap contract, source and diagnostic jobs over
expensive proof chains while branches remain unproven.

## Acceleration And Parity

Hardware acceleration is a systems-performance optimization, not a claim.
Accelerated kernels may be used only behind a deterministic runner boundary.
Evidence cards consume frozen artifacts; they do not depend on whether those
artifacts were produced by CPU, GPU or another backend.

A `systems_performance_family` must prove parity before accelerated output is
trusted:

- CPU reference output exists;
- accelerated output matches within a frozen tolerance;
- random seeds, precision, batch order and reduction order are declared;
- a sample parity digest is stored before accelerated output is trusted;
- parity failure tombstones only the acceleration branch, not the scientific or
  source family.

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
