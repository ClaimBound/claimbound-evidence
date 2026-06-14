# Related Work And Independence

Status: public positioning note. This page is not a novelty claim, legal
opinion, affiliation statement or empirical result record.

ClaimBound Evidence is an independent open-source evidence-card toolkit for
narrow public AI, ML, data and software-development claims. It is not affiliated
with EviBound and is not a continuation, fork or implementation of the EviBound
paper, code, artifacts, repository or research package.

The maintainer acknowledges EviBound, "Evidence-Bound Autonomous Research
(EviBound): A Governance Framework for Eliminating False Claims"
([arXiv:2511.05524](https://arxiv.org/abs/2511.05524)), submitted on
2025-10-28, as related prior art discovered after ClaimBound development work
was already underway. The similar naming and shared concern with evidence-bound
claims are acknowledged explicitly rather than hidden.

This page separates the projects by scope. It does not claim that ClaimBound
invented every evidence-bound governance idea first, and it does not claim that
EviBound is related to or derived from ClaimBound.

## Scope Split

| Dimension | EviBound | ClaimBound Evidence |
| --- | --- | --- |
| Primary object | Autonomous research-agent execution framework. | Public evidence-card toolkit and registry. |
| Main problem | Autonomous agents reporting completed research tasks without machine-checkable artifacts. | Public AI, ML, data, reproducibility and software-development claims being broader than their evidence. |
| Core mechanism | Dual approval and verification gates around execution. | Evidence cards with protocol, source boundary, status, hashes, claim boundary and reproduction level. |
| Verification substrate | MLflow-backed run IDs, artifacts, metrics and finished execution status. | Source audits, public-source boundaries, deterministic scripts, manual checklists, sanitized reports, JSON/SVG cards and registry entries. |
| Result surface | Verified or blocked autonomous research tasks. | Passed, negative, blocked, insufficient, drift and reproduced evidence records. |
| Public examples | Eight benchmark tasks reported in the paper. | NASA POWER, NOAA CO-OPS, EEA/public-data, public AI documentation, Grok prompt source audit and software-development validator examples. |
| R&D structure | Research-agent task execution and retry governance. | R&D family/frontier ledgers, proof surfaces, stop rules, tombstones and optional tree overlays. |
| Intended reader | Researchers building or evaluating autonomous research agents. | Maintainers, reviewers, public-data operators, AI transparency readers, software developers and external rerun operators. |

## Where EviBound Is Stronger

EviBound has a published arXiv paper with a focused experimental evaluation for
autonomous research-agent execution. Its strongest contribution is the specific
dual-gate architecture: acceptance criteria are checked before execution, and
artifacts are verified after execution through a machine-checkable backend such
as MLflow.

For teams whose main problem is an autonomous research agent claiming task
completion without valid MLflow artifacts, EviBound is the more direct reference
architecture.

## Where ClaimBound Evidence Is Stronger Or Different

ClaimBound Evidence is stronger in a different operational scope: public
claim-boundary records rather than one autonomous execution pipeline.

Its public surface includes:

- evidence-card JSON and rendered SVG records;
- a registry of validated cards;
- public-source and rights-boundary documentation;
- first-class negative, blocked, insufficient, drift and reproduced outcomes;
- NASA POWER, NOAA CO-OPS, EEA, public AI documentation and software-development
  examples;
- R&D family/frontier ledgers for related tracks, proof surfaces, stop rules and
  tombstones;
- optional tree overlays for public maps of stable claims, flow claims and
  stopped branches;
- software-development and AI-assisted workflow guidance that does not replace
  tests, CI, code review, security review or human judgment.

This makes ClaimBound Evidence useful when the problem is not only "did an
agent complete a run?", but "what exact public claim is supported, by which
source, under which frozen protocol, with which status, and where does that
claim stop?"

## Origin And Boundary Statement

ClaimBound Evidence arose from a practical R&D need: prevent narrow technical
checks, public-source audits, software-development results and multi-track
research attempts from being upgraded into broader claims than the evidence
supports.

That origin is reflected in the repository's current artifacts: public evidence
cards, source-audit protocols, NASA and NOAA examples, European public-data
examples, software-development evidence, blocked-source records, R&D family
ledgers and tombstone-oriented closure discipline.

The public repository should therefore be read as a distinct open-source
implementation for evidence cards and claim boundaries. It should not be
described as EviBound-derived work, EviBound continuation work, or an attempt to
claim priority over EviBound's autonomous-research execution framework.

## Practical Citation Guidance

When discussing related work, cite both projects narrowly:

- Cite EviBound for evidence-bound autonomous research execution gates,
  MLflow-backed verification and the reported dual-gate benchmark results.
- Cite ClaimBound Evidence for public evidence-card records, claim boundaries,
  source-boundary audits, negative/blocked/drift statuses, registries and R&D
  family discipline.

Do not use either project to make broad claims that are outside its documented
scope.
