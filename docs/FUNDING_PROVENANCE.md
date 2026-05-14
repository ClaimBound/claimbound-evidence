# Funding Provenance And Audit Logs

This note defines how ClaimBound Public Benchmarks should present development
provenance for funding reviews and public accountability.

## Short Answer

The GitHub organization audit log is not an AI provenance log.

Use it as supporting governance evidence only: repository settings changes,
ruleset changes, permission changes, security-adjacent events and other
organization-level activity.

The primary project provenance is the public development trail:

- merged pull requests;
- commit SHAs and release tags;
- GitHub Actions check results;
- evidence cards and registry entries;
- documented AI assistance fields in evidence cards;
- human-reviewed PR descriptions and linked issues or discussions.

## Public Provenance Sources

For funding-facing reports, cite public records first:

| Source | What it proves | Where |
| --- | --- | --- |
| Pull requests | What changed, why it changed, review/check status and discussion context. | GitHub PR URLs. |
| Commits | Exact repository state and file history. | Commit SHA links. |
| Releases and tags | Stable public snapshots for milestones. | GitHub Releases and tags. |
| GitHub Actions | Tests and dependency review ran on a branch or PR. | Workflow run URLs. |
| Evidence cards | Protocol, source boundary, status, AI assistance, reproduction level and limitations. | `docs/evidence_cards/` and `docs/registry/evidence_index.json`. |
| Project docs | The rules under which AI, manual review, raw payload boundaries and publication happen. | `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/AI_WORKFLOW.md`, `docs/AI_OPERATOR_PROTOCOL.md`. |

These public records are safer and more useful for reviewers than private audit
exports because they are reproducible from the repository itself.

## Private Funding Evidence Bundle

If a funding reviewer requests additional provenance, prepare a private bundle
outside this public repository.

Suggested private layout:

```text
funding-evidence/
  claimbound-public-benchmarks/
    2026-05-14/
      README.md
      public-pr-index.csv
      release-and-tag-index.txt
      action-run-index.csv
      evidence-card-index.json
      github-org-audit-log-repo-filtered.json
      SHA256SUMS
```

The private bundle may include:

- exported GitHub organization audit-log rows filtered to
  `repo:ClaimBound/claimbound-public-benchmarks`;
- a dated list of public PRs, commits, releases and workflow runs;
- a digest of the evidence-card registry;
- sanitized AI-work summaries when they are relevant to funding reporting.

Do not include raw payloads, credentials, private local paths, personal account
screenshots, private messages, full AI chat transcripts or private-source
implementation details in this public repository.

## GitHub Audit Log Use

Use the organization audit log for governance questions, not claim evidence.

Appropriate uses:

- showing when branch protection or rulesets changed;
- showing repository visibility or permission changes;
- showing security or advisory configuration events;
- supporting an internal timeline of repository administration.

Inappropriate uses:

- proving what an AI assistant wrote;
- proving that a benchmark result is valid;
- replacing PRs, commits, tests, evidence cards or signed release artifacts;
- publishing raw audit-log exports in the public repository.

GitHub documents that organization audit logs are accessible to organization
owners, list organization actions for a limited retention window and can be
exported as JSON or CSV from the audit-log UI. GitHub also documents audit-log
API access, but API availability and retention depend on plan and permissions.

Useful reference:

<https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/reviewing-the-audit-log-for-your-organization>

For the ClaimBound organization UI, use:

<https://github.com/organizations/ClaimBound/settings/audit-log?q=repo%3AClaimBound%2Fclaimbound-public-benchmarks>

## Recommended Funding Reporting Pattern

For each reporting period:

1. Create a public milestone summary with PR links, commit SHAs, release tags
   and evidence-card links.
2. Export a private, repo-filtered GitHub audit log only if needed.
3. Redact sensitive fields before sharing outside maintainers.
4. Hash the private bundle and record the hash in the private funding archive.
5. Submit public URLs plus private bundle hashes, not raw private logs, unless
   the reviewer explicitly requires the raw export.

This keeps the public project auditable without leaking private operational or
account metadata.
