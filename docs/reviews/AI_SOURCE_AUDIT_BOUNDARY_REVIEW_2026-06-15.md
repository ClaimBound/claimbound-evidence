# AI Source Audit Boundary Review (2026-06-15)

Reviewer: maintainer (`rostsh`)
Scope: public AI source-audit cards and adjacent docs wording.

## Card checklist

| Card | boundary OK? | docs overclaim? | fix needed? |
| --- | --- | --- | --- |
| Anthropic system cards | YES | NO | NO |
| OpenAI GPT-5 system card | YES | NO | NO |
| Google DeepMind model cards | YES | NO | NO |
| Grok prompts repository | YES | NO | NO |

## Findings

All four cards:

- restrict `claim_boundary` to source availability / metadata / hashes;
- include explicit exclusions for safety, quality, benchmarks and deployment;
- use source-audit-only `allowed_claim_sentence` text;
- document `known_limitations` completely.

`README.md` reviewer FAQ correctly states that source-audit cards do **not** prove safety, quality or runtime behavior.

`docs/CURRENT_EVIDENCE_TRACKS.md` and `docs/REVIEWER_SUMMARY.md` keep AI examples in the source-audit lane without benchmark-superiority language.

## Conclusion

No JSON or SVG wording changes required. Boundary review passes under frozen protocol scope.
