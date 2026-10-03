# Security Assessment

This assessment covers the public ClaimBound Evidence repository, its CLI validation paths, evidence-card data model, GitHub Actions workflows and release publication path. It is a lightweight threat assessment for the released software, not a penetration test or a formal security certification.

## Security objectives

- Prevent secrets, credentials and private source material from entering the public repository.
- Prevent contributor-controlled changes from silently bypassing required validation and review.
- Preserve integrity and provenance of released Python artifacts.
- Prevent evidence validation from being interpreted as certification, safety approval or general correctness.
- Keep vulnerability reports private until maintainers can assess and remediate them.

## Threat assessment

| Threat | Likelihood | Impact | Existing controls | Residual risk |
|---|---|---|---|---|
| Malicious or accidental secret/private-data commit | Medium | High | CONTRIBUTING.md and SECURITY.md prohibit secrets/raw private payloads; PR review and automated checks; public-repository boundary | A contributor can still intentionally attempt disclosure; repository monitoring and review remain necessary |
| Dependency or build-tool compromise | Medium | High | Locked dependencies, dependency review, Dependabot, isolated GitHub-hosted build, explicit workflow permissions | Upstream package compromise cannot be eliminated by ClaimBound alone |
| CI workflow privilege abuse | Low/Medium | High | Explicit job permissions, protected main, review requirements, release environment, OIDC Trusted Publishing | GitHub Actions and repository administration remain privileged trust boundaries |
| Tampered release artifact | Low | High | Release artifacts receive SHA-256 manifest entries and GitHub/Sigstore attestations; publication is performed by GitHub Actions | Downstream users must verify hashes/attestations to benefit from the control |
| Evidence-card or registry manipulation | Medium | Medium | Validation commands, tests, protected main, review, explicit claim boundaries and immutable release history | A malicious maintainer or compromised administrative account remains a trusted actor |
| Unsafe interpretation of validation output | Medium | High | Documentation explicitly states that ClaimBound is not certification and that narrow protocol passes do not imply general safety or quality | Downstream readers may still overgeneralize results |
| Public vulnerability disclosure before remediation | Low/Medium | Medium/High | SECURITY.md provides private GitHub Security Advisory reporting and response targets | No project can guarantee that all vulnerabilities are privately discovered |
| Malicious contribution with legal/licensing uncertainty | Low/Medium | Medium | DCO sign-off is required on every PR commit; license and contribution rules are documented | DCO is a contributor certification, not independent proof of authorship |

## Attack surface analysis

The released software is a Python command-line tool and library. It opens no network
listener, runs no server and has no authentication, user accounts or persistent data store.

| Entry point | Reachable by | Critical code path | Controls |
| --- | --- | --- | --- |
| Evidence-card and registry JSON files passed to `claimbound validate-card`, `validate-all`, `inspect` | Whoever supplies a file | JSON parsing and field validation in `evidence_card.py`, `registry.py` | JSON only (no pickle, `eval` or YAML object loading); field checks reject malformed cards; commands do not execute card content |
| Command-line arguments and paths | The local user | Path handling in `cli.py`, `scaffold.py` | Paths are resolved relative to the working directory; no shell is invoked (`subprocess` is called with an argument list) |
| Public-source fetchers (`nasa_power_fetch.py`, `noaa_coops_fetch.py`) | The local user running a rerun | HTTPS requests with a timeout to the NASA POWER and NOAA CO-OPS APIs | Fixed API base URLs; responses are parsed as data and stored locally; raw payloads are not committed |
| Helper scripts started through the CLI | The local user in a repository clone | `_run_script` in `cli.py` | Fixed script names under `scripts/`; arguments passed as a list |
| GitHub Actions workflows | Pull requests and releases | `publish.yml` (privileged), `pages.yml` | Top-level read-only permissions, job-level minimum privileges, no `pull_request_target`, actions pinned to commit SHAs, hash-locked build tools, OIDC publishing with artifact attestations |
| Dependencies | Supply chain | `numpy`, `pdfplumber`, `pypdf` | Lock file with hashes, Dependabot, dependency review, see [DEVELOPMENT.md](DEVELOPMENT.md) |

The largest remaining exposure is the input parsing of files supplied by third parties
(card JSON and the PDF/data files read by the helper scripts) and the release workflow. Both
are covered by the controls above, by CodeQL and by the tests.

## Highest-priority risks

1. **Supply-chain integrity:** release build and publication are privileged operations. The release workflow therefore uses constrained permissions, OIDC Trusted Publishing and artifact attestations.
2. **Sensitive-data disclosure:** the project handles evidence about public sources and deliberately excludes raw private payloads. Documentation and review are the primary controls.
3. **Integrity of evidence semantics:** validators can establish only the documented protocol result. Claim boundaries and non-goals are treated as part of the security and trust model.
4. **Repository compromise:** protected branches, required checks, maintainer access controls and private vulnerability reporting reduce the impact of unauthorized changes.

## Assessment scope and limitations

This assessment is based on the repository architecture and released workflows. It does not include a penetration test, dependency source-code audit, GitHub infrastructure audit, PyPI infrastructure audit, or independent cryptographic review.

## Update triggers

Reassess this document when a new privileged workflow, network service, authentication mechanism, package-publication path, persistent data store, public API, or materially different evidence-processing component is introduced. Also reassess it for security-relevant breaking changes.
