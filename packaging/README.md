# Packaging Recipes

Ready-to-submit recipes for distributing the card-level CLI outside PyPI. **Nothing here is
submitted or published automatically**; a maintainer copies the rendered files to the
target repository by hand after a release exists on PyPI.

| Channel | Files | Tested here | Submitted |
| --- | --- | --- | --- |
| conda-forge | `conda-forge/recipe.yaml.tmpl` (v1 format) | Package names and versions checked against conda-forge; not built: no conda tooling on the authoring machine; YAML structure and the v1 layout follow the staged-recipes example | yes: merged as staged-recipes#35003, feedstock `conda-forge/claimbound-evidence-feedstock`, `claimbound-evidence 0.4.8` (noarch) published \|
| Homebrew tap | `homebrew/claimbound-evidence.rb.tmpl` | Ruby syntax; the dependency wheels it lists were downloaded, hash-checked and installed offline into a fresh Python 3.13 environment (macOS arm64). `brew install` itself was not run | no |
| Docker image | `docker/Dockerfile`, `docker/publish.yml.example` | Not built (Docker daemon was not running) | no |

## Render for a release

```bash
python packaging/render.py --version 0.4.8      # release must already be on PyPI
```

Output goes to `packaging/build/` (git-ignored): `conda-forge/recipe.yaml` and
`homebrew/claimbound-evidence.rb`. Hashes come from the PyPI JSON API; dependency wheels for
Homebrew come from `uv.lock` of the checked-out commit, so render from the release tag.

## conda-forge

1. Fork `conda-forge/staged-recipes`, add `recipes/claimbound-evidence/recipe.yaml` from the
   rendered file (staged-recipes requires the v1 format; v0 `meta.yaml` is deprecated for new recipes), open a pull request from the owner's GitHub account.
2. The linter and CI in that pull request are the real test; expect requests to adjust
   `about` fields. After merge, a feedstock is created and updated by a bot on each release.
3. The feedstock exists (2026-09-30); the badge and the install line are in the README. Updates are opened by the conda-forge bot on each PyPI release; the maintainer merges them.

The recipe is `noarch: python` and depends on `numpy`, `pdfplumber` and `pypdf`, all of which
exist on conda-forge. The build needs `hatchling` and `hatch-fancy-pypi-readme`.

## Homebrew (own tap)

1. Create the repository `ClaimBound/homebrew-tap` (owner action), add
   `Formula/claimbound-evidence.rb` from the rendered file.
2. Test on a Mac: `brew install --build-from-source ./claimbound-evidence.rb`, then
   `brew test claimbound-evidence` and `brew audit --strict --new claimbound-evidence`.
3. Users install with `brew install claimbound/tap/claimbound-evidence`.

Homebrew builds run without network access, so the formula installs the project wheel and
every dependency as a pinned binary wheel resource (SHA-256 each) with `pip --no-index`.
Platforms for which a dependency has no wheel (at the time of writing: macOS Intel, because
`cryptography` ships no Intel wheel) are excluded and make `install` stop with a clear message.
Every release needs a new rendered formula. Homebrew core is not a target: it requires
notability thresholds the project does not meet yet.

## Docker

```bash
python -m build --wheel
docker build -f packaging/docker/Dockerfile -t claimbound-evidence .
docker run --rm -v "$PWD:/work" claimbound-evidence validate-card card.json
```

`publish.yml.example` would push an image to GHCR on each release. It is not active; copy it
to `.github/workflows/docker.yml` only after deciding to publish images.

## Note on dependencies

`pdfplumber` and `pypdf` are declared as required dependencies but the installed package does
not import them; only scripts in the repository do. Moving them to an optional extra would make
all channels lighter (no Pillow, cryptography or pypdfium2 wheels). It is intentionally not done
here because `scripts/fetch_frozen_claim_sources.py` silently returns empty text when `pypdf`
is missing, which is a known cause of false "insufficient coverage" results. Decide this
together with a fix for that silent fallback.
