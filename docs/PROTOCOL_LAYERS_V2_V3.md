# ClaimBound Protocol Layers: v2 And v3

Status: explanatory documentation. This page does not create a new empirical result, migrate historical cards or change the evidence-card schema.

ClaimBound currently separates result evidence from R&D planning metadata. The practical rule is simple:

```text
evidence card = one completed result
protocol v2 = family/frontier planning and closure discipline
protocol v3 = optional tree overlay for public status maps
```

For a practical decision matrix by layer, work shape and audience, see
[Protocol use by layer and audience](PROTOCOL_USE_BY_LAYER_AND_AUDIENCE.md).

## Why There Are Multiple Layers

A single evidence card is intentionally small: it records one narrow claim, one source boundary, one frozen protocol, one status and one reproduction level. Real R&D often needs more than one track before a card is justified. Protocol v2 and v3 exist to manage that surrounding work without making the final card broader than it is.

Neither v2 nor v3 makes an evidence result stronger by itself. They are anti-overclaim layers: they show what was planned, what was blocked, what was stopped, which claims are proof-ready, and which claims are only diagnostic or routing metadata.

## Layer Summary

| Layer | Main object | Protocol string | What it is for | What it must not do |
| --- | --- | --- | --- | --- |
| Evidence-card protocol | Evidence card JSON/SVG | Evidence-card schema/version fields | Publish one completed result with status, boundary, hashes and reproduction level. | Replace a protocol run, broaden a claim, or certify a whole project. |
| R&D family/frontier v2 | `*_FAMILY_LEDGER.json`, optional `*_FRONTIER.json` | `claimbound-rnd-family-v2` | Coordinate related tracks, claim lists, proof surfaces, budgets, stop rules, frontier state and tombstones. | Turn diagnostics into proof or rescue a failed branch by rerunning cosmetically similar tracks. |
| Tree overlay v3 | `*_TREE.json` | `claimbound-tree-v3` | Show a compact public tree of iron claims, flow claims, track nodes, tombstones, badge counts and branch-block rules. | Reinterpret old cards, remove tombstones, or claim deployment/correctness outside the frozen boundary. |

## Protocol v2 In Plain Language

Protocol v2 is the family-orchestration layer. It is useful when a project needs a sequence such as:

```text
source boundary
  -> schema or inventory
  -> availability and causality
  -> diagnostic screening
  -> frozen proof
  -> reproduction or closure
```

Its main job is to prevent selective reporting. It requires the family to separate source claims, diagnostic claims, proof claims, deployment/economic claims, reproduction claims and closure decisions. A diagnostic track may discover a candidate or blocker, but it cannot be cited as a positive proof result.

Important v2 concepts:

- `claimbound-rnd-family-v2`: the protocol string used by family and frontier ledgers.
- Family ledger: the durable contract for related tracks.
- Claim list: the narrow claims that may be tested.
- Proof surface: the source, selection, target, candidate, decision rule, metric and gates that make a result reusable.
- Proof-surface hash: the deterministic hash of the frozen proof surface.
- Frontier: the set of currently runnable tracks.
- Tombstone: an append-only stop record for a failed, closed, superseded or poisoned branch.
- Context capsule: a short summary later tracks should read before inspecting long reports.

Use v2 when the main risk is R&D drift: too many related attempts, unclear stop rules, diagnostics being mistaken for proof, or a need to show why a branch was stopped.

## Protocol v3 In Plain Language

Protocol v3 is the tree overlay. It sits above the evidence-card layer and above v2 family/frontier ledgers. It can describe a one-track project with one node or a larger project with many related branches.

Its main job is visibility. A reader can quickly see which claims are stable proof claims, which are volatile routing claims, which branches are runnable, and which branches are blocked by tombstones.

Important v3 concepts:

- `claimbound-tree-v3`: the protocol string required by v3 overlays.
- `iron_claim`: a narrow bounded claim intended to support stable evidence.
- `flow_claim`: a volatile routing, dependency, availability or scheduling claim; useful, but not proof by itself.
- `tombstone`: an append-only stop record surfaced directly in the tree.
- `track_nodes`: the tracks that consume claim nodes and dependencies.
- Badge counts: machine-readable counts of iron claims, flow claims and tombstones.
- Branch-block rules: rules that prevent stopped or poisoned work from being reused as success evidence.

Use v3 when the project needs a public map: a compact view of what is alive, stopped, proof-ready, diagnostic-only, or blocked.

## Key Difference Between v2 And v3

| Question | v2 answer | v3 answer |
| --- | --- | --- |
| What is the main purpose? | Run related R&D fairly. | Show related R&D state clearly. |
| What does it organize? | Family contract, claim list, proof surface, budgets, frontier and closure. | Tree nodes, iron/flow/tombstone split, track dependencies and branch blocks. |
| Is it required for every card? | No. It is recommended for multi-track families and useful for one-track scaffolds when planning discipline matters. | No. It is optional and additive. |
| Does it change old evidence cards? | No. | No. |
| Does it create a result? | No. It schedules and constrains future or related tracks. | No. It maps planning/status metadata. |
| What failure does it prevent? | Selective reruns, diagnostic/proof confusion and missing closure. | Reader confusion about active, stopped, reusable and volatile branches. |
| What is the safest small use? | One family ledger with one claim list and stop rule. | One tree with one `iron_claim` node and zero tombstones. |

## How They Work Together

For a small one-track source audit, the project can publish only an evidence card. If the track has a clear planning context, it may also keep a v2 family ledger and a one-node v3 tree overlay.

For a larger R&D program, the usual stack is:

```text
v2 family ledger defines the claim list, proof surface, budget and stop rules
v2 frontier records what is runnable or stopped
v3 tree overlay exposes the current public status map
evidence cards record completed leaf results
```

The evidence card remains the result. v2 and v3 remain the guardrails around the result.

## Software-Development Interpretation

For software developers, v2 and v3 should stay thin:

- v2 can define a risky change family, frozen commands, fixtures, parity gates, regression budgets and closure rules.
- v3 can show which claims are stable behavior claims, which are flow/dependency claims, and which branches are stopped.
- Neither layer replaces tests, CI, code review, release engineering or maintainer judgment.

A green card for a software track means only that one narrow software claim passed under one written protocol. It does not prove the whole project is correct, secure, complete or deployment-ready.

## Validation Commands

Validate a v2 family ledger:

```bash
uv run claimbound validate-family docs/track_families/EXAMPLE_D001_FAMILY_LEDGER.json
```

Validate a v2 frontier ledger:

```bash
uv run claimbound validate-frontier docs/track_families/EXAMPLE_D001_FRONTIER.json
```

Validate a v3 tree overlay:

```bash
uv run claimbound validate-tree docs/track_families/EXAMPLE_D001_TREE.json
```

Validate evidence cards, registry, optional v2 ledgers and optional v3 overlays together:

```bash
uv run claimbound validate-all
```

## Recommended Reader Path

1. Read the evidence card first to see the actual result.
2. Read the v2 family ledger when you need to understand planning, budgets, proof surfaces or closure.
3. Read the v3 tree overlay when you need a compact status map across one or many tracks.
4. Treat diagnostics, flow claims and tombstones as boundary information, not proof of success.
