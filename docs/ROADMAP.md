# Roadmap

This roadmap is about the public open-source foreground.

The working split between immediate public work, near-term public work and
later platform work is summarized in
[Project next steps](PROJECT_NEXT_STEPS.md).

## Immediate Implementation Plan

The immediate goal is to make ClaimBound obvious to a new reader:

```text
ClaimBound turns a narrow public AI, ML or data claim into a reproducible
evidence card with protocol, source lineage, hashes, status, claim boundary and
reproduction level.
```

The project should read as one useful whole: not a leaderboard, not a
forecasting service, not a certification authority and not an archive, but a
small public evidence-card toolkit for claims that should be checked under
rules fixed before the result is known.

### Public Message

Add or tighten public documentation around:

- the problem: public AI/ML/data claims are easy to overstate and hard to rerun;
- the answer: one claim, one frozen protocol, one source boundary, one exact
  status, one compact evidence card;
- the strongest call to action: "Where is the evidence?";
- the difference from experiment trackers, paper indexes, leaderboards, DOI
  archives, fact-checking sites and certification services;
- the two execution paths: `MANUAL_NO_AI` and `AUTOMATED_AI_ASSISTED`.

### Global Audiences And Examples

Add nine audience examples to the public README and audience/use-case docs.
Each example should show what a concrete ClaimBound record gives that ordinary
marketing, screenshots or narrative claims do not give.

| Audience | Example public use |
| --- | --- |
| AI and LLM evaluation teams | Check a model, RAG, agent or benchmark claim with timestamp, prompt hash, model/API metadata, source rule and scoring rule. |
| Open-science and reproducibility researchers | Publish negative, blocked and reproduced outcomes as useful evidence records instead of hiding them. |
| Funding reviewers and program evaluators | Inspect what was promised, which protocol and source were used, what happened and what cannot be claimed. |
| Data stewards and public-data teams | Audit whether a source is official, rights are clear, coverage is sufficient and raw redistribution is avoided. |
| Civic-tech, journalism and watchdog projects | Check claims against public sources such as government data, climate data, mobility data and public infrastructure records. |
| ML researchers | Add a small honest appendix to a paper or report with protocol, hashes, result status and reproduction level. |
| Educators | Teach reproducible ML by requiring students to run a protocol, publish pass/fail/blocked status and explain limitations. |
| Companies with AI products | Give customers narrow evidence cards for specific public claims instead of broad "trust us" statements. |
| Independent verifiers, procurement teams and public buyers | Request or rerun a narrow evidence card before adopting, buying or citing an AI/data product claim. |

### Claim Request Workflow

Before building a hosted service, add a lightweight open workflow:

- GitHub issue template for an evidence request;
- required fields: claim, proposed source, public value, audience, deadline,
  expected result type and any known source-rights concerns;
- labels such as `evidence-request`, `source-audit`, `forecast-resolution`,
  `manual-track` and `ai-assisted-track`;
- clear rule that a request is not evidence until a validated card exists.

### Independent Verification Workflow

Add documentation for how another operator can pick up a request or rerun an
existing card:

- freeze or reference the protocol before scoring;
- use the manual or AI-assisted track;
- record command logs, source access date, hashes and deviations;
- publish `reproduction_attempt` when rerunning an existing result;
- update the registry only after the evidence card validates.

### Evidence Card 1.1

Extend the card model carefully, keeping the current compact public format:

- keep `record_type` required with exactly:
  `evidence_result`, `source_audit`, `protocol_registration`,
  `reproduction_attempt`;
- add a stable registry number or registry sequence field;
- record operator public name or organization;
- record latest verification date;
- record verification count or independent-rerun count;
- record verification level such as single-operator, independent rerun or
  multi-operator;
- keep raw payloads outside the repository unless rights and policy explicitly
  allow otherwise.

### Visual Card Improvements

Fix evidence-card rendering quality:

- stable field lengths;
- word wrapping for long source names, commands and claim boundaries;
- multi-line limitations/comments;
- status color that reflects validity, not popularity;
- SVG rendered from validated JSON rather than edited by hand.

### Validity Levels And Tamper Evidence

ClaimBound cannot make fraud impossible without trusted execution, vendor
cooperation or independent witnesses. The realistic public goal is stronger:
invalid or weak evidence should be visible immediately.

Add deterministic card validity levels:

| Level | Meaning |
| --- | --- |
| `GREEN_VALIDATED` | Protocol frozen, required fields present, hashes/logs valid, source boundary recorded, scoring rule fixed, card validates and rerun path is clear. |
| `YELLOW_LIMITED_REPRODUCIBILITY` | Card validates but has a known limitation such as proprietary API drift, source-byte drift, no independent rerun or temporary prompt embargo. |
| `RED_INVALID_OR_TAMPER_EVIDENCE` | Missing prompt/source/scoring rule, changed protocol after result, missing hashes, broad claim, unverifiable source or validator failure. |
| `GRAY_DRAFT_NOT_EXECUTED` | Scaffold or request exists, but no real run has happened. |

Votes, popularity and community interest must never decide validity. They can
help prioritize claims, but only protocol evidence decides card status.

### Proprietary Model Claim Protocol

Add a first public protocol draft for proprietary model claims, using the
"Where is the evidence?" example.

Example scope:

```text
Claim: a proprietary model release performs better on a frozen public task set.
Inputs: frozen prompt set, prompt hash or Merkle root, model/API metadata,
temperature/settings, answer timestamp, raw transcript hashes.
Resolution: public or official sources only.
Scoring: fixed before answer collection.
Result: evidence card with pass, negative, blocked or limited-reproducibility
status.
```

For prompts, prefer commit-reveal:

1. Before the run, publish or record a hash/Merkle root for the prompt set.
2. During the run, record model settings, timestamps, request IDs when
   available and raw transcript hashes.
3. After the run, reveal prompts unless there is a documented embargo.
4. If prompts cannot be revealed, mark the card as limited reproducibility.

Screenshots alone should never produce a green card.

### Manual Track Completion

Finish the current manual track as a first-class outcome. The result can be
passed, negative, blocked or insufficient coverage. The important point is that
the status is honest, source rights are recorded, raw payload policy is clear
and the final claim boundary is narrow.

### Scaffold MVP

Implement a small deterministic scaffold command before building a server:

- `ProtocolDraftBuilder`;
- `ChecklistRenderer`;
- `PlaybookRenderer`;
- `EvidenceCardScaffolder`;
- `CardValidator`;
- `SvgRenderer`;
- a simple `RegistryPatchBuilder` that prepares a patch only after validation.

Keep heavier discovery modules for later unless they are small and deterministic:

- `SourceProbe`;
- `RightsProbe`;
- `TrackClassifier`.

The current public scaffold should remain conservative. Smart source probing
with HTTP/content-type checks, OpenAPI/Swagger hints, license/terms discovery,
robots/terms notes and safe/blocked recommendations is better scoped as a
public roadmap item because it needs careful validation and should not look like
an automated legal or final-evidence conclusion.

### High-Value Public Card Candidates

Good next cards should be concrete, current and narrow:

- xAI `grok-prompts` repository source-audit reruns;
- OpenAI system-card page/PDF source audits;
- Anthropic system-card index and selected-card source audits;
- Google DeepMind model-card page/PDF source audits;
- LLM forecast-resolution records with timestamped answers and official
  resolution sources;
- independent reproduction attempts for existing NASA POWER and NOAA cards.

Each AI-company documentation card should prove only source availability,
version/date, hash and limitation boundary. It must not claim model superiority,
runtime equivalence, safety certification or deployment readiness.

### What To Defer

Do not make these part of the immediate public implementation:

- user registration;
- hosted request queue;
- API-key write endpoints;
- Postgres-backed registry;
- private or closed groups;
- ranking by votes as evidence validity;
- blockchain, token, wallet, on-chain storage or chain timestamp features.

These can be future platform work only after the card schema, validator,
manual workflow, examples and public positioning are clear.

## 0.1.x

- Improve reproduction instructions.
- Add claim-boundary documentation.
- Add result-status documentation.
- Add public data policy.
- Add manual public-domain audit templates.
- Strengthen publication guards.
- Add project-positioning documentation.
- Add honesty, manual-audit and AI-assisted operator rules.

## 0.2.x

- Add one additional public-domain protocol.
- Add one additional parser or source adapter if source rights are clear.
- Publish one additional sanitized evidence record, whether positive, negative
  or source-blocked.
- Add an evidence-card template.
- Add an evidence-card validator with required execution-mode provenance.

## 0.3.x

- Add a small protocol registry.
- Add report validation helpers.
- Add richer source-lineage manifests.
- Add examples showing negative controls and blocked-source outcomes.
- Add a machine-readable evidence-card index.

## 0.4.x

- Add examples that show how ClaimBound can be used for public-source forecast
  audits, negative-result records, source-boundary audits and independent
  reproductions.
- Add a narrow LLM forecast-resolution protocol with timestamped prompts,
  official resolution sources and pre-selected scoring.
- Add automated checks for evidence-card completeness and forbidden claim
  patterns.

## Later

- Publish selected evidence bundles as stable release archives.
- Explore DOI repository deposits for high-value evidence records.
- Keep archives secondary to the protocol, hashes, claim boundary and
  reproduction path.
- Consider optional transparency backends only after the core registry is useful:
  signed releases, public transparency logs, archival timestamping or other
  append-only hash anchoring. ClaimBound should not depend on blockchain for
  trust.

## Non-Goals

- No production forecasting service.
- No public-health alert system.
- No private-background performance claim.
- No raw payload redistribution.
- No informal or speculative claims.
- No general model leaderboard as the primary product.
- No blockchain, token, wallet, on-chain storage or chain timestamp features.
