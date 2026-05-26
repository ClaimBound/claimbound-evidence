# EEA AQ D-001 AI-Assisted Autonomous Prompt

This document is the autonomous AI-assisted version of the EEA AQ D-001 track.
It intentionally contains one operator prompt instead of a long manual runbook.

Use this file when you want an AI coding agent to execute the track end to end
under ClaimBound rules, while preserving honesty, reproducibility, source
boundaries, raw-payload separation, and exact result-status reporting.

If an operator wants a step-by-step human workflow, use
[docs/manual_audit/EEA_AQ_D001_MANUAL_TRACK.md](EEA_AQ_D001_MANUAL_TRACK.md).

## When To Use This File

Use this prompt only when the AI agent can:

- read and edit the local repository;
- create external working folders outside the repository;
- run shell commands;
- download or instruct the operator to download official source data;
- run Python locally;
- produce sanitized public artifacts;
- run tests;
- show exact changed files.

Do not use this prompt when the AI assistant is only a chat window with no
local filesystem, no terminal, and no way to verify command output.

## One Prompt To Give The AI Agent

Copy the full prompt below into the AI agent. Do not edit the fixed scope.

```text
You are operating inside the ClaimBound evidence repository.

Your task is to run or prepare the EEA AQ D-001 AI-assisted ClaimBound track
honestly, reproducibly, and without broadening the claim.

You must follow these non-negotiable rules:

1. The result must be honest.
2. A blocked, negative, or insufficient-coverage result is a valid result.
3. Do not optimize the protocol for a positive outcome.
4. Do not change the fixed scope after source data or outcome data is inspected.
5. Do not choose favorable stations after seeing coverage.
6. Do not lower the coverage gate.
7. Do not fabricate source-rights notes.
8. Do not fabricate hashes.
9. Do not fabricate command output.
10. Do not commit raw payloads.
11. Do not commit full AI transcripts.
12. Do not make forecasting-performance, deployment-readiness,
    health-impact, model-superiority, or broad environmental claims.
13. If source access, source rights, file format, or required metadata is
    unclear, record `BLOCKED_SOURCE`.
14. If data is readable but the fixed coverage gate does not pass, record
    `INSUFFICIENT_COVERAGE`.
15. If the source is accessible, rights are acceptable for sanitized public
    evidence, and all fixed countries pass the gate, record
    `PASSED_UNDER_PROTOCOL`.
16. If an accessible source produces a legitimate non-passing outcome not better
    represented by insufficient coverage, record `NEGATIVE_RESULT_UNDER_PROTOCOL`.

Fixed scope:

- Track ID: EEA_AQ_D001
- Claim type: source audit
- Official source: EEA Air Quality Download Service
- Dataset: verified E1a data
- Pollutant: PM10
- Countries: NL, BE, DE
- Period: 2018-01-01 through 2024-12-31
- Aggregation: daily records
- Coverage gate: at least 85 percent daily coverage per sampling point
- Selection rule: first five eligible sampling points per country after sorting
  by country code, city/locality if available, and sampling point ID
- Raw payload policy: raw files stay outside the repository
- Public output policy: commit only sanitized summary, evidence card JSON,
  evidence card SVG, registry updates, and documentation changes
- Execution mode: AUTOMATED_AI_ASSISTED

Official source references to use:

- EEA AQ Portal download page:
  https://aqportal.discomap.eea.europa.eu/download-data/
- Air Quality Download web application:
  https://eeadmz1-downloads-webapp.azurewebsites.net/
- Air Quality Download API Swagger:
  https://eeadmz1-downloads-api-appservice.azurewebsites.net/swagger/index.html
- Air Quality Download documentation PDF:
  https://eeadmz1-downloads-webapp.azurewebsites.net/content/documentation/How_To_Downloads.pdf
- EEA copyright notice:
  https://www.eea.europa.eu/en/about/policy/copyright
- EEA reuse FAQ:
  https://www.eea.europa.eu/en/about/contact-us/faqs/can-i-use-eea-content-in-my-work-or-in-my-organisations-products

Required workflow:

1. Inspect the repository first.
2. Read these project rules before running the track:
   - docs/RESULT_STATUS.md
   - docs/CLAIMS.md
   - docs/EVIDENCE_CARD.md
   - docs/MANUAL_AUDIT_PROTOCOL.md
   - docs/AI_OPERATOR_PROTOCOL.md
   - docs/DATA_POLICY.md
3. Confirm the git worktree state.
4. If unrelated local changes exist, do not overwrite or revert them.
5. Create an external run root outside the repository:
   `$HOME/claimbound_runs/eea_aq_d001_ai_<UTC_DATE>`.
6. Inside the external run root, create:
   - raw/
   - downloads/
   - hashes/
   - logs/
   - reports/
   - scripts/
   - work/
   - ai/
7. Create `logs/operator_log.md`.
8. Create `logs/protocol_lock.txt` with the fixed scope above.
9. Hash `logs/protocol_lock.txt`.
10. Open or fetch the official source references only from the URLs above.
11. Record source access notes in `logs/operator_log.md`.
12. Decide whether sanitized public summaries are acceptable under the source
    boundary. Do not claim raw payload redistribution unless the official source
    clearly allows it.
13. If source rights are unclear, stop and prepare a `BLOCKED_SOURCE` result.
14. Download or instruct the human operator to download verified E1a PM10 daily
    records for NL, BE, DE from 2018-01-01 through 2024-12-31.
15. Store downloaded raw files only under the external run root.
16. Never copy raw parquet, raw CSV payload, ZIP payload, secrets, tokens, or
    private browser screenshots into the repository.
17. Hash raw payload files and hash the raw hash manifest.
18. Build or reuse a local parser that:
    - reads parquet and CSV files from the external run root;
    - identifies sampling point, pollutant, start datetime, value, unit,
      aggregation, country, and city/locality columns where available;
    - filters to PM10;
    - filters to countries NL, BE, DE;
    - filters to 2018-01-01 through 2024-12-31;
    - uses daily records when an aggregation field is present;
    - computes observed unique days per sampling point;
    - computes expected days for the fixed period;
    - applies the 85 percent coverage gate;
    - sorts by country, city/locality if available, and sampling point ID;
    - selects the first five eligible sampling points per country;
    - writes station coverage CSV outside the repository;
    - writes selected sampling points CSV outside the repository;
    - writes a sanitized summary JSON outside the repository.
19. The sanitized summary must include:
    - schema name;
    - track ID;
    - execution mode;
    - official source name and URLs;
    - fixed scope;
    - raw_payload_committed: false;
    - by-country counts;
    - selected sampling point IDs;
    - exact result_status;
    - exact reason;
    - claim boundary;
    - known limitations.
20. Do not include raw payload rows in the public sanitized summary.
21. Derive the result status from deterministic processing and source-rights
    checks, not from AI opinion.
22. Copy only the sanitized summary JSON into the repository under artifacts/.
23. Create a ClaimBound evidence card JSON under docs/evidence_cards/.
24. Set `execution_mode` to `AUTOMATED_AI_ASSISTED` only if you completed or
    prepared the AI track under this protocol and deterministic validation
    produced the status. If a human must perform source-download or source-access
    steps manually, stop with a blocker or switch to the manual track instead of
    creating a third execution mode.
25. The evidence card must disclose that AI assistance was used.
26. The evidence card must state that AI did not have authority to change the
    gate, select favorable stations, fabricate hashes, or broaden the claim.
27. Validate the evidence card with the repository validator.
28. Create a visual SVG card from docs/assets/claimbound_evidence_card.svg.
29. Update docs/registry/evidence_index.json if a completed public card is
    added.
30. Run local tests.
31. Scan for accidental raw payload files before staging.
32. Scan for unsupported broad claims.
33. Show the final git diff.
34. Commit only intended public files.
35. If pushing and opening a PR is available, create a PR and wait for checks.
36. If checks fail, fix the real issue without changing the result status unless
    the status was objectively computed incorrectly.

Required output from you:

1. List the exact external run root used.
2. List the public files changed.
3. State the exact result status.
4. State whether raw payloads were committed. The expected answer is no.
5. State whether AI changed the gate after seeing results. The expected answer
   is no.
6. State whether AI selected favorable stations after seeing coverage. The
   expected answer is no.
7. State whether the evidence card validator passed.
8. State whether tests passed.
9. State any blockers or deviations honestly.
10. If you could not complete the run, produce the best honest blocked summary
    and explain the next exact command or human action needed.
```

## Expected Public Artifacts

If the run completes, the public repository should contain only sanitized
artifacts such as:

```text
artifacts/eea_aq_d001_ai_assisted_summary.json
docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-AI-YYYY-MM-DD.json
docs/evidence_cards/CLAIMBOUND-EEA-AQ-D001-AI-YYYY-MM-DD.svg
docs/registry/evidence_index.json
```

Raw payloads, full AI transcripts, downloaded ZIP files, downloaded parquet
files, and private browser screenshots must stay outside the repository.

## Minimal Public Disclosure

Use this disclosure in the evidence card or PR body:

```text
AI assistance was used to execute or prepare the EEA AQ D-001 track under a
fixed ClaimBound protocol. AI was not allowed to change the fixed scope after
source or outcome inspection, choose favorable stations, lower gates, fabricate
hashes, fabricate source-rights notes, alter raw payloads, or broaden the claim
boundary.
```
