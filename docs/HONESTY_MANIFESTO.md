# ClaimBound Honesty Manifesto

ClaimBound exists to make narrow public-source claims harder to overstate and
easier to challenge.

The project is built around a simple rule:

```text
Rules first. Source second. Run third. Claim last.
```

## Principles

1. A protocol must be fixed before outcome inspection.
2. A source boundary must be checked before any performance claim.
3. Negative, blocked and insufficient-coverage results are valid outcomes.
4. A result must not be rewritten to look better after the run.
5. A model output is not evidence by itself.
6. A public claim must fit inside the protocol boundary.
7. Raw payload handling must respect source rights and repository policy.
8. Another operator should be able to inspect the record and decide whether a
   rerun is possible.

## What Counts As Evidence

A ClaimBound evidence record can include:

- frozen protocol;
- family ledger for related tracks;
- official source reference;
- source-rights note;
- raw payload hash manifest outside the repository;
- parser or manual audit log;
- runner command;
- baseline and control summary;
- result status;
- sanitized report hash;
- evidence card;
- reproduction level.

A ClaimBound evidence record does not rely on:

- screenshots as the only source of truth;
- model confidence;
- undocumented manual judgment;
- hidden threshold changes;
- selective deletion of weak windows;
- broad claims outside the protocol boundary.

## Anti-Cheating Design

ClaimBound should make manipulation visible through:

- protocol files committed before real runs;
- family ledgers that separate diagnostic, proof and closure tracks;
- fixed target, candidate, baselines, controls and acceptance gate;
- raw payload hashes recorded outside the repository;
- sanitized reports committed inside the repository;
- publication guards that reject raw payloads and forbidden public claims;
- result statuses that allow failure without stigma;
- evidence cards that require limitations and reproduction level.

## Allowed Public Claim Shape

Use narrow wording:

```text
Under protocol P, using source S accessed on date D, candidate C received
status R under gate G. This does not imply performance outside the documented
claim boundary.
```

Avoid broad wording:

```text
The system is generally predictive.
The model is best.
The method is ready for deployment.
The result proves a universal effect.
```

## Durable Purpose

ClaimBound can remain useful as long as public claims need disciplined evidence.
Individual domains may change, APIs may drift and models may be replaced, but
the core record stays useful:

```text
What was claimed?
What source was used?
What was fixed before the run?
What happened?
What can be reproduced?
What must not be claimed?
```
