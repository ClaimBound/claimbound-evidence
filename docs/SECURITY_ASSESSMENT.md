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

## Highest-priority risks

1. **Supply-chain integrity:** release build and publication are privileged operations. The release workflow therefore uses constrained permissions, OIDC Trusted Publishing and artifact attestations.
2. **Sensitive-data disclosure:** the project handles evidence about public sources and deliberately excludes raw private payloads. Documentation and review are the primary controls.
3. **Integrity of evidence semantics:** validators can establish only the documented protocol result. Claim boundaries and non-goals are treated as part of the security and trust model.
4. **Repository compromise:** protected branches, required checks, maintainer access controls and private vulnerability reporting reduce the impact of unauthorized changes.

## Assessment scope and limitations

This assessment is based on the repository architecture and released workflows. It does not include a penetration test, dependency source-code audit, GitHub infrastructure audit, PyPI infrastructure audit, or independent cryptographic review.

## Update triggers

Reassess this document when a new privileged workflow, network service, authentication mechanism, package-publication path, persistent data store, public API, or materially different evidence-processing component is introduced. Also reassess it for security-relevant breaking changes.
