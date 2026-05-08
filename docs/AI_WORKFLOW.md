# AI Workflow

AI assistance is allowed when it makes the evidence trail easier to inspect.
It must not decide the final result by opinion.

## Correct Use

AI can help with:

- drafting an evidence request from a public claim;
- generating a scaffold for a selected request;
- writing runner, parser, scorer or validator code;
- preparing a reproduction checklist;
- summarizing machine-readable reports;
- drafting an evidence card from validated artifacts;
- checking whether card wording overclaims.

The human operator remains responsible for the source boundary, protocol freeze,
final result status, claim boundary and publication decision.

## End-To-End Flow

1. **Evidence request**

   AI may help turn a public claim into an issue using the evidence request
   template. The issue must still include a narrow question, proposed sources,
   scoring or resolution rule, risks and forbidden claims.

2. **Scaffold**

   AI or CLI may create a draft protocol, playbook, checklist, operator
   declaration, draft card and source-probe summary.

   This is not evidence. It must not assign a positive or negative result.

3. **Protocol freeze**

   A human freezes source, target, model or method identity, baselines, controls,
   scoring rule, acceptance gate, stop rules and forbidden after-result changes.

4. **Run or reproduction**

   AI may run commands or write deterministic code. The result must come from a
   script, checklist or validator, not from model judgment.

5. **Sanitized report**

   AI may summarize already computed outputs. Raw payloads, full transcripts and
   restricted source materials stay outside the public repository.

6. **Evidence card**

   AI may draft JSON fields from the report. A validator must check required
   fields, status, claim boundary, raw-payload policy and forbidden claims.

7. **Registry**

   AI may prepare a registry patch only after the card validates. The registry
   must not contain raw payloads.

8. **Human publication review**

   A human confirms that the card says only what the evidence supports.

## Required Disclosure

Every completed card should disclose whether AI assisted with:

- request drafting;
- scaffold generation;
- source review support;
- code generation;
- run execution;
- report summarization;
- card drafting.

## Stop Rules For AI-Assisted Work

Stop and record a blocked, insufficient or invalid state when:

- source rights are unclear;
- official-source status cannot be checked;
- raw payloads or transcripts cannot be hashed or referenced safely;
- the scoring rule was not fixed before outcome inspection;
- a prompt set or benchmark set changed after the run began;
- a model/API identity is unavailable or unstable;
- the evidence card would need broad unsupported wording to look positive.

## AI Must Not

AI must not:

- choose favorable data after seeing outcomes;
- change thresholds or gates after scoring;
- fabricate hashes, citations, commands or source-rights notes;
- hide failed runs;
- convert blocked or negative results into positive claims;
- approve its own final evidence card without validation and human review.
