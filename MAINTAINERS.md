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

## Granting access

Collaborators are reviewed before they receive escalated permissions to sensitive resources
(repository administration, rulesets, workflow configuration, releases, package-registry and
security-advisory access).

1. A contributor first works only through pull requests from a fork or branch; submitting a
   pull request never grants access.
2. Before access is escalated, a maintainer reviews the contributor's history in the
   project: accepted contributions, adherence to the [DCO](DCO.md) and the contribution
   rules, and conduct under the [Code of Conduct](CODE_OF_CONDUCT.md).
3. The person must have two-factor authentication enabled (the organization enforces it).
4. Access is the minimum the role needs, is granted by an existing maintainer with access to
   those resources, and is recorded in the table above in the same change.
5. Access is removed, and any shared secrets rotated (see the
   [secrets policy](docs/SECRETS_POLICY.md)), when a person no longer needs it.

Today no one other than the maintainer listed above has such access.

