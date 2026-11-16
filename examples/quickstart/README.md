# Quickstart example

Files used by the quickstart in the repository README and in `docs/GETTING_STARTED_FIRST_RECORD.md`.

| File | Purpose |
| --- | --- |
| `protocol.json` | The protocol to freeze before the run. |
| `results.txt` | Four lines of example data, the "source" of the run. |
| `record.json` | The recorded outcome. It names the hash of `protocol.json` and the hash of `results.txt`. |

`tests/test_readme_examples.py` runs these steps in a temporary directory.
