# Agent Rules

Rules for any AI coding assistant (Claude, Codex, Gemini, Cursor, Copilot or other)
working in this repository. They are binding and override tool defaults.

## Git authorship

- Every commit is authored **and** committed by the repository owner's git identity:
  `Rost S. <63606118+NeoZorK@users.noreply.github.com>`. Check `git config user.name`
  and `git config user.email` before the first commit; if they differ, stop and ask.
- Never set an AI, bot or tool as author or committer.
- Do not add `Co-Authored-By:` trailers for AI tools, and no "Generated with ...",
  robot emoji or similar footers in commit messages, PR descriptions, tags or
  release notes.
- Never rewrite published history and never force-push `main`.
- `git push`, tags, GitHub releases, PyPI/TestPyPI publishing and changes to repository
  settings happen **only after explicit owner approval, each time**.
- This rule is about commit identity only. Existing AI-use disclosures that are part of
  the evidence record (`docs/AI_USE.md`, `docs/AI_PROVENANCE_LOG.md`, `execution_mode`
  and `ai_assistance` fields in cards) must stay truthful; do not delete or falsify them.

## Evidence honesty

- Do not replace a blocked or insufficient source after seeing the result.
- Do not turn absence of evidence into a negative result, and do not reclassify
  outcomes to reach a target pass rate.
- `BLOCKED_SOURCE`, `INSUFFICIENT_COVERAGE`, `NEGATIVE_RESULT_UNDER_PROTOCOL` and
  source drift are first-class evidence, not failures to hide.
- Raw payloads stay local (`raw_payload_committed: false`).
- See [MAINTAINER_BOUNDARY.md](MAINTAINER_BOUNDARY.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Reserved roadmap work

Items listed in [docs/PLANNED_NOT_SHIPPED.md](docs/PLANNED_NOT_SHIPPED.md) and the
phases of [docs/ROADMAP_2026.md](docs/ROADMAP_2026.md) (SourceProbe, scaffold
hardening, run-root/deviation logs, public AI protocol, static registry views,
independent rerun tooling, schema/validator hardening, accessibility pass) are
reserved. Do not implement them without explicit owner approval. Keep releases on
`0.4.x`; `0.5.0` and later are reserved for those milestones.

Do not touch files or issues about the Manifold fair race
(`docs/manifold_monte_neo_fair_race/`, related scripts, artifacts and issues).
Never add private background technology or private data to this repository.

## Working plan

If a local, git-ignored `.maintainer/` directory exists, the plan inside it is the
current maintenance plan: continue from the first open item and append to its
handoff log.

## Commands

```bash
uv sync --extra dev
uv run claimbound validate-all
uv run --extra dev pytest -q -n auto
uv build && uvx twine check dist/*
```

If the uv cache is not writable in a sandbox, set `UV_CACHE_DIR` to a temp directory.
