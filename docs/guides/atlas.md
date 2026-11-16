# Browse experiments with the atlas

`protocolith atlas` turns a ledger or a directory of evidence cards into one HTML file you can open from disk, email or
a web server. Everything is inside the file: markup, style, script and data. It makes no network request and needs no
server, font or library.

```bash
protocolith atlas --out atlas.html                      # the local ledger (.protocolith), else docs/evidence_cards
protocolith atlas --store .protocolith --out site/      # writes site/protocolith-atlas.html
protocolith atlas --cards docs/evidence_cards --cards other/cards --title "Team registry" --out atlas.html
```

## Sources

- **Ledger** (`--store`): verified exactly like `verify-ledger`. Every `record` entry becomes a row; the shown fields are
  the card the record would issue. The header shows the head (`seq` and hash). If verification fails the atlas is still
  written, with a red banner listing the problems, and the command exits `1`.
- **Evidence cards** (`--cards DIR`, repeatable): every `*.json` file below the directory. Unknown fields are kept.
  Files that are not valid JSON, not an object, larger than 2 MiB, or without a string `evidence_id` and `result_status`
  are skipped; the page shows how many and why. Cards read from files are shown as found, not verified against a ledger.

Both can be combined. If two records share an `evidence_id` the first is kept and a warning is printed.
Exit codes: `0` ok, `1` the ledger failed verification, `2` bad input (missing directory, unknown `--default-lang`), `3`
environment error (for example no ledger).

## What the page offers

Header with integrity badge, summary tiles, a status bar chart and a timeline by month (both follow the filters), full-text
search over id, protocol, domain, status, claim boundary and sources, filters (status, domain, reproduction level, date
range), a sortable table in pages of 50 rows (fast with 10,000 or more records), and a detail drawer with every field,
the raw JSON, copy buttons for id, hash and link, and a permalink (`#<evidence_id>`).

Keyboard: `/` focuses the search, `j` and `k` move through the rows, `Enter` opens the row, `Esc` closes the drawer.
The theme follows the system and can be toggled. Statuses carry a letter and a symbol besides the colour:
P passed, N negative result, B blocked source, I insufficient coverage, D source drift, R reproduced outcome. A status
outside this vocabulary is shown as found with `?`; nothing is hidden or reclassified.

## Size and speed

A row keeps the columns above; all other fields are compressed in blocks and decoded when you open a record. Eight
thousand cards give a page of about 7 MB, built in a few seconds. Very long values are clipped in the page (the source
file is authoritative). `--max-rows N` embeds only the newest N records; the totals and status counts stay complete.

## Languages

The interface is English. Add languages with your own files: one `<code>.json` per language in a directory, passed as
`--i18n DIR`:

```json
{ "_name": "Deutsch", "filter_reset": "Filter zuruecksetzen" }
```

- `_name` is the name shown in the language switcher; the file name (`de.json`) is the code. Codes are two or three
  letters, optionally with a region (`pt-BR`).
- Missing or empty keys fall back to English. Keys that are not in `src/protocolith/core/atlas_i18n/en.json`, and values
  that are not strings, are ignored with a warning.
- The switcher appears only when at least one extra language is present. It starts in English (or `--default-lang`) and
  remembers the choice in the browser. Strings switch instantly.
- `python scripts/export_atlas_i18n_template.py --out de.json` writes all keys with empty values.
- `examples/atlas/i18n/de.json` is a complete example (German, written without umlauts).

The package ships no translation other than English.

## From Python and MCP

```python
from protocolith import core

page = core.build_atlas(cards=["docs/evidence_cards"], max_rows=5000)   # bytes
```

The MCP tool `protocolith_atlas` writes the page and returns its path. Paths must stay inside the working directory.
The output is deterministic: the same input gives the same bytes, and the page contains no timestamp of its own.
