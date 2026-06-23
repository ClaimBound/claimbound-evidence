# HEADROOM_WIDE_CLAIMS_D001 Runbook

This runbook reproduces the single-operator Headroom wide-claim split into
narrow ClaimBound evidence cards.

## Local Setup

Prerequisites:

- Python 3.12+
- `uv`
- local Ollama server
- one installed Qwen model, preferably `qwen2.5-coder:7b`

```bash
uv sync --extra dev
uv run claimbound doctor
ollama list
curl -sS http://127.0.0.1:11434/api/version
```

The runner keeps Headroom out of the base project dependencies. If Headroom is
not importable, it re-executes itself through:

```bash
uv run --with headroom-ai==0.27.0 --with transformers python scripts/claimbound_run_headroom_wide_claims.py
```

## Execute

```bash
HEADROOM_TELEMETRY=off \
uv run python scripts/claimbound_run_headroom_wide_claims.py
```

Optional flags:

```bash
uv run python scripts/claimbound_run_headroom_wide_claims.py --skip-ollama
uv run python scripts/claimbound_run_headroom_wide_claims.py --model qwen3:8b
uv run python scripts/claimbound_run_headroom_wide_claims.py --access-date 2026-06-23
```

`--skip-ollama` is only for debugging the source-boundary path. It should not be
used for the committed runtime cards unless the cards are marked
`INSUFFICIENT_COVERAGE`.

## Validate

```bash
uv run python scripts/claimbound_render_evidence_card_svg.py --all
uv run claimbound validate-all
uv run --extra dev python -m pytest -q
```

## What Is Public

Committed artifacts include only sanitized summaries: hashes, byte counts,
token counts, model identifiers, exact boolean gates and known limitations.

Do not commit:

- raw fixtures;
- full prompts or transcripts;
- API keys or tokens;
- private Codex traffic;
- macOS serial number, hardware UUID or provisioning UDID;
- full Ollama response bodies.

## How To Read Negative Runtime Cards

The Ollama runtime cards are not a verdict that Headroom cannot be used locally.
They say something narrower: under this direct local Ollama/Qwen protocol, a
fixture had to satisfy both token reduction and exact synthetic-answer
preservation. JSON and log fixtures achieved large token reductions, but the
compressed prompt did not return the expected identifier. The agent-history
fixture preserved the answer but did not reduce tokens. Those are negative
results for these frozen gates only.

If a Headroom workflow intentionally relies on CCR retrieval, proxy routing,
tool calls, or accepts semantic answer drift, open a new protocol and card for
that claim. Do not reinterpret these cards as proof that Headroom is broadly
unusable or broadly validated.

## How To Rerun Or Challenge

1. Open a GitHub reproduction request for the relevant Headroom card.
2. State your OS, hardware class, Ollama version and model name.
3. Rerun the same command and attach sanitized summaries only.
4. Publish a rerun card with one of:
   `REPRODUCED_OUTCOME`, `NEGATIVE_RESULT_UNDER_PROTOCOL` or
   `INSUFFICIENT_COVERAGE`.

Different outcomes are useful evidence. Do not edit thresholds after seeing the
result.

## Headroom Maintainer Contact

After the public cards validate, open a neutral Headroom GitHub issue or
discussion:

```text
We used ClaimBound to split Headroom's wide token-compression statement into
narrow evidence cards. This is not a certification or endorsement request. The
cards include positive, negative and insufficient outcomes under one local
MacBook Pro / Ollama / Qwen run. Would you like a link to the cards or runbook
in your docs for external reruns?
```

## LinkedIn Note

A LinkedIn Organization Page can be used for a no-paid-distribution article
when the user has the right page admin role. Publish only after the cards and
registry are public. Recommended title:

```text
Independent ClaimBound evidence cards for Headroom token-compression claims
```

The article must say: single-operator local run, MacBook Pro M1 Pro 16 GB, not
certification, reruns welcome.
