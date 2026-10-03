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
