# Install

ClaimBound needs Python 3.12 or newer and works on Windows, macOS and Linux
([platform support](PLATFORM_SUPPORT.md)).

## Card-level CLI from PyPI

```bash
pipx install claimbound-evidence        # or: uv tool install claimbound-evidence
                                        # or: pip install claimbound-evidence
                                        # or: conda install -c conda-forge claimbound-evidence   (pixi add claimbound-evidence)
claimbound --version
claimbound doctor
```

The package contains the validator and the card-level commands: `validate-card`, `inspect`,
`hash`, `run-root`, `new` and `doctor`. It does **not** contain the 8,000+ evidence cards,
the registry or the runner scripts. Commands that need them (`validate-all`, `demo`, `rerun`,
`drift`, `verify`) print how to clone the repository.

## Full clone

```bash
git clone https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
uv sync --extra dev
uv run claimbound validate-all
```

The repository is large because it holds every card and its SVG. If you only need the code,
tests and registry index:

```bash
git clone --filter=blob:none --sparse https://github.com/ClaimBound/claimbound-evidence.git
cd claimbound-evidence
git sparse-checkout set src tests docs/registry docs/evidence_cards docs/track_families
```

`validate-all` needs `docs/evidence_cards`; skip that folder only if you do not run it.
