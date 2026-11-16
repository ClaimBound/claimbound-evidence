# Related Work And Independence

Status: public positioning note. It is not a novelty claim, a legal opinion or an affiliation statement.

Protocolith was published under the name **ClaimBound Evidence** until version 0.5.0 (2026-11-06). The name was
changed because two unrelated works use a very similar name (see below) and the project did not want to be mistaken
for either of them. Old releases stay on PyPI and in git history under the old name.

## What Protocolith Is

Protocolith records, verifies and issues trial records: a protocol is frozen before a run, the outcome is recorded
against it, the history is verified, and a card can be issued. The core is specified in
[spec/CORE_SPEC.md](spec/CORE_SPEC.md). It does not run experiments, manage agents or answer questionnaires.

## Unrelated Works With Similar Names

| Work | What it is | Relation to Protocolith |
| --- | --- | --- |
| [EviBound](https://arxiv.org/abs/2511.05524) ("Evidence-Bound Autonomous Research (EviBound): A Governance Framework for Eliminating False Claims", arXiv, 2025) | A governance framework for autonomous AI research agents: acceptance criteria are checked before code runs, and results are confirmed through MLflow run records. | None. Not a fork, not derived from it, not affiliated. The paper was found after development of this project had started. |
| claimbound.com | A commercial service that helps companies answer the AI sections of enterprise security questionnaires with evidence-linked claims. | None. A different product with a similar name, not affiliated, not endorsed. |
| [metahub-ai/assay](https://github.com/metahub-ai/assay) | An open project that inspects and audits AI artifacts such as skills, MCP servers and agents. | Neighbouring area, different object and mechanism. Not affiliated. |

Similarity of names or of the words "evidence" and "claim" does not imply a shared product, team or code.

## Scope Split

| Dimension | EviBound | Protocolith |
| --- | --- | --- |
| Primary object | Execution of autonomous research agents. | A ledger of frozen protocols and recorded trial outcomes. |
| Main problem | Agents reporting completed tasks without machine-checkable artifacts. | Results reported without a protocol that was fixed beforehand, or broader than their evidence. |
| Mechanism | Acceptance gates before and after code execution, MLflow verification. | Canonical JSON, a hash-chained ledger, a closed vocabulary of result statuses, issued cards. |
| Reader | Teams building research agents. | Anyone who runs local experiments and wants a checkable record. |

Do not describe Protocolith as derived from EviBound, and do not claim priority over it.

## What Can Be Shown About Independence

- The git history of this repository starts on 2026-04-29 and is kept unchanged.
- No code, text or schema of the works above was copied; the mechanisms differ as shown in the table.
- Fixing a protocol before a run is an established practice (pre-registration, registered reports); neither this
  project nor the works above own it.
- Development of this project used AI assistance; the disclosures are in [AI_USE.md](AI_USE.md) and
  [AI_PROVENANCE_LOG.md](AI_PROVENANCE_LOG.md) and are kept truthful.
- The project makes no priority or novelty claim.

## Canonical Home

The canonical source is [github.com/protocolith/protocolith](https://github.com/protocolith/protocolith); documentation is
on [protocolith.github.io/protocolith](https://protocolith.github.io/protocolith/). Other repositories, sites or
services using a similar name are not this project.

## Archived State Before The Rename

The repository state under its former name (ClaimBound Evidence, `github.com/ClaimBound/claimbound-evidence`) was archived by Software Heritage
on 2026-11-16, before the repository was moved. This is an independent timestamp of the earlier name, history and content:

- Snapshot: `swh:1:snp:6d2917c2ed88f1e41d7270dcd17570f32500dbf7`
- Revision: `swh:1:rev:842d5897af940acdce39da23c356a18077e0587d`
- Directory: `swh:1:dir:c1b1d320d52d7554118fb7d576703164068a7339`
- [Browse the archived origin](https://archive.softwareheritage.org/swh:1:dir:c1b1d320d52d7554118fb7d576703164068a7339;origin=https://github.com/ClaimBound/claimbound-evidence;visit=swh:1:snp:6d2917c2ed88f1e41d7270dcd17570f32500dbf7;anchor=swh:1:rev:842d5897af940acdce39da23c356a18077e0587d)
