# Maintainers

ClaimBound is currently maintained by one project participant.

| Participant | GitHub account | Role | Sensitive resources |
|---|---|---|---|
| Rostyslav Shcherbyna | [@NeoZorK](https://github.com/NeoZorK) | Project maintainer / release maintainer | GitHub repository administration, branch/ruleset administration, GitHub Actions workflow configuration, GitHub Releases, PyPI Trusted Publishing configuration, and security-advisory handling |

## Access boundary

The maintainer is the only currently documented human with administrative or release access to the project's sensitive resources.

The public repository does not contain long-lived PyPI credentials. Release publication uses GitHub Actions OpenID Connect (OIDC) Trusted Publishing. Repository secrets and environment protections, where configured by GitHub, are administrative resources rather than source-controlled project data.

Contributors do not receive direct access to protected release or repository-administration resources merely by submitting a pull request.

This file must be updated when another person receives administrative, release, security-advisory, or other sensitive-resource access.

## Giving access

Collaborators are reviewed before they receive escalated permissions to sensitive resources
(repository administration, rulesets, workflow configuration, releases, package-registry and
security-advisory access).

1. A contributor first works only through pull requests from a fork or branch; submitting a
   pull request never gives access.
2. Before access is escalated, a maintainer reviews the contributor's history in the
   project: accepted contributions, adherence to the [DCO](DCO.md) and the contribution
   rules, and conduct under the [Code of Conduct](CODE_OF_CONDUCT.md).
3. The person must have two-factor authentication enabled (the organization enforces it).
4. Access is the minimum the role needs, is given by an existing maintainer with access to
   those resources, and is recorded in the table above in the same change.
5. Access is removed, and any shared secrets rotated (see the
   [secrets policy](docs/SECRETS_POLICY.md)), when a person no longer needs it.

Today no one other than the maintainer listed above has such access.

## Limitations and continuity

**One maintainer, no independent review.** The project is run by a single person. Changes are
not approved by a second human reviewer: the maintainer merges their own pull requests using
the repository-administrator bypass of the main ruleset. For that reason the project does not
claim OpenSSF Baseline Level 3 (criterion OSPS-QA-07.01 is answered "Unmet"), and the
Scorecard `Code-Review` check stays at 0. No second maintainer or reviewer is planned, and
none is simulated.

**What replaces review.** Automatic checks gate every change to `main`: the test suite on
Linux and Windows (macOS and Python 3.14 run as additional checks), the dependency review, the
DCO sign-off check and CodeQL, which blocks a pull request that introduces a high-severity or
error-level alert; `ruff` runs with the tests. These checks catch mechanical problems; they do
not replace a second pair of eyes, and the project does not present them as if they did.

**Continuity.** The code is licensed under Apache-2.0, so anyone may fork and continue it.
Releases are built by a public workflow, and the package is also distributed through
conda-forge. If the maintainer can no longer maintain the project, the intent is to say so in
the README and archive the repository rather than leave it looking active. Update this
section when another person gets access (see "Giving access" above).

