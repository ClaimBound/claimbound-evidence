# Project Next Steps

This page separates public repository work from near-term public work and later platform work. The public repository must remain independently usable.

## Do Now In The Public Repository

These items make the open project clearer and safer without waiting for larger platform work:

1. Keep the README focused on the simple public message:
   "ClaimBound turns a public claim into a small evidence card."
2. Keep a beginner path:
   [ClaimBound in 5 minutes](CLAIMBOUND_IN_5_MINUTES.md),
   [getting started](GETTING_STARTED.md), then the operator docs.
3. Show two or three concrete evidence-card examples on the README, including
   a positive source audit, a positive narrow result and a negative result.
4. Keep the evidence request issue template as the public entry point for new
   claims.
5. Provide scriptable commands:
   `uv run claimbound new`, `uv run claimbound demo ...`,
   `uv run claimbound validate-all`.
6. Keep improving SVG cards rendered from JSON, not edited by hand.
7. Add practical AI workflow rules that explain what AI may draft, run and
   summarize, and where human approval is required.
8. Keep raw payloads outside the public repository.
9. Publish only validated cards in the registry.

## Good Public Card Candidates

These candidates are public and useful because they are current AI-transparency
or public-source claims. Each should start as a narrow source audit or
readiness card, not as a broad model-quality claim.

| Candidate | Useful narrow question | Why it matters |
| --- | --- | --- |
| xAI `grok-prompts` repository | Is the public prompt repository reachable at a fixed commit, with README/LICENSE and prompt-file hashes? | Strong public AI transparency example already represented in this repo. |
| OpenAI system cards | Can a specific published system-card page/PDF be source-audited by date, URL, hash and limitation boundary? | Shows how model-safety claims can be linked to checkable public evidence without claiming model superiority. |
| Anthropic system cards | Can the system-card index and selected card be source-audited with publication date, URL and hash? | Good comparison source for public model documentation practice. |
| Google DeepMind model cards | Can a selected model-card page/PDF be source-audited with date, URL, hash and stated limitations? | Broadens examples beyond one vendor and keeps the claim boundary narrow. |
| Public LLM forecast-resolution record | Did timestamped model answers resolve against official sources under a frozen scoring rule? | Moves from documentation audit to actual reproducible evaluation. |
| Independent rerun of NASA POWER D-103 | Can another operator reproduce the same outcome or record source-byte drift? | Demonstrates reproduction as a first-class result. |

## Put In The Near-Term Public Roadmap

These are larger than a cleanup pass and should be public roadmap items:

1. Smart SourceProbe v1:
   HTTP status, content type, OpenAPI/Swagger hints, CSV/JSON/XML hints,
   license/terms link discovery, robots/terms note, checksum possibility and
   `safe to continue / needs human review / blocked` output.
2. Scaffold automation hardening:
   reusable builders for protocol, playbook, checklist, draft card, registry
   patch and SVG rendering.
3. Manual-track simplification:
   wizard-assisted operator flow, deviation log, run-root setup and fewer
   copy/paste steps.
4. Static searchable registry:
   card search, filters by status/source/domain/audience, SVG preview and
   public read-only pages.
5. Completed example set:
   10 to 20 honest cards across positive, negative, blocked, insufficient and
   reproduced outcomes.
6. Proprietary/public AI claim protocol:
   prompt hash or Merkle root, model/API metadata, transcript hashes, resolution
   source and scoring rule.
7. Independent rerun workflow:
   reproduction PR template, reproduction badge and registry fields.
8. Funders page:
   public value, reproducibility, negative results, deliverables and scope
   boundaries.

## Keep For Later Platform Work

These should wait until the static cards, validators, examples and workflows are
solid:

1. Postgres-backed registry and hosted API.
2. User accounts, authenticated write endpoints and operator profiles.
3. Public request queue with verifier assignment.
4. Signed evidence cards or transparency-log integrations.
5. DOI/archive deposits for selected evidence bundles.
6. Training, hosted support and sustainability services.

## Boundary

The public repository should contain the open toolkit, public docs, validated
cards, scripts, registry and public roadmap. Operational planning details are outside this public repository.
