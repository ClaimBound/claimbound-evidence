# SPDX-License-Identifier: Apache-2.0
"""Deterministic read-only static views of the public evidence registry.

Reads ``docs/registry/evidence_index.json`` (validated against every referenced
card JSON) and renders Markdown pages plus one self-contained HTML page under
``docs/registry/views/``. Output depends only on the index and the repository
file tree; it contains no wall-clock timestamps and no raw payloads.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from claimbound_evidence.registry import load_registry, validate_registry

INDEX_REL = "docs/registry/evidence_index.json"
VIEWS_REL = "docs/registry/views"
# (index field, row key, label)
FILTERS = (
    ("result_status", "status", "Status"),
    ("official_source_name", "source", "Source"),
    ("domain", "domain", "Domain"),
    ("audience", "audience", "Audience"),
    ("reproduction_level", "repro", "Reproduction level"),
)
REPO_NOTE = (
    "Read-only generated view of `docs/registry/evidence_index.json`. "
    "Do not edit by hand; regenerate with "
    "`uv run python scripts/claimbound_build_registry_view.py`. "
    "No raw payloads are stored here."
)


class RegistryViewError(RuntimeError):
    """Raised when the index does not validate against the card JSON files."""


def slug(value: str) -> str:
    out = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return out or "unknown"


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def validate_registry_strict(registry: dict[str, Any], repo_root: Path) -> None:
    violations = validate_registry(registry, repo_root)
    if violations:
        shown = "\n".join(violations[:20])
        raise RegistryViewError(
            f"registry does not validate against card JSON ({len(violations)} "
            f"violation(s)); first:\n{shown}"
        )


def _row(entry: dict[str, Any], repo_root: Path, up: str) -> dict[str, Any]:
    """Normalise one entry; ``up`` is the relative prefix from views dir to docs/."""
    card_rel = entry["path"]
    docs_rel = card_rel[len("docs/"):] if card_rel.startswith("docs/") else card_rel
    svg_rel = docs_rel[:-5] + ".svg" if docs_rel.endswith(".json") else ""
    has_svg = bool(svg_rel) and (repo_root / "docs" / svg_rel).is_file()
    return {
        "seq": entry["registry_sequence"],
        "id": entry["evidence_id"],
        "status": entry["result_status"],
        "source": entry["official_source_name"],
        "domain": entry["domain"],
        "audience": str(entry.get("audience", "")),
        "repro": entry["reproduction_level"],
        "record_type": entry["record_type"],
        "json": up + docs_rel,
        "svg": (up + svg_rel) if has_svg else "",
    }


def _md_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| # | Evidence | Status | Domain | Source | Reproduction level | Card | SVG |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        svg = f"[svg]({r['svg']})" if r["svg"] else "n/a"
        lines.append(
            f"| {r['seq']} | `{_md(r['id'])}` | {_md(r['status'])} | {_md(r['domain'])} "
            f"| {_md(r['source'])} | {_md(r['repro'])} | [json]({r['json']}) | {svg} |"
        )
    return lines


def _counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return dict(sorted(out.items()))


def _page(title: str, rows: list[dict[str, Any]], version: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"> {REPO_NOTE}",
        "",
        "[Index](index.md) | [HTML view](index.html)",
        "",
        f"Entries: {len(rows)} (index last_updated: {version})",
        "",
        *_md_table(rows),
        "",
    ]
    return "\n".join(lines)


def _index_md(registry: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# ClaimBound Public Evidence Registry - static view",
        "",
        f"> {REPO_NOTE}",
        "",
        f"- Registry: {registry.get('registry_name')} {registry.get('registry_version')}",
        f"- Index last_updated: {registry.get('last_updated', '')}",
        f"- Entries: {len(rows)}",
        "- Single-file filterable view: [index.html](index.html)",
        "",
        "## By result status",
        "",
        "| Status | Entries |",
        "|---|---:|",
    ]
    for s, n in _counts(rows, "status").items():
        lines.append(f"| [{_md(s)}](status-{slug(s)}.md) | {n} |")
    lines += ["", "## By domain", "", "| Domain | Entries |", "|---|---:|"]
    for d, n in _counts(rows, "domain").items():
        lines.append(f"| [{_md(d)}](domain-{slug(d)}.md) | {n} |")
    lines.append("")
    return "\n".join(lines)


def _index_html(registry: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    esc = html.escape
    version = esc(str(registry.get("last_updated", "")))
    filters = []
    for _field, key, label in FILTERS:
        values = sorted({r[key] for r in rows if r[key]})
        if not values:
            continue  # field absent from index data (e.g. audience): no empty filter
        opts = "".join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in values)
        filters.append(
            f'<label>{esc(label)} <select data-filter="{key}">'
            f'<option value="">All</option>{opts}</select></label>'
        )
    body_rows = []
    for r in rows:
        svg = f'<a href="{esc(r["svg"])}">svg</a>' if r["svg"] else "n/a"
        body_rows.append(
            f'<tr data-status="{esc(r["status"])}" data-source="{esc(r["source"])}" '
            f'data-domain="{esc(r["domain"])}" data-audience="{esc(r["audience"])}" '
            f'data-repro="{esc(r["repro"])}">'
            f'<th scope="row">{r["seq"]}</th>'
            f'<td><code>{esc(r["id"])}</code></td><td>{esc(r["status"])}</td>'
            f'<td>{esc(r["domain"])}</td><td>{esc(r["source"])}</td>'
            f'<td>{esc(r["repro"])}</td>'
            f'<td><a href="{esc(r["json"])}">json</a></td><td>{svg}</td></tr>'
        )
    head = "".join(
        f'<th scope="col">{c}</th>'
        for c in ("#", "Evidence", "Status", "Domain", "Source",
                  "Reproduction level", "Card", "SVG")
    )
    nl = "\n"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClaimBound Public Evidence Registry</title>
<style>
:root{{color-scheme:light dark;--bg:#fff;--fg:#1a1a1a;--muted:#555;--line:#ccc;--head:#f0f0f0;--link:#0b5cad}}
@media (prefers-color-scheme:dark){{:root{{--bg:#121212;--fg:#e8e8e8;--muted:#aaa;--line:#444;--head:#222;--link:#7ab8ff}}}}
body{{margin:0 auto;max-width:90rem;padding:1rem;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}
a{{color:var(--link)}}
.filters{{display:flex;flex-wrap:wrap;gap:.75rem;margin:1rem 0}}
.filters[hidden]{{display:none}}
select{{max-width:22rem;background:var(--bg);color:var(--fg);border:1px solid var(--line);padding:.25rem}}
.wrap{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%}}
caption{{text-align:left;font-weight:600;padding:.5rem 0}}
th,td{{border:1px solid var(--line);padding:.3rem .5rem;text-align:left;vertical-align:top}}
thead th{{background:var(--head)}}
code{{font-size:.85em;word-break:break-all}}
.muted{{color:var(--muted)}}
</style>
</head>
<body>
<h1>ClaimBound Public Evidence Registry</h1>
<p class="muted">Read-only generated view of <code>docs/registry/evidence_index.json</code>
(last_updated {version}). {len(rows)} entries. No raw payloads are stored here.
Markdown pages: <a href="index.md">index.md</a>.</p>
<div class="filters" id="filters" role="search" aria-label="Filter registry entries" hidden>
{nl.join(filters)}
<span id="count" role="status" aria-live="polite"></span>
</div>
<div class="wrap">
<table id="registry">
<caption>Evidence registry entries, ordered by registry sequence</caption>
<thead><tr>{head}</tr></thead>
<tbody>
{nl.join(body_rows)}
</tbody>
</table>
</div>
<script>
(function(){{
var box=document.getElementById('filters');
if(!box)return;
box.hidden=false;
var sels=box.querySelectorAll('select[data-filter]');
var rows=document.querySelectorAll('#registry tbody tr');
var count=document.getElementById('count');
function apply(){{
var n=0;
for(var i=0;i<rows.length;i++){{
var ok=true;
for(var j=0;j<sels.length;j++){{
var v=sels[j].value;
if(v&&rows[i].getAttribute('data-'+sels[j].getAttribute('data-filter'))!==v){{ok=false;break;}}
}}
rows[i].hidden=!ok;
if(ok)n++;
}}
count.textContent=n+' of '+rows.length+' shown';
}}
for(var k=0;k<sels.length;k++)sels[k].addEventListener('change',apply);
apply();
}})();
</script>
</body>
</html>
"""


def build_views_from_registry(registry: dict[str, Any], repo_root: Path) -> dict[str, str]:
    """Render views from an already-validated registry dict."""
    rows = [_row(e, repo_root, "../../") for e in registry["cards"]]
    rows.sort(key=lambda r: r["seq"])
    version = str(registry.get("last_updated", ""))
    out: dict[str, str] = {
        "index.md": _index_md(registry, rows),
        "index.html": _index_html(registry, rows),
    }
    for key, prefix, label in (("status", "status", "Status"), ("domain", "domain", "Domain")):
        groups: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            groups.setdefault(r[key], []).append(r)
        seen: dict[str, str] = {}
        for value in sorted(groups):
            name = f"{prefix}-{slug(value)}.md"
            if name in seen:
                raise RegistryViewError(f"slug collision: {value!r} vs {seen[name]!r}")
            seen[name] = value
            out[name] = _page(f"{label}: {value}", groups[value], version)
    return out


def build_views(repo_root: Path) -> dict[str, str]:
    """Validate the index against card JSON, then render. Raises RegistryViewError."""
    registry = load_registry(repo_root / INDEX_REL)
    validate_registry_strict(registry, repo_root)
    return build_views_from_registry(registry, repo_root)


def write_views(repo_root: Path) -> list[str]:
    content = build_views(repo_root)
    vdir = repo_root / VIEWS_REL
    vdir.mkdir(parents=True, exist_ok=True)
    for p in sorted(vdir.iterdir()):
        if p.is_file() and p.name not in content and p.name != "README.md":
            p.unlink()
    for name, text in content.items():
        (vdir / name).write_bytes(text.encode("utf-8"))
    return sorted(content)


def check_views(repo_root: Path) -> list[str]:
    """Return a list of problems (empty when committed views are current)."""
    content = build_views(repo_root)
    vdir = repo_root / VIEWS_REL
    problems: list[str] = []
    for name, text in sorted(content.items()):
        p = vdir / name
        if not p.is_file():
            problems.append(f"missing: {name}")
        elif p.read_bytes() != text.encode("utf-8"):
            problems.append(f"stale: {name}")
    if vdir.is_dir():
        for p in sorted(vdir.iterdir()):
            if p.is_file() and p.name not in content and p.name != "README.md":
                problems.append(f"unexpected: {p.name}")
    return problems
