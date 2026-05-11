# Project Next Steps

This page separates what should stay in the public repository from larger
platform work. The public repository must remain independently usable.

## Public Repository Focus

Keep the open project understandable before adding more machinery:

1. Lead with the simple message: ClaimBound turns a public claim into a small
   evidence card.
2. Show real cards early: one green source audit, one yellow limited
   reproduction card and one red negative result.
3. Keep the beginner path in this order:
   [ClaimBound in 5 minutes](CLAIMBOUND_IN_5_MINUTES.md),
   [evidence cards](evidence_cards/README.md),
   [getting started](GETTING_STARTED.md),
   [result statuses](RESULT_STATUS.md).
4. Keep technical protocols versioned and deeper in the documentation.
5. Publish only validated cards in the registry.
6. Keep raw payloads, prompt text and transcripts outside the public repository
   unless rights clearly allow redistribution.

## Strong Public AI Examples

These are good first-screen examples because they are familiar public AI claims
but can be narrowed safely.

| Public claim candidate | Narrow ClaimBound question | Current repository state |
| --- | --- | --- |
| Anthropic publishes public system-card documentation for its AI models. | Can the official system-card page be source-audited by URL, access date, expected markers and SHA-256? | Green source-audit card exists. It does not prove Claude safety or runtime behavior. |
| OpenAI publishes a GPT-5 system-card PDF. | Can the official PDF source be audited by content type, byte size, expected marker and SHA-256? | Green source-audit card exists. It does not prove model quality or deployment readiness. |
| Google DeepMind publishes model-card documentation. | Can the official model-card source boundary be checked and hashed? | Green source-audit card exists. It does not prove Gemini benchmark superiority. |
| xAI publishes Grok prompt sources in a public repository. | Can the public repository commit, README/LICENSE presence and prompt-file hash manifest be verified without copying prompt text? | Green source-audit card exists. It does not prove live runtime equivalence. |
| A public AI product claim says a model or agent can perform a task. | Are model ID, prompt set, transcript hashes, scoring rule and stop rules available before scoring? | Current product/eval/procurement cards are blocked until the source evidence is good enough. |

Future product-level examples can use familiar names such as Claude Code,
ChatGPT or Gemini only after the exact public claim, official source URL, model
or product identity, prompt/transcript policy and scoring rule are frozen. Until
then, they should remain candidates, not evidence.

## Near-Term Public Roadmap

These are practical next improvements for the open repository:

1. Smart SourceProbe v1: HTTP status, content type, source owner, license/terms
   links, structured-data hints and `safe / human review / blocked` output.
2. Scaffold workflow hardening: reusable builders for request, protocol,
   playbook, checklist, draft card, registry patch and SVG rendering.
3. Manual-track completion path: the EEA AQ D-001 runner and blocked card now
   exist; next, add an external raw-payload rerun path and independent operator
   reproduction record.
4. Static searchable registry: filters by status, source, domain, audience and
   SVG preview.
5. Completed example set: 10 to 20 honest cards across positive, negative,
   blocked, insufficient, reproduced and source-byte-drift outcomes.
6. AI claim protocol: prompt hash or Merkle root, model/API metadata,
   transcript hashes, resolution source and scoring rule.
7. Independent rerun workflow: reproduction PR template, reproduction badge and
   registry fields.

## Later Platform Work

These should wait until the static cards, validators, examples and workflows are
solid:

1. Hosted registry API or database-backed search.
2. User accounts, authenticated write endpoints and operator profiles.
3. Public request queue with verifier assignment.
4. Signed evidence cards or transparency-log integrations.
5. DOI/archive deposits for selected evidence bundles.
6. Training, hosted support and sustainability services.

## Out Of Scope

Blockchain, token, wallet, on-chain storage and chain timestamp features are not
part of the public roadmap. The trust model is public code, source lineage,
frozen protocols, hashes, claim boundaries and independent reproduction.
