# ClaimBound In 30 Seconds

ClaimBound turns a public statement such as "we checked this", "this source
exists", "this benchmark reproduced", "this model is better" or "this risky
change passed" into a small evidence card.

The card records what was checked, which public source was used, which protocol
was frozen before the result, which command or checklist ran, what status was
assigned, which hashes support the record, what limitations apply and how
reproducible the result is.

The main question is simple:

```text
Where is the evidence?
```

If there is no evidence card, the statement is still only a claim.

## What Problem It Solves

ClaimBound is an anti-overclaiming layer. It helps public AI, ML, data,
software-development, funding-review and reproducibility work say exactly what
has been checked and what has not.

The point is not to say "the model is safe" or "the change works". The point is
to say something narrow enough to inspect:

```text
This official source page was reachable, contained the expected markers and was
hashed under the documented source-audit protocol on the recorded access date.
```

That narrow result must not be silently upgraded into a broad model-safety,
product-quality, deployment-readiness or funding-approval claim.

## Who It Helps

| Audience | Typical use |
| --- | --- |
| AI and LLM evaluation teams | Turn model, prompt, RAG, agent or benchmark claims into inspectable evidence cards. |
| AI risk, security and automation-control teams | Record bounded checks for tool use, prompt-injection controls, release gates or incident evidence. |
| Software developers and maintainers | Attach a reviewable evidence trail to risky, AI-assisted or regression-sensitive changes. |
| Open science and reproducibility teams | Publish reproduced, negative, blocked and drift outcomes instead of hiding weak results. |
| Funding reviewers and public-interest teams | Replace marketing-style progress language with protocol, source, status and limitation records. |
| Public data, civic tech and procurement teams | Check official source and evidence boundaries before relying on public claims. |

## What Makes It Different

Experiment trackers, model registries and leaderboards usually ask which run,
model or score is better. ClaimBound asks a smaller question:

```text
What exactly was proven, under which rules, and where does that proof stop?
```

Green means one narrow claim passed under the stated protocol. Negative,
blocked, insufficient and drift results are useful too, because they prevent
weak or incomplete evidence from being renamed as success.

For AI-assisted claims and actions, the same discipline becomes
[12 AI Life Rules](TWELVE_AI_LIFE_CONTROLS.md): a compact control layer for
boundaries, sources, frozen gates, blocked states, human review, audit trails
and tombstones.

## Honest Caveat

ClaimBound is an early open-source evidence framework with public examples and a
clear social need. It should be presented as a practical evidence-discipline
toolkit, not as a mature standard, certification authority or already adopted
market category.
