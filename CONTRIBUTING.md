# Contributing

Participation falls under the [Code of Conduct](CODE_OF_CONDUCT.md).

Contributions are welcome when they preserve the evidence boundary.

Rules:

- do not commit raw CSV, JSON, parquet, ZIP or account-export payloads;
- do not commit secrets, API keys, private paths or personal account screenshots;
- do not add private production integrations or private background technology;
- do not change a frozen target, scorer, control or acceptance gate after seeing
  a result;
- record failed or blocked runs honestly;
- new behavior comes with a test: add or update a pytest case in `tests/` that fails
  without your change (the suite runs in CI on every pull request).

## AI Assistance And Provenance

AI assistance is allowed when it follows [AI Workflow](docs/AI_WORKFLOW.md) and
[AI Operator Protocol](docs/AI_OPERATOR_PROTOCOL.md).

When AI assistance is materially used in a contribution:

- disclose the role of AI assistance in the pull request summary or linked
  evidence card;
- keep final status decisions tied to a frozen protocol, checklist, runner or
  validator, not model opinion;
- keep raw prompts, transcripts, private account material and private-source
  details outside the public repository unless redistribution is clearly allowed;
- keep public provenance in PRs, commits, checks, releases, evidence cards and
  registry entries.

For AI provenance log and GitHub audit-log handling, see
[AI provenance log and audit logs](docs/AI_PROVENANCE_LOG.md).

## Reporting a bug

Open a [Bug Report](https://github.com/ClaimBound/claimbound-evidence/issues/new?template=bug_report.yml)
for incorrect tool behavior, failing tests or broken reproducibility. Include:

- the output of `claimbound --version` and `claimbound doctor`;
- the exact command you ran and the card file or `evidence_id` involved;
- what you expected and what happened instead (paste the error text, never raw payloads);
- your operating system and Python version.

Other issue forms cover source drift, card-boundary questions, evidence requests and
reproduction requests: <https://github.com/ClaimBound/claimbound-evidence/issues/new/choose>.
Do not open a public issue for a suspected vulnerability; follow [SECURITY.md](SECURITY.md).

## Default branch (`main`)

Repository rules enforce the following:

- **Pull requests**: changes must reach `main` through a merged PR (not by direct push).
- **Reviews**: **one approving review** is required for users who are not covered by a ruleset bypass.
  **ClaimBound organization owners** can bypass rules in the pull-request merge path (`bypass_mode: pull_request`)
  so a solo org owner can still land changes after checks pass; everyone else needs a normal approval.
  GitHub does not count approving your **own** PR toward the required review count.
- **Status checks**: `pytest` (`.github/workflows/tests.yml`) and `review`
  (`.github/workflows/dependency-review.yml`) must succeed on pull requests;
  strict branch-up-to-date behavior is enabled. Both workflows use GitHub-hosted
  runners, which are free for this public repository.
- **Merge style**: only **squash** or **rebase** merges are allowed; merge commits are disabled to match
  **required linear history** and reduce accidental merge-only noise on `main`.

The JSON payload for the repo ruleset (for reproducibility) lives at
[`scripts/github/ruleset_protect_main.json`](scripts/github/ruleset_protect_main.json). To recreate it from
scratch after deletion, admins can run `gh api --method POST` with `--input` pointing at that file; to
adjust an existing ruleset without duplicating entries, obtain its numeric id (`gh ruleset list -R ClaimBound/claimbound-evidence`) and use GitHub's `PUT /repos/{owner}/{repo}/rulesets/{ruleset_id}` REST route.

## Platform support

ClaimBound targets Windows, macOS and Linux through the `claimbound` Python CLI.
You do not need bash, jq, curl or shasum for the primary operator paths. See
[platform support](docs/PLATFORM_SUPPORT.md).

Before opening a pull request:

```bash
uv sync --extra dev
uv run claimbound doctor
uv run claimbound validate-all
uv run pytest -n auto
```

## Developer Certificate of Origin

ClaimBound requires every commit submitted through a pull request to carry a matching `Signed-off-by:` trailer under the [Developer Certificate of Origin](DCO.md). Use `git commit -s` when creating commits. The `DCO` GitHub Actions check rejects pull requests with a missing or mismatched sign-off.
