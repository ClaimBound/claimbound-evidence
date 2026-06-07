# Protocol Use By Layer And Audience

Status: practical guidance. This page does not create an empirical result, change the evidence-card schema, or make protocol v2/v3 mandatory for every card.

ClaimBound should be used as the thinnest honest evidence layer that fits the risk. The evidence card is the result. Protocol v2 and protocol v3 are planning and visibility layers around the result.

```text
minimal result proof      -> evidence card
related R&D discipline    -> protocol v2 family/frontier ledger
public status map         -> protocol v3 tree overlay
public registry/reporting -> registry entry, report and README links
```

## Core Rule

Use the smallest layer stack that prevents overclaiming.

- Use an evidence card when there is one narrow completed claim.
- Add protocol v2 when related tracks, diagnostics, proof budgets, stop rules or closure decisions matter.
- Add protocol v3 when readers need a compact map of iron claims, flow claims, tombstones and blocked branches.
- Do not add v2 or v3 just to make a weak result look stronger.

## Layer Map

| Layer | Artifact | Main question answered | Best used when | Must not be used to claim |
| --- | --- | --- | --- | --- |
| Request/scaffold layer | request, charter, playbook, checklist, draft card | What are we preparing to check? | A claim is still being narrowed. | That evidence exists. |
| Evidence-card layer | validated JSON/SVG card and sanitized report | What happened under the frozen protocol? | A completed source audit, reproduction, regression, parity, benchmark, AI-control or checklist run has one exact status. | Whole-project correctness, certification, runtime safety, deployment readiness or broad model superiority. |
| Protocol v2 family/frontier layer | `*_FAMILY_LEDGER.json`, optional `*_FRONTIER.json` | How do related tracks stay fair? | There are multiple related attempts, diagnostics, proof surfaces, budgets, dependencies or closure decisions. | That a diagnostic or exploratory result is proof. |
| Protocol v3 tree overlay | `*_TREE.json` with `claimbound-tree-v3` | What is alive, stopped, proof-ready or blocked? | Public readers need a compact status map across one or many tracks. | That a flow claim, dependency or tombstone is a positive result. |
| Registry/reporting layer | registry entry, README link, changelog, release note | Where can the public find the validated record? | A card is validated and ready to be discovered. | That unvalidated drafts are evidence. |

## Choosing The Right Stack

| Work shape | Recommended stack | Reason |
| --- | --- | --- |
| One simple source audit | Evidence card only; optional one-node v2/v3 if a scaffold already exists. | The result is narrow and does not need a large planning map. |
| One risky software regression or parity check | Evidence card plus a small v2 family ledger. Optional one-node v3 if the PR needs a public status map. | Commands, fixtures, tolerance, stop rules and forbidden inference should be frozen. |
| AI-agent, security, robotics or vehicle-software control claim | Evidence card plus v2 when there are scenarios, tool permissions, safety envelopes, scan gates, release gates or approval dependencies. Add v3 when readers need a public risk/status map. | Turns broad rules like “do not harm” or “do not leak secrets” into bounded source, scenario, command, log, gate and limitation records. |
| Multi-track ML or data R&D | Evidence cards for completed leaves plus v2 family/frontier ledgers. Add v3 when public status is hard to read. | Prevents selective reruns and diagnostic/proof confusion. |
| AI or LLM evaluation with prompts/transcripts | Evidence card plus v2 when prompt sets, scoring, transcript hashes and model metadata are staged across tracks. Add v3 for public dependency maps. | Keeps source, prompt, model, scorer and transcript boundaries separate. |
| Public procurement or award review | Validated card plus registry/reporting links; v2 when several related promises or milestones must be tracked. v3 when the reviewer needs a map. | Reviewers need status and limitations, not narrative success language. |
| Closed or failed research branch | v2 tombstone and, when public visibility helps, v3 tombstone surfaced in the tree. | Stopped work must stay citable as boundary evidence without being recycled as success. |

## Audience Matrix

| Audience | Main risk | How to use v2 | How to use v3 | Finished card should say | Avoid |
| --- | --- | --- | --- | --- | --- |
| Public AI transparency readers | Confusing public documentation access with model behavior. | Usually light or optional; useful when several source pages, model-card families or runtime-equivalence requests are chained. | Useful as a public map of source-audit claims versus later runtime claims. | The official source boundary was or was not reachable, dated, hashed and limited. | Claims that a source audit proves model safety or runtime behavior. |
| AI and LLM evaluation teams | Missing prompt, model, scorer, transcript or run metadata. | Freeze prompt sets, model IDs, settings, scoring rules, transcript hashes, proof budgets and stop rules. | Show iron proof claims, flow dependencies such as access/model availability, and tombstones for blocked benchmark branches. | The exact model/eval claim passed, failed, blocked or reproduced under the frozen gate. | Leaderboard-style broad superiority claims. |
| AI risk, security and automation-control teams | Treating moral slogans, model policies or agent instructions as enforceable proof. | Freeze tool permissions, model identity, scenarios, commands, safety/security gates, approval points, stop rules, logs and forbidden inferences. | Map iron control claims, flow dependencies, blocked safety/security branches and tombstoned unsafe paths. | One narrow AI-control, security-scan, prompt-injection, robot-scenario or release-gate claim passed, failed or blocked. | Claiming complete safety, hacker-proofing, certification, production readiness or physical runtime control. |
| Software developers and maintainers | Saying a change works without a bounded command path or fixture set. | Freeze risky PR claims, AI-assisted patches, local API checks, compatibility, parity, regression budgets, commands, fixtures, tolerances and closure rules. | Show stable behavior claims, flow dependencies, stopped branches or proof-ready nodes. | One narrow build, API, parity, compatibility or regression claim passed, failed or blocked. | Replacing tests, CI, code review, release engineering or maintainer judgment. |
| Companies with AI products | Turning marketing language into unsupported evidence. | Split product claims into source, model, prompt, scorer, user-impact, safety and deployment families. | Show which claims are evidence-backed and which remain flow/dependency claims. | One narrow customer-readable claim has source, protocol, status and limitations. | Certification or deployment-readiness language unless separately proven. |
| Independent verifiers, procurement teams and public buyers | Adopting a system from broad vendor claims. | Require source, scoring, model metadata, artifacts and reproduction or challenge paths before adoption decisions. | Map vendor claims, blocked requirements and tombstoned branches. | What was independently checkable, what happened, and what remains unsupported. | Treating blocked source as a pass. |
| Data stewards and public-data teams | Using data before source rights, coverage, lineage or payload policy are clear. | Order source audit, schema, coverage, rights, causality and later result tracks. | Map many datasets, endpoints or regions when active or blocked. | The source boundary, rights note, coverage and raw-payload policy were checked under protocol. | Publishing raw payloads or rights claims that are not allowed. |
| Civic tech, journalism and watchdogs | Overstating causal or political conclusions from limited public data. | Separate source access, metric definition, resolution rule, analysis and publication boundaries. | Show which branches are source-only, diagnostic-only, proof-ready or stopped. | One public-service, mobility, climate or infrastructure claim was checked with exact status and limitation. | Broad causal claims not frozen before scoring. |
| Open science and reproducibility teams | Hiding negative, drifted or partial reproduction results. | Freeze reproduction protocol, allowed deviations, source/code versions, controls and closure rules. | Expose reproduced, drifted, negative and tombstoned branches. | The result reproduced, failed, blocked or reproduced with drift under stated limits. | Rewriting negative reproduction as success. |
| ML researchers | Mixing diagnostics, method exploration and proof. | Separate source, feature/signal inventory, diagnostic screening, frozen proof, controls, baselines, robustness and closure. | Map proof-ready claims and stopped paths. | The narrow method or benchmark claim status under one fixed protocol. | Broad model superiority or deployment value from one track. |
| Educators | Students learning only final scores instead of evidence discipline. | Teach claim lists, gates, forbidden inference and stop rules lightly. | Use only when it helps students see claim kinds and blocked branches. | A classroom run produced a clear status and limitation. | Overbuilding protocol machinery for a tiny exercise. |
| Program reviewers and evaluators | Narrative milestone reports without source/status/limitation trace. | Track promised milestones, proof surfaces, stop rules, negative outcomes and closure. | Give reviewers a compact project map across claims, dependencies, tombstones and validated cards. | Which milestone claim was checked, what source was used, what happened and what cannot be claimed. | Treating a demo, scaffold or future plan as evidence. |

## AI Risk-Control Examples

Use ClaimBound to make AI-control claims small enough to review. Do not use it to claim that an AI, robot, vehicle or software system is generally safe.

Good examples:

- a prompt-injection fixture set verifies that an AI agent made no unauthorized tool calls under a frozen allowlist;
- an AI-generated patch passes a fixed security-scan command and protected-path check before merge;
- a robot scenario fixture verifies one speed, force or keep-out-zone envelope under a logged simulator or hardware-in-loop run;
- a driver-assistance-style claim verifies that one scenario logged a takeover, disable or warning event with required fields;
- a release gate blocks deployment because the required evidence card is negative, blocked or insufficient.

Bad examples:

- “the robot is safe”;
- “the car can drive itself safely”;
- “the AI cannot be hacked”;
- “the agent obeys policy” without a frozen tool, command, scenario, prompt and validator boundary;
- using a card instead of safety engineering, cybersecurity controls, access control, sandboxing, runtime monitoring, emergency stop, code review or release approval.

See [AI risk control with ClaimBound](AI_RISK_CONTROL_WITH_CLAIMBOUND.md) for the full guidance.

## Software Development Examples

Use ClaimBound only for changes where an evidence trail is worth the overhead.

Good examples:

- a local API server promises one response schema or deterministic output for a frozen request fixture;
- a library claims backward compatibility for a documented input/output fixture set;
- an AI-assisted patch changes behavior and reviewers need a fixed command path plus sanitized log hashes;
- an acceleration branch claims parity with a CPU reference within a frozen tolerance;
- a regression-sensitive public PR claims that one previously failing scenario now passes under fixed commands.

Bad examples:

- formatting, comments, typos or README-only edits;
- vague claims such as “the project is fixed” or “the feature works”;
- private logs or source payloads that cannot be summarized or hashed safely;
- deployment, security or correctness claims that were not separately frozen and tested;
- using a card as a substitute for tests, CI, review, release engineering or maintainer approval.

## Practical Workflow

```text
1. Narrow the claim.
2. Decide the smallest stack: card only, card + v2, or card + v2 + v3.
3. Freeze source, command path, fixture/prompt/data boundary, gate and forbidden inference.
4. Run the manual checklist or deterministic runner.
5. Keep bulky or sensitive raw artifacts local.
6. Publish sanitized report, hashes and exact status.
7. Validate card, registry, optional v2 ledgers and optional v3 tree overlays.
8. Link only validated cards from README-facing docs.
```

## Common Mistakes

- Creating v3 before the reader has a real status-map problem.
- Calling a `flow_claim` proof.
- Treating a v2 diagnostic track as a positive result.
- Adding a new proof track after failure without tombstoning or non-overlap reasoning.
- Publishing a draft card as evidence.
- Saying a software card proves project correctness or deployment readiness.
- Saying an AI-control card proves general safety, hacker-proofing, certification or runtime enforcement.
- Hiding negative, blocked or insufficient results.

## Quick Commands

```bash
uv run claimbound validate-family docs/track_families/EXAMPLE_D001_FAMILY_LEDGER.json
uv run claimbound validate-frontier docs/track_families/EXAMPLE_D001_FRONTIER.json
uv run claimbound validate-tree docs/track_families/EXAMPLE_D001_TREE.json
uv run claimbound validate-all
```

## Reader Path

1. Read the evidence card first.
2. Read the sanitized report if the card status matters to a decision.
3. Read the v2 family/frontier ledger when you need the planning, proof surface, stop rules or closure record.
4. Read the v3 tree overlay when you need the public status map.
5. Treat every card as bounded to its written claim, source, protocol, status and reproduction level.
