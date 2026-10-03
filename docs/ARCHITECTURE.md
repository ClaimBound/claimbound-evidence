# Architecture

This document describes the released ClaimBound Evidence system as a set of actors and actions. It is intentionally limited to the public repository and its documented release/validation paths.

## Actors and subsystems

| Actor / subsystem | Can influence | Actions |
|---|---|---|
| Human contributor | Source tree and pull requests | Creates commits, opens PRs, adds tests/docs/cards and responds to review |
| Maintainer | Protected repository, releases and security handling | Reviews/merges PRs, manages repository configuration, tags/releases, handles vulnerabilities |
| GitHub repository | Source and protected integration state | Stores source, issues, PRs, releases, rulesets and workflow definitions |
| GitHub Actions | Build/test/release outputs | Runs checkout, dependency installation, validation, tests, package build, attestation and publication workflows |
| Python package tooling | Build artifacts | Builds the Python sdist and wheel from repository state |
| ClaimBound CLI | Evidence files supplied by an operator | Validates cards, registry data and repository-level evidence according to implemented protocols |
| Evidence registry | Public metadata index | Maps published evidence identifiers to validated card JSON and metadata |
| External source / artifact | Input to an evidence run | Supplies public source material or an artifact whose boundary is recorded by a card |
| PyPI Trusted Publishing | Published Python packages | Receives release artifacts from the protected GitHub Actions workflow using OIDC |

## Main actions and data flow

### Evidence validation

1. An operator supplies a ClaimBound card, registry entry or supported evidence input.
2. The ClaimBound CLI reads the declared protocol, source boundary, hashes and result fields.
3. Validators check the applicable schema, protocol constraints and cross-file relationships.
4. The CLI reports a validation result; it does not grant certification or make a general quality/safety determination.
5. Maintainers may review the resulting change through the normal pull-request process.

### Repository contribution

1. A contributor creates commits and signs each commit under the DCO.
2. A pull request triggers automated checks, including DCO, dependency review and tests.
3. Required checks and repository review rules govern acceptance into main.
4. A maintainer merges the pull request.

### Release

1. A maintainer publishes a GitHub Release.
2. The release workflow checks out the tagged repository state and builds the Python distribution artifacts.
3. The workflow generates SHA-256 hashes for the build artifacts.
4. GitHub artifact attestations are generated for the artifacts and release manifest.
5. The release assets and hash manifest are uploaded to the GitHub Release.
6. PyPI publication uses OIDC Trusted Publishing rather than a long-lived PyPI token.

## Trust boundaries

- Public source and issue/PR content are untrusted contributor input.
- Evidence source material is treated according to the source boundary declared by the evidence card; raw/private payloads are outside the public repository boundary.
- GitHub Actions workflows are privileged automation and therefore use explicit job permissions.
- Release publication and repository administration are maintainer-controlled operations.
- PyPI is an external package distribution service; ClaimBound does not control downstream installations or environments.

## Update rule

Update this document when a new subsystem, external service, privileged workflow action, public interface or material data flow is introduced, or when a breaking change alters the actors/actions described above.
