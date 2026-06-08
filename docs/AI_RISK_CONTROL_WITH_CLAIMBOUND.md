# AI Risk Control With ClaimBound

Status: practical guidance. This page does not create an empirical result, safety standard, certification, compliance claim or runtime safety controller.

ClaimBound can be used as an evidence-bound control layer around AI-assisted work. It is not a replacement for safety engineering, cybersecurity, access control, sandboxing, formal verification, runtime monitoring, robot safety standards, human supervision or emergency-stop design.

For the compact rulebook version of this idea, see
[12 AI Life Rules](TWELVE_AI_LIFE_CONTROLS.md). Those rules are practical guidance for
using ClaimBound internally, externally or publicly around AI-assisted claims
and actions.

## Is ClaimBound A Rule System For Managing AI?

ClaimBound is not a set of moral slogans for AI. It is a way to make narrow AI-related claims and actions checkable.

A useful way to describe it:

```text
ClaimBound = external evidence-control plane for claims, AI-assisted changes and risk-sensitive decisions
```

It can indirectly govern or limit AI by forcing AI output to pass through:

- a narrow claim boundary;
- a frozen protocol or checklist;
- source, prompt, fixture, model, command and environment boundaries;
- deterministic validators or manual no-AI checklists;
- hashes, logs and sanitized reports;
- exact result statuses such as passed, negative, blocked or insufficient;
- explicit forbidden inferences;
- optional protocol v2 family/frontier ledgers for budgets, dependencies, diagnostics, proof tracks and stop rules;
- optional protocol v3 tree overlays for public maps of iron claims, flow claims, tombstones and blocked branches.

The AI may help draft, run or summarize. It must not decide that its own output is true, safe, secure, deployment-ready or approved.

## What Risks Can Be Reduced?

| Risk | How ClaimBound reduces it | Can it be removed completely? |
| --- | --- | --- |
| Overclaiming | The card states one exact claim, status, source boundary and limitation. | No. A human or downstream reader can still misuse the card. |
| AI hallucination | Model-written text must be tied to sources, commands, hashes and validators. | No. The model can still hallucinate before review. |
| Prompt injection or instruction hijack | The model output is not trusted directly; tools, commands and final status are bounded by protocol and validation. | No. Runtime isolation and security controls are still required. |
| Selective reruns and cherry-picking | Protocol v2 can freeze proof budgets, diagnostics, tombstones and closure rules. | Reduced strongly when enforced, but not eliminated if operators hide runs. |
| Benchmark or eval hacking | Prompt sets, model IDs, scorers, transcript hashes and gates are fixed before scoring. | No. It reduces manipulation surface but does not prove general model quality. |
| Insecure output handling | AI output that becomes code, shell commands, SQL, robot actions or UI content must be reviewed and validated before use. | No. Sanitizers, sandboxes and code review are still required. |
| Data poisoning or source substitution | Source manifests, hashes, dependency records and reproduction paths make drift or substitution visible. | No. A compromised source can still be validly hashed. |
| Supply-chain confusion | Dependencies, model IDs, runner versions and artifacts can be pinned in the evidence trail. | No. Pinning is not vulnerability scanning. |
| Missing incident evidence | Required logs, hashes and reports make later review easier. | No. Logs can be incomplete unless the system is engineered to capture them. |
| AI agent overreach | Allowed actions, forbidden actions, stop rules and human approval gates are recorded before execution. | No. Tool permissions and runtime enforcement must exist outside ClaimBound. |
| Governance theater | A public card must show what was actually checked and what remains unsupported. | Reduced. It still depends on honest operation and review. |

## What ClaimBound Cannot Do

ClaimBound must not be described as removing all AI risk. It cannot by itself:

- stop malware or an active attacker;
- secure secrets, keys or production infrastructure;
- prevent a robot from moving unsafely in real time;
- prove that a vehicle, robot or model is generally safe;
- replace ISO, NIST, OWASP, IEC, automotive or robotics safety processes;
- replace tests, CI, code review, red-teaming, threat modeling, access control or sandboxing;
- turn a source audit into a runtime-behavior claim;
- turn a demo into certification.

The honest claim is narrower: ClaimBound makes unsupported claims, after-the-result rule changes, hidden negative results and unsafe inference jumps easier to detect.

## Difference From Mnemonic Or Moral Rules

A mnemonic rule is a short human-readable rule, such as:

```text
Do not harm a human.
```

That kind of rule is useful as a value reminder, but it is too broad for engineering control. It does not say which source was checked, which scenario was tested, which sensor boundary was used, what counts as harm, what the stop rule is, who approved the result, what failed or what must not be inferred.

ClaimBound turns broad rules into checkable evidence units.

| Human-readable rule | ClaimBound form |
| --- | --- |
| Do not harm a human. | In scenario fixture `RBT-SAFE-001`, the robot controller did not exceed the frozen speed/force envelope under the logged simulator and hardware-in-loop run. |
| Do not leak secrets. | The AI agent task ran with a frozen secret-scan command and no high-severity secret findings in the sanitized report. |
| Do not modify production without approval. | The agent branch did not touch protected deployment paths and the final card records human approval before merge. |
| Do not drive outside safe conditions. | The driving-assistance claim is limited to a defined operational design domain, logs takeover/disable events and blocks unsupported weather/road claims. |
| Do not let prompts override policy. | The prompt-injection test corpus produced no unauthorized tool call under the frozen allowlist and validator. |

The advantage is not that ClaimBound is more moral. The advantage is that ClaimBound is smaller, auditable and falsifiable.

## Robotics And Vehicle-AI Use

For robotics, autonomous systems and driver-assistance software, ClaimBound should be used around the engineering and release process, not as the millisecond-level safety controller.

Use it for pre-release, post-incident and public-claim evidence:

| Layer | Example ClaimBound use | Required external controls |
| --- | --- | --- |
| Requirements | Freeze the allowed task, operating domain, forbidden actions and safety envelope. | Hazard analysis, safety standards, human factors review. |
| Simulation | Record simulator version, scenario fixtures, seeds, pass/fail gate and logs. | Simulator validation and coverage analysis. |
| Hardware-in-loop | Hash hardware config, firmware version, sensor setup and measured limits. | Physical safety rigs, guards, emergency stop. |
| Runtime telemetry | Verify that logs capture intervention, override, stop and anomaly events. | Secure logging, tamper resistance, privacy controls. |
| Release gate | Block deployment if a required safety card is negative, blocked or insufficient. | CI/CD controls, approvals, staged rollout, rollback. |
| Public communication | Prevent a source audit or demo from being described as broad autonomy proof. | Legal, safety and product review. |

### Robot Example

Bad broad claim:

```text
The household robot is safe around people.
```

ClaimBound version:

```text
For fixture ROBOT-KITCHEN-REACH-001, firmware build X and simulator/runtime log set Y, the robot did not exceed the frozen speed, force and keep-out-zone thresholds during the defined reach-and-place task; this card does not claim general household safety.
```

A completed card can help decide whether one narrow release gate passed, failed, blocked or needs reproduction. It does not certify the robot.

### Driver-Assistance Or Tesla-Like Example

Do not claim that ClaimBound controls or certifies Tesla vehicles. Use this only as a generic pattern for AI-assisted vehicle software or public autonomy claims.

Bad broad claim:

```text
The car can drive itself safely.
```

ClaimBound versions:

```text
The public owner-facing documentation for feature X states the required human supervision boundary and was source-audited by URL, access date, expected markers and hash.
```

```text
In scenario fixture VEH-ODD-FOG-002, build X disabled lane-follow actuation outside the frozen operational design domain and logged the disable event with the required fields.
```

```text
In takeover fixture VEH-TAKEOVER-001, the driver-monitoring warning path triggered within the frozen time limit and the sanitized log contains the required intervention fields.
```

These are useful because they stop a reader from jumping from “one source or scenario passed” to “the system is generally autonomous or safe.”

## AI Security And Hacker-Resistance

ClaimBound protects AI-assisted software mostly by reducing trust in unchecked model output. It is not a firewall, antivirus or exploit mitigation.

Good uses:

- require AI-generated code to pass fixed tests, linters and security scans before a card can pass;
- hash prompts, fixtures, source files, reports and artifacts so later tampering is visible;
- record the model/API/tool identity used for an AI-assisted run;
- block evidence when commands, logs, model identity or source rights are missing;
- keep raw secrets, restricted transcripts and private payloads out of the public repository;
- require human approval for final status and publication;
- tombstone failed or compromised branches instead of silently reusing them.

Example security claims:

```text
For AI-agent patch SEC-AGENT-001, the frozen command set completed with no high-severity findings from the selected scanner, no protected deployment-path changes and a reviewed sanitized report.
```

```text
For prompt-injection fixture set LLM-PI-001, the agent produced no unauthorized filesystem, network or shell tool call under the frozen allowlist and validator.
```

```text
For dependency update DEP-SUPPLY-001, the lockfile diff, package manager metadata and test logs were recorded and the card does not claim the dependency is vulnerability-free.
```

## Recommended Workflow

```text
1. Convert the broad AI risk into one narrow claim.
2. Write forbidden inferences before the run.
3. Freeze source, model, prompt, fixture, command, environment, scorer and gate.
4. Decide the smallest stack: card only, card + v2, or card + v2 + v3.
5. Run deterministic checks or a manual no-AI checklist.
6. Store raw sensitive artifacts outside the public repo and publish only hashes/summaries.
7. Assign the exact status: passed, negative, blocked, insufficient or reproduced.
8. Publish the card only if the limitation boundary is explicit.
9. Use v2/v3 to keep failed, blocked and related branches visible.
```

## Mapping To Common AI Governance Language

ClaimBound is compatible with risk-management frameworks because it produces small reviewable records. For example:

| Governance need | ClaimBound artifact |
| --- | --- |
| Govern | Policy boundary, human approval, prohibited AI actions, disclosure of AI assistance. |
| Map | Source boundary, model/prompt/fixture inventory, operational design domain, affected audience. |
| Measure | Frozen scorer, checklist, command path, logs, hashes and exact result status. |
| Manage | Stop rules, tombstones, blocked-source records, reproduction level and registry entry. |

## References And Standards Context

These references are context only; ClaimBound does not claim compliance with them by default.

- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI RMF Generative AI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- OWASP LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- ISO 10218 industrial robot safety requirements: https://www.iso.org/standard/73933.html

## Core Rule

Use ClaimBound to make AI claims smaller, harder to fake, harder to silently change and easier to challenge.

Do not use ClaimBound to say that an AI, robot, vehicle or software system is safe unless that exact safety claim, source boundary, scenario, protocol, result status and limitation were actually checked.
