# 12 AI Life Rules

Status: practical guidance. This page does not create a new evidence-card
schema, result status, empirical result, runtime controller, certification or
approval process.

## Core Idea

ClaimBound can be used as a portable evidence-bound control layer for AI claims
and actions.

```text
AI may assist, but evidence must bind.
```

The rules can be used internally by builders and operators, externally by
reviewers and users, or publicly through ClaimBound evidence cards. They do not
replace an AI system's hidden policies, tests, review, access control,
sandboxing, monitoring or human judgment. They add a visible evidence layer
around claims, actions, approvals, blocked states and tombstones.

The practical rule is simple:

```text
AI output is not trusted until it passes visible ClaimBound checks.
```

For v1, these rules are guidance and mapping language. They do not add new
required fields to existing cards. Future examples may add optional templates for
AI action boundaries, reversibility classes, human gates and action logs without
breaking the current card registry.

## How To Read The Rules

Each rule has the same shape:

| Part | Meaning |
| --- | --- |
| Human rule | The plain-language behavior expected from an AI-assisted workflow. |
| ClaimBound gate | The checkable evidence requirement. |
| Internal use | How a team, maintainer, CI flow or operator can use it privately. |
| External use | How a reviewer, user or public reader can challenge the claim. |
| Blocked state | What happens when evidence is missing or the boundary is too weak. |

## 1. Rule Of Bounded Claim

Human rule: AI must not expand a narrow checked claim into a broad conclusion.

ClaimBound gate: Every AI claim needs a `claim_boundary` tied to a card,
checklist, report or blocked state.

Internal use: PR summaries, release notes, model notes and operator reports say
only what the fixed check actually proved.

External use: A reviewer can ask which evidence card supports the public
statement and what the card forbids readers from inferring.

Blocked state: If the boundary is missing or too broad, the claim remains
unsupported and should not be presented as evidence.

## 2. Rule Of Evidence Before Authority

Human rule: AI must not treat model confidence, brand, role, title or fluent
language as proof.

ClaimBound gate: A trusted AI claim needs a source, protocol or checklist,
hashes or retained artifacts when applicable, exact result status and limitation
text.

Internal use: Teams can require AI-written summaries to cite the card, command,
source or report they are summarizing.

External use: Readers can reject statements that rely on reputation or tone
instead of a visible evidence record.

Blocked state: If the source, card, report or status cannot be found, the claim
is treated as unsupported or blocked rather than accepted.

## 3. Rule Of Frozen Rules Before Run

Human rule: AI must not change success criteria after seeing the result.

ClaimBound gate: Source boundary, target, scorer, baseline, controls, acceptance
gate and forbidden inference are fixed before execution.

Internal use: CI jobs, agent tasks and evaluation runs keep the command path,
fixtures and decision rule stable before outputs are inspected.

External use: A reviewer can compare the final card with the protocol to see
whether the rule changed after the outcome.

Blocked state: If the gate was changed after outcome inspection, the run cannot
produce a trusted positive claim.

## 4. Rule Of Source Lineage

Human rule: AI must know where the claim, data, prompt, file, document or result
came from.

ClaimBound gate: Record source URL or path, access date, commit or version,
hashes or manifest references, and source-rights or payload policy.

Internal use: Operators can keep raw or restricted materials outside the public
repository while preserving hashes and sanitized summaries.

External use: Reviewers can inspect the source boundary without needing hidden
raw payloads.

Blocked state: If lineage is missing, unstable or not safe to disclose even as a
summary, the claim should block instead of turning green.

## 5. Rule Of Honest Blocked State

Human rule: AI must not convert missing evidence into a weak positive result.

ClaimBound gate: Missing source access, rights, coverage, model identity,
scoring evidence, logs or hashes becomes a documented blocked or insufficient
state.

Internal use: Teams can preserve failed or blocked AI work without renaming it
as success.

External use: Readers can see that a blocked card is a useful evidence boundary,
not a hidden failure.

Blocked state: The blocker is named plainly, and no empirical pass or broad
trust claim is made.

## 6. Rule Of Reversible Action First

Human rule: AI should prefer reversible steps before hard-to-reverse actions.

ClaimBound gate: Risky AI-assisted workflows record whether the action is
read-only, draft, reversible, hard to reverse or irreversible.

Internal use: Agents start with read-only audit, local dry run, draft PR,
reviewable patch or rollback-ready change before stronger action.

External use: Reviewers can ask why a hard-to-reverse step happened before a
draft, test or review gate.

Blocked state: If reversibility is unknown for a high-impact action, the action
should not proceed as trusted evidence.

## 7. Rule Of Human Gate For High-Impact Actions

Human rule: AI must not complete high-impact or irreversible actions without a
human approval gate.

ClaimBound gate: The workflow records approval requirement, approval reference,
protected surfaces and the final human-reviewed boundary.

Internal use: Maintainers can require approval before merge, release,
permission changes, destructive operations, public publication or outbound
messages from the project.

External use: A reviewer can check whether the card or PR record shows human
approval where the action boundary required it.

Blocked state: If required approval is missing, the work is blocked by the human
gate. This is a blocker reason, not a new v1 `result_status`.

## 8. Rule Of No Hidden Goal Substitution

Human rule: AI must not replace the user's stated goal with a different goal
that is easier, flashier or more favorable to the AI output.

ClaimBound gate: Each AI-assisted task records the user-intent surface, allowed
scope and forbidden substitutions.

Internal use: Operators keep agent work tied to the request, issue, protocol or
PR objective that started the task.

External use: Reviewers can challenge work that silently shifts from checking a
claim to promoting a broader story.

Blocked state: If the intent surface is missing or the output solves a different
problem, the result should be rewritten, narrowed or blocked.

## 9. Rule Of Minimal Necessary Data

Human rule: AI should use and publish only the data needed for the claim.

ClaimBound gate: Public records store sanitized summaries, hashes, paths and
limitations instead of raw private payloads, full transcripts or restricted
source material.

Internal use: Teams can keep local run roots, raw logs and restricted inputs out
of the public repository while retaining enough evidence to review.

External use: Readers can inspect the public boundary without receiving material
that should not be redistributed.

Blocked state: If the claim requires raw material that cannot be safely
summarized or hashed, the public claim should block or stay local.

## 10. Rule Of Counterclaim Search

Human rule: AI must look for contradiction, absence and negative evidence, not
only support.

ClaimBound gate: The protocol or checklist records expected counterclaims,
negative controls, missing-evidence checks or forbidden positive inferences.

Internal use: Operators ask what would disprove, weaken or block the AI claim
before accepting the output.

External use: A reviewer can ask whether the card checked only supporting facts
or also looked for blockers and negative outcomes.

Blocked state: If obvious contradictory or missing evidence was not checked, the
claim is not ready for trusted publication.

## 11. Rule Of Audit Trail

Human rule: AI-assisted work must leave a record of what happened, why, by which
tool and with what result.

ClaimBound gate: Keep command paths, tool surfaces, source references, output
hashes, sanitized reports, operator notes and final status together.

Internal use: Teams can reconstruct an agent run, PR check, rerun or manual
review without trusting memory or chat text.

External use: A reviewer can inspect the evidence card, report and registry
entry instead of relying on a narrative claim.

Blocked state: If the audit trail is missing or cannot be summarized, the work
should not be promoted as trusted evidence.

## 12. Rule Of Tombstone And Supersession

Human rule: AI must not quietly forget a claim that became wrong, stale,
overbroad, blocked or superseded.

ClaimBound gate: Failed, stopped, drifted or superseded branches get a tombstone
or explicit supersession record when v2 or v3 tracking is used.

Internal use: Teams can stop repeated attempts from recycling the same weak
branch as a new positive claim.

External use: Readers can see which branches are alive, stopped, proof-ready,
blocked or superseded.

Blocked state: If a branch needs a tombstone before descendants can be trusted,
new descendant claims stay blocked until the stop record is visible.

## Internal, External And Public Use

| Use mode | What the rules help with | Typical artifacts |
| --- | --- | --- |
| Internal | Agent task control, CI gates, PR review, release gates, local run roots and operator notes. | Protocols, checklists, local logs, draft cards and private run roots. |
| External | Reviewer questions, user challenges, independent reruns and source-drift reports. | Evidence cards, sanitized reports, issue templates and rerun notes. |
| Public | Open evidence records that can be read without trusting a hidden AI policy. | JSON cards, SVG cards, registry entries, docs and tombstones. |

The same rule can serve all three modes. A team may first use it internally,
then publish only the sanitized card and boundary when public evidence is
appropriate.

## Relationship To Evidence Cards

Evidence cards remain the public unit of record. The 12 AI Life Rules explain
how to read and use those cards around AI-assisted work:

- green means one narrow gate passed, not broad trust;
- amber or blocked means the rules stopped an unsupported claim;
- red or negative means the protocol ran and the claim did not pass;
- yellow or drift means the outcome remains useful with an explicit limitation;
- gray means request, scaffold or draft only.

The rules do not require historical cards to migrate. They make the existing
card colors and statuses easier to explain.

## Deferred V2 Example: AI PR Merge Guard

A strong future demo is an AI-assisted PR merge guard:

```text
An AI coding assistant should not merge a pull request unless the claim
boundary, fixed check command, changed-file surface, human approval requirement
and rollback path are recorded.
```

This is intentionally deferred from v1. Implementing it as a card, schema or
family ledger would require real artifacts, validator decisions and registry
updates. The v1 rulebook keeps the concept visible without changing the current
evidence-card protocol.

## Boundary

Do not claim that the 12 AI Life Rules make an AI system generally safe,
truthful, secure, autonomous, production-ready or certified. The honest claim is
narrower:

```text
The rules make AI-assisted claims and actions easier to bound, block, review,
reproduce, audit and tombstone.
```
