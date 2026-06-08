# Governance

ClaimBound is currently a single-maintainer open-source repository. Governance
is intentionally lightweight so that the public evidence workflow stays
inspectable and reproducible.

## Maintainer Responsibilities

The maintainer is responsible for:

- keeping the evidence-card schema and validators coherent;
- reviewing changes to public card status, claim boundaries and registry
  entries;
- preserving raw-payload and private-data boundaries;
- keeping documentation clear about what a card proves and does not prove;
- tagging releases when the public workflow changes materially.

## Evidence Decisions

Evidence status is determined by protocol, source boundary, artifacts,
validator output and documented limitations. It is not determined by votes,
popularity, award interest or maintainer preference.

Requests and scaffolds are not evidence. A result becomes public evidence only
after:

1. the protocol or checklist is frozen;
2. the run or manual check is completed;
3. sanitized artifacts and hashes are recorded;
4. the evidence card validates;
5. the registry entry is updated.

## External Contributions

External contributors can help by:

- opening evidence requests;
- reporting source drift;
- rerunning existing cards;
- improving validators, docs and examples;
- challenging claim boundaries when a card appears too broad or unclear.

The maintainer may decline or narrow a request when the source is private,
ambiguous, unsafe to publish, too broad or outside the public repository
boundary.

## Non-Goals

This repository does not provide:

- legal, procurement, compliance, award or investment decisions;
- certification;
- model rankings by default;
- hosted review services;
- guaranteed turnaround for third-party checks.

