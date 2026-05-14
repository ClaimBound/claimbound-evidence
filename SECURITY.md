# Security Policy

## Supported Versions

ClaimBound Public Benchmarks is currently pre-1.0 public research tooling. Security fixes are applied to the default branch and to the latest tagged release when practical.

| Version | Supported |
| ------- | --------- |
| Latest `main` | Yes |
| Latest tagged release | Yes |
| Older releases | No, unless a severe issue affects public users |

## Reporting a Vulnerability

Please report suspected vulnerabilities privately through GitHub Security Advisories:

<https://github.com/ClaimBound/claimbound-public-benchmarks/security/advisories/new>

Do not open a public issue for vulnerabilities involving:

- dependency compromise;
- CI or GitHub Actions permissions;
- repository publication guard bypasses;
- accidental exposure of raw payloads, local paths, credentials, tokens, or private-source material;
- unsafe handling of operator-supplied files.

## Expected Response

I aim to acknowledge valid reports within 7 calendar days. If the report is accepted, I will try to provide a fix, mitigation, or documented decision within 30 calendar days, depending on severity and available maintainer time.

If the report is declined, I will explain the reason where possible.

## Project-Specific Boundaries

This repository is public ClaimBound benchmark foreground. It must not contain raw external payloads, credentials, private local paths, private-source code, or private production integrations.

Security reports about private systems, private-source implementations, or unrelated infrastructure are out of scope for this public repository unless they demonstrate a direct leak or vulnerability in the public benchmark code.

## Safe Handling Notes

When reproducing benchmarks:

- keep raw payloads outside the repository;
- publish hashes, manifests, summaries, and claim boundaries only;
- do not include access tokens, cookies, API keys, or private local paths in reports;
- verify generated artifacts before committing.

## Provenance And Audit-Log Handling

Funding evidence bundles, GitHub organization audit-log exports, AI session logs
and private reviewer materials may contain account metadata, private messages,
local paths or sensitive operational details. Do not commit those raw exports to
this public repository.

Use public PRs, commits, releases, GitHub Actions runs, evidence cards and the
registry as the public provenance trail. Store any raw audit-log export only in a
private funding archive, redact before sharing externally and publish hashes or
public URLs instead of private logs where possible.

If an audit-log export, AI transcript, raw payload, token, private path or
private-source detail is accidentally committed or disclosed, report it through
GitHub Security Advisories:

<https://github.com/ClaimBound/claimbound-public-benchmarks/security/advisories/new>
