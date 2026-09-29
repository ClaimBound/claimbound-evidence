# Glossary

Short definitions of the terms used across cards, the registry and the CLI.
Exact field rules live in the [evidence card protocol](EVIDENCE_CARD.md) and the
[result status protocol](RESULT_STATUS.md).

| Term | Meaning |
| --- | --- |
| **Claim** | A narrow public statement that can be checked against a public source, for example "this documentation page lists these models". |
| **Evidence card** | A small JSON record (with an SVG rendering) that documents one check of one claim: protocol, source, hashes, result, boundary and reproduction level. |
| **Protocol (charter)** | The written rules of a check, frozen before the result is known: source, method, gate and acceptance rule. |
| **Frozen** | Fixed and hashed before the run. A frozen protocol or source is never swapped after seeing the result. |
| **Gate** | The pass/fail condition of the protocol. |
| **Claim boundary** | The plain-language limit of what the card shows. A pass never extends beyond it. |
| **Source audit** | A check that a public source was reachable, had the expected markers and hashed to a recorded value. It is not a check that the source's statements are true. |
| **`result_status`** | The gate outcome: `PASSED_UNDER_PROTOCOL`, `NEGATIVE_RESULT_UNDER_PROTOCOL`, `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE` or `REPRODUCED_OUTCOME`. |
| **`PASSED_UNDER_PROTOCOL`** | One narrow claim passed the frozen gate. It is not a general quality, safety or compliance statement. |
| **`BLOCKED_SOURCE`** | Access, rights, metadata or lineage were not good enough for a fair verdict. First-class evidence, not a failure to hide. |
| **`INSUFFICIENT_COVERAGE`** | The source exists but is too sparse or uneven for the pre-registered test. |
| **`reproduction_level`** | How far a rerun has confirmed the outcome: `not independently reproduced`, `REPRODUCED_OUTCOME`, `REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT`. |
| **Source-byte drift** | A rerun reached the same gate outcome, but the fresh source bytes differ from the original ones. Shown as a yellow reproduction chip, never as a failed gate. |
| **`verification_level`** | Verification strength: `SINGLE_OPERATOR`, `SINGLE_OPERATOR_RERUN`, `INDEPENDENT_RERUN`, `MULTI_OPERATOR`, `NOT_EXECUTED`. |
| **`SINGLE_OPERATOR`** | One operator ran it. Most public cards are at this level until someone else reruns them. |
| **`execution_mode`** | Provenance: `MANUAL_NO_AI` or `AUTOMATED_AI_ASSISTED`. It does not make a result more or less valid. |
| **Operator** | The person or handle that ran a check. |
| **Rerun / reproduction attempt** | A later run of the same frozen protocol, recorded as its own card that links back to the original. |
| **Registry** | `docs/registry/evidence_index.json`: sanitized metadata and hashes of all cards. It never stores raw payloads. |
| **Raw payload** | The downloaded source bytes. Kept locally (`raw_payload_committed: false`), only hashes are published. |
| **Run root** | A local-only folder with standard subfolders for raw data, logs, hashes and reports, created by `claimbound run-root`. |
| **Artifact-only record** | A summary kept in the artifacts catalog that is not (yet) a registry card. |
| **Pseudonymous subject** | A confidential method or model referred to by a `SUBJ-…` identifier; see the [pseudonym policy](PSEUDONYM_POLICY.md). |
