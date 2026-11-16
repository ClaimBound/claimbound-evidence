# Archive and examples

Before the core ledger, this project was a toolkit for evidence cards about narrow public claims, published under
the name ClaimBound Evidence until 0.5.0. That material still works and is kept, not deleted. It is listed here
so the main documentation can stay focused on the core. See
[related work and independence](../RELATED_WORK_AND_INDEPENDENCE.md) for the rename.

None of these pages describe the ledger commands. Cards produced by the older runners were not created through
the ledger and cannot be verified with `verify-ledger`.

## Evidence cards and the registry

| Topic | Page |
| --- | --- |
| What an evidence card is, every field | [EVIDENCE_CARD](../EVIDENCE_CARD.md) |
| Result status protocol v0.1 | [RESULT_STATUS](../RESULT_STATUS.md) |
| Common misreadings of cards | [COMMON_MISREADINGS](../COMMON_MISREADINGS.md) |
| Glossary | [GLOSSARY](../GLOSSARY.md) |
| Pseudonym policy | [PSEUDONYM_POLICY](../PSEUDONYM_POLICY.md) |
| Registry views (generated, static) | [REGISTRY_VIEWS](../REGISTRY_VIEWS.md) |
| Registry folder (index of cards) | [docs/registry](../registry/) |
| Evidence cards (JSON and SVG) | [docs/evidence_cards](../evidence_cards/) |
| Case studies | [docs/case_studies](../case_studies/) |
| Current evidence tracks | [CURRENT_EVIDENCE_TRACKS](../CURRENT_EVIDENCE_TRACKS.md) |

## Reading cards, reruns and reviewing

| Topic | Page |
| --- | --- |
| Reading a card (card-level quick start) | [Quick start](../../docs_site/quickstart.md), [Reading a card](../../docs_site/concepts.md) |
| Install the card-level tools | [Install (card tools)](../../docs_site/install.md) |
| Start without coding | [START_WITHOUT_CODING](../START_WITHOUT_CODING.md) |
| Independent rerun workflow | [INDEPENDENT_RERUN_WORKFLOW](../INDEPENDENT_RERUN_WORKFLOW.md) |
| Reviewer path and summary | [REVIEWER_PATH](../REVIEWER_PATH.md), [REVIEWER_SUMMARY](../REVIEWER_SUMMARY.md) |
| Protocolith in 30 seconds / 5 minutes (earlier wording) | [30 seconds](../PROTOCOLITH_IN_30_SECONDS.md), [5 minutes](../PROTOCOLITH_IN_5_MINUTES.md) |
| Getting started with cards and scaffolds | [GETTING_STARTED](../GETTING_STARTED.md) |
| Platform support of the older commands | [PLATFORM_SUPPORT](../PLATFORM_SUPPORT.md) |
| Earlier architecture description | [ARCHITECTURE](../ARCHITECTURE.md) |

## Campaign material and source runners

| Topic | Location |
| --- | --- |
| NASA POWER runners and atlas | [docs/nasa](../nasa/) |
| ESA atlas and 500-card heat map | [docs/esa](../esa/), [ESA_500_HEATMAP](../esa/ESA_500_HEATMAP.md) |
| Public-claim atlases and catalogues | [docs/public_claims](../public_claims/) |
| Evidence-card campaign drafts | [docs/evidence_card_drafts](../evidence_card_drafts/) |
| Track families and R&D family protocol | [docs/track_families](../track_families/), [R_AND_D_FAMILY_PROTOCOL](../R_AND_D_FAMILY_PROTOCOL.md) |
| Runbooks | [docs/runbooks](../runbooks/) |
| Source probe | [SOURCE_PROBE](../SOURCE_PROBE.md) |
| Examples (self-check forms) | [docs/examples](../examples/) |
| Scripts (runners, atlas builders) | [scripts/README.md](../../scripts/README.md) |

The NOAA CO-OPS and NASA POWER runners are modules of the package (`protocolith.noaa_coops_*`,
`protocolith.nasa_power_*`) and are reached through the older commands in the [command reference](../CLI.md).
