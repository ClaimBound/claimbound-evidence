# Public Roadmap 2026

This roadmap describes the open-source ClaimBound foreground. It does not
include private systems and does not change any private or already-submitted
materials.

## Position

ClaimBound is an open-source evidence-card toolkit for narrow public AI, ML,
data and software claims. It should remain independently usable from this
repository.

It is not a model leaderboard, certification authority, hosted review queue or
raw-data archive.

## Public Work Plan

This plan describes the current public implementation path: harden an existing
prototype into reusable evidence-card infrastructure.

| Phase | Work package | Deliverables | Acceptance |
| ---: | --- | --- | --- |
| 1 | Public baseline consolidation | Release checklist, link/metadata audits, status wording, card/report/protocol consistency checks | `validate-all` passes; artifact-only records are not presented as completed cards. |
| 2 | SourceProbe v1 | Source URL metadata, final URL, content type, byte size, SHA-256, marker checks and source-boundary recommendations | Probe supports public AI documentation and public-data source audits; probe output is not a positive result by itself. |
| 3 | Scaffold workflow hardening | Request, protocol charter, playbook, checklist, operator declaration, draft card and registry-patch scaffolds | One command can prepare a safe scaffold; drafts stay clearly gray/not evidence. |
| 4 | Manual and AI-assisted workflows | Local run roots, deviation logs, source-rights checklist, raw payload/transcript policy and AI stop rules | Operators can follow manual or AI-assisted paths without hidden steps; final status remains human-reviewed and validator-checked. |
| 5 | Public AI claim protocol | Source-audit rules for public AI docs, model/API metadata fields, prompt/transcript hash policy and screenshot-only limits | Source-audit cards do not imply model safety, runtime behavior or benchmark superiority. |
| 6 | Static registry MVP | Generated read-only registry views, filters by status/source/domain/audience/reproduction and SVG links | Registry remains inspectable without hosted accounts or a database; entries validate against card JSON. |
| 7 | Independent rerun workflow | Reproduction request template, rerun checklist, reproduction status fields and source-byte drift handling | Reruns can update evidence without changing the original claim. |
| 8 | Completed example set and tutorials | Honest cards or scaffolds across public AI, public data, reproducibility and software examples | Project credibility does not depend on only positive results. |
| 9 | Release, review and sustainability | Tagged release, maintainer guide, dependency/security notes, AI-use disclosure summary and follow-on roadmap | The repository remains independently usable after this work. |

## Work Boundary

The public work package should produce reusable open-source outputs:

- validators and test coverage;
- source-boundary tooling;
- static registry generation;
- manual and AI-assisted runbooks;
- documented rerun paths;
- examples, tutorials and release process.

It should not produce:

- closed private systems;
- private data or private transcripts;
- hosted account systems;
- authenticated write APIs;
- commercial hosting;
- legal certification services;
- broad product or private performance claims.

This boundary keeps the work small enough for a single-maintainer open-source
project and clear enough for external review.

## Strong Public Examples To Keep Visible

| Example class | Current example | Why it matters |
| --- | --- | --- |
| Public AI source audit | Anthropic, OpenAI, Google DeepMind and Grok source-audit cards | Familiar AI transparency sources, safely narrowed to source boundaries. |
| European public data | EEA source audit and EEA AQ manual blocked card | European open-data source-boundary and blocked-source discipline. |
| Narrow positive empirical result | NASA POWER D-103 | Shows that fixed public-data gates can produce reusable evidence. |
| Honest negative result | NOAA CO-OPS D-131 | Shows a protocol can fail without being renamed as success. |
| External operator path | Starter pack, rerun issues and boundary-review issues | Shows how another reader can inspect, rerun or challenge a card. |

## Risk Register

| Risk | Control |
| --- | --- |
| Scope grows into a general verification platform | Keep work to validators, source-boundary checks, registry, workflows and examples. |
| Source audits are misread as safety or runtime claims | Repeat claim boundaries in cards, docs and issue templates. |
| Blocked/negative cards look like project failure | Explain that blocked and negative outcomes are first-class evidence. |
| Artifact-only records are confused with validated cards | Keep artifact-only records in a separate section and mark them as not evidence cards. |
| Single-maintainer bus factor | Publish release process, maintainer boundary, governance notes and reproducible workflows. |
| External operators do not know where to start | Maintain issue templates, rerun workflow and external operator starter pack. |
