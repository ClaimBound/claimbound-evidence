# Related Work And Independence

Status: public positioning note — not a novelty claim, legal opinion, or
affiliation statement.

ClaimBound Evidence is independent open-source work for narrow public evidence
cards. It is not affiliated with, a fork of, or derived from
[EviBound](https://arxiv.org/abs/2511.05524) ("Evidence-Bound Autonomous
Research", arXiv, Oct 2025). That paper was discovered after ClaimBound
development had started; similar naming is acknowledged explicitly.

## Scope Split

| Dimension | EviBound | ClaimBound Evidence |
| --- | --- | --- |
| Primary object | Autonomous research-agent execution framework. | Public evidence-card toolkit and registry. |
| Main problem | Agents reporting completed tasks without machine-checkable artifacts. | Public claims broader than their evidence. |
| Core mechanism | Dual approval and verification gates around execution. | Evidence cards with protocol, source boundary, status, hashes, claim boundary and reproduction level. |
| Verification substrate | MLflow run IDs, artifacts, metrics and FINISHED status. | Source audits, public-source boundaries, deterministic scripts, manual checklists, JSON/SVG cards and registry entries. |
| Result surface | Verified or blocked autonomous research tasks. | Passed, negative, blocked, insufficient, drift and reproduced evidence records. |
| Public examples | Eight benchmark tasks in the paper. | NASA POWER, NOAA CO-OPS, EEA/public-data, public AI documentation and software-development examples. |
| Intended reader | Teams building autonomous research agents. | Maintainers, reviewers, public-data operators and external rerun operators. |

## When To Reference Which Project

**EviBound** — dual-gate agent execution, MLflow-backed verification, and the
paper's hallucination benchmark.

**ClaimBound Evidence** — public evidence cards, source and claim boundaries,
negative/blocked/drift statuses, registries and R&D family discipline.

EviBound asks whether an agent finished with valid artifacts. ClaimBound asks
what exact public claim is supported, by which source and frozen protocol, with
which status, and where that claim stops.

Do not describe ClaimBound as EviBound-derived or as claiming priority over
EviBound's agent-execution framework.
