# Contributing

Participation falls under the [Code of Conduct](CODE_OF_CONDUCT.md).

Contributions are welcome when they preserve the evidence boundary.

Rules:

- do not commit raw CSV, JSON, parquet, ZIP or account-export payloads;
- do not commit secrets, API keys, private paths or personal account screenshots;
- do not add private production integrations or private background technology;
- do not change a frozen target, scorer, control or acceptance gate after seeing
  a result;
- record failed or blocked runs honestly.

## Default branch (`main`)

Repository rules enforce the following:

- **Pull requests**: changes must reach `main` through a merged PR (not by direct push).
- **Reviews**: **one approving review** is required for users who are not covered by a ruleset bypass.
  **ClaimBound organization owners** can bypass rules in the pull-request merge path (`bypass_mode: pull_request`)
  so a solo org owner can still land changes after checks pass; everyone else needs a normal approval.
  GitHub does not count approving your **own** PR toward the required review count.
- **Status checks**: `pytest` (`.github/workflows/tests.yml`) and `review`
  (`.github/workflows/dependency-review.yml`) must succeed; strict branch-up-to-date behavior is enabled.
- **Merge style**: only **squash** or **rebase** merges are allowed; merge commits are disabled to match
  **required linear history** and reduce accidental merge-only noise on `main`.

The JSON payload for the repo ruleset (for reproducibility) lives at
[`scripts/github/ruleset_protect_main.json`](scripts/github/ruleset_protect_main.json). To recreate it from
scratch after deletion, admins can run `gh api --method POST` with `--input` pointing at that file; to
adjust an existing ruleset without duplicating entries, obtain its numeric id (`gh ruleset list -R ClaimBound/claimbound-public-benchmarks`) and use GitHub's `PUT /repos/{owner}/{repo}/rulesets/{ruleset_id}` REST route.

Before opening a pull request:

```bash
uv run pytest -n auto
```

