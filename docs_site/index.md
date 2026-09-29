# ClaimBound Evidence

**Where is the evidence?** ClaimBound turns a narrow public claim about AI, ML, data or
software into a small *evidence card*: frozen protocol, hashed sources, an exact result status,
a claim boundary and a reproduction level.

It is not a model leaderboard, a hosted scoring service or a certification authority.

## Pick a path

<div class="grid cards" markdown>

- **Check a card**

    Validate and read an existing card.

    [Quick start](quickstart.md) · [Read a card](concepts.md)

- **Rerun a card**

    Repeat a frozen check and record whether it reproduces.

    [Independent rerun workflow](INDEPENDENT_RERUN_WORKFLOW.md) · [No-coding start](START_WITHOUT_CODING.md)

- **Contribute a card**

    Scaffold a new check with a frozen protocol.

    [Getting started](GETTING_STARTED.md) · [Contributing](CONTRIBUTING.md)

</div>

## Install

```bash
pipx install claimbound-evidence        # or: uv tool install claimbound-evidence
claimbound validate-card path/to/card.json
```

See [Install](install.md) for what the pip package includes and for a full clone.

## Reading the results honestly

- A green card means **one narrow claim passed under one frozen protocol**, nothing more.
- Most public cards are still `SINGLE_OPERATOR` and `not independently reproduced`. Independent
  reruns are the signal that matters most; see [common misreadings](COMMON_MISREADINGS.md).
- Many cards were produced with AI assistance (`execution_mode: AUTOMATED_AI_ASSISTED`); the field
  is part of every card and a validated card is judged by its protocol, hashes and boundary.
- Negative, blocked and insufficient-coverage outcomes are published like positive ones.

Terms are explained in the [glossary](GLOSSARY.md).
