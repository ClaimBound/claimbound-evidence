# Secrets and credentials policy

This policy covers every secret or credential the project uses: tokens, keys, passwords
and signing material.

## What exists today

- The repository holds **no GitHub Actions secrets** and no long-lived package-registry
  credentials. Releases are published to PyPI and TestPyPI through OpenID Connect
  Trusted Publishing (`id-token: write`); the workflows use only the short-lived
  `GITHUB_TOKEN`.
- Deployment environments are `pypi`, `testpypi` and `github-pages`.
- Accounts with access to sensitive resources are listed in [MAINTAINERS.md](../MAINTAINERS.md).
  The GitHub organization requires two-factor authentication for all members.

## Storing

- Never commit a secret, key, token, password or private path. `.gitignore` excludes
  environment and key files; GitHub secret scanning and push protection are enabled.
- If a secret is ever needed by a workflow, store it as a GitHub encrypted secret scoped to
  the narrowest environment that needs it (never in the repository, issues or logs), and
  prefer OIDC or a short-lived token over a long-lived one.
- Local credentials stay on the maintainer's machine and in the operating-system keychain or
  a password manager, never in the working tree.

## Accessing

- Only the maintainers in [MAINTAINERS.md](../MAINTAINERS.md) may create, read or change
  secrets and environment settings.
- Workflows request the minimum `permissions:`; jobs that touch privileged credentials never
  run on code from untrusted pull requests (no `pull_request_target`).

## Rotating and revoking

- A secret that is introduced must be rotated at least once a year and whenever a maintainer
  with access leaves.
- A suspected exposure is handled at once: revoke the credential first, then replace it, then
  review the logs of the affected service. Report it through a private
  [GitHub Security Advisory](https://github.com/ClaimBound/claimbound-evidence/security/advisories/new).
- Trusted Publishing needs no rotation; the publisher configuration is reviewed whenever the
  release workflow or repository name changes.
