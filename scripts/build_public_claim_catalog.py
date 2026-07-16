#!/usr/bin/env python3
"""Build the 7,000-candidate ClaimBound public claim catalog."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import subprocess
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs/public_claims/domains"
VERSION = "2026-07-16-v1"
N_DOMAINS = 100
PER_DOMAIN = 70
N_CLAIMS = 7_000
BATCH_DOMAINS = 3

OUTCOMES = [
    "PASSED_UNDER_PROTOCOL",
    "INSUFFICIENT_COVERAGE",
    "NEGATIVE_RESULT_UNDER_PROTOCOL",
    "BLOCKED_SOURCE",
    "SOURCE_DRIFT",
]

GATES = [
    (
        "source-integrity",
        "The headline about {topic} can be traced to one exact public source "
        "version, canonical URL, access time, redirect chain, and SHA-256 hash.",
        "Freeze the exact source before the first fetch; do not replace a "
        "blocked or weak source after seeing the result.",
    ),
    (
        "numerator-denominator",
        "The published number for {topic} reproduces from the disclosed "
        "numerator, denominator, units, exclusions, and rounding rule.",
        "A nearby number or a recalculation with a different denominator is "
        "insufficient.",
    ),
    (
        "coverage",
        "The public claim about {topic} does not silently exclude affected "
        "people, places, incidents, products, time periods, or failed cases.",
        "Record the population, geography, inclusion rules, missingness, and "
        "known coverage limits.",
    ),
    (
        "time-boundary",
        "The public claim about {topic} is valid for the stated date or period "
        "and is not inherited from an older page, dataset, label, model, or "
        "policy version.",
        "Historical and current claims require separate cards; later drift "
        "must not rewrite the baseline.",
    ),
    (
        "method-version",
        "The claimed performance or change in {topic} survives the exact "
        "disclosed method, software version, thresholds, transformations, and "
        "quality controls.",
        "Freeze the method before execution and preserve version or "
        "implementation drift.",
    ),
    (
        "comparator",
        "The comparison behind {topic} uses a genuinely comparable baseline, "
        "population, operating condition, time window, and measurement rule.",
        "Do not compare unlike populations, definitions, roads, hospitals, "
        "models, years, products, or geographies.",
    ),
    (
        "reproducibility",
        "An independent operator can obtain the same public inputs for {topic} "
        "and rerun the frozen protocol without private credentials or "
        "undisclosed data.",
        "If access, licensing, paywalls, robots rules, missing files, or private "
        "inputs prevent this, preserve BLOCKED_SOURCE.",
    ),
    (
        "negative-evidence",
        "Negative, failed, delayed, recalled, blocked, adverse, or contradictory "
        "evidence relevant to {topic} is not omitted from the selected boundary.",
        "Absence alone is not a negative result; record INSUFFICIENT_COVERAGE "
        "unless the frozen protocol establishes contradiction.",
    ),
    (
        "conflicts-disclosure",
        "Sponsor, vendor, author, ownership, procurement, or institutional "
        "interests relevant to {topic} are disclosed inside the audit boundary.",
        "Disclosure is not proof of bias; missing disclosure is not proof of "
        "misconduct.",
    ),
    (
        "overclaim-drift",
        "The selected source does not justify a broader promise that {topic} is "
        "universally safe, effective, complete, causal, permanent, certified, "
        "or guaranteed.",
        "A pass is only source support for the narrow wording. It is never "
        "domain-wide certification or endorsement.",
    ),
]


def domains() -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = []
    for path in sorted(DATA_DIR.glob("domain_catalog_*.json")):
        part = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(part, list):
            raise SystemExit(f"ERROR: {path} must contain a list")
        data.extend(part)
    if not data:
        raise SystemExit("ERROR: no domain catalog chunks found")
    return data


def make_claims(domain_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    ordinal = 0
    for domain_index, domain in enumerate(domain_rows, 1):
        domain_code = f"DOM{domain_index:03d}"
        for topic_index, topic in enumerate(domain["topics"], 1):
            for gate_index, (gate, template, rule) in enumerate(GATES, 1):
                ordinal += 1
                claims.append(
                    {
                        "catalog_version": VERSION,
                        "ordinal": ordinal,
                        "claim_id": (
                            f"CB7K-{domain_code}-T{topic_index:02d}-"
                            f"G{gate_index:02d}"
                        ),
                        "domain_code": domain_code,
                        "domain_slug": domain["slug"],
                        "domain_title": domain["title"],
                        "topic_index": topic_index,
                        "topic": topic,
                        "gate_index": gate_index,
                        "gate": gate,
                        "frozen_candidate_claim": template.format(topic=topic),
                        "adjudication_rule": rule,
                        "suggested_source_boundary": domain["source_hint"],
                        "source_url": None,
                        "source_frozen_sha256": None,
                        "status": "PENDING_SOURCE_SELECTION",
                        "honest_outcomes": OUTCOMES,
                        "raw_payload_committed": False,
                    }
                )
    return claims


def validate(
    domain_rows: list[dict[str, Any]], claims: list[dict[str, Any]]
) -> None:
    errors: list[str] = []
    if len(domain_rows) != N_DOMAINS:
        errors.append(f"expected {N_DOMAINS} domains, got {len(domain_rows)}")
    if len(claims) != N_CLAIMS:
        errors.append(f"expected {N_CLAIMS} claims, got {len(claims)}")

    claim_ids = [claim["claim_id"] for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("claim IDs are not unique")

    slugs = [domain["slug"] for domain in domain_rows]
    if len(slugs) != len(set(slugs)):
        errors.append("domain slugs are not unique")

    for domain in domain_rows:
        if len(domain.get("topics", [])) != 7:
            errors.append(f"{domain.get('slug')}: expected 7 topics")

    counts = {slug: 0 for slug in slugs}
    for claim in claims:
        counts[claim["domain_slug"]] += 1
        if claim["status"] != "PENDING_SOURCE_SELECTION":
            errors.append(f"{claim['claim_id']}: bad initial status")
        if claim["source_url"] is not None:
            errors.append(f"{claim['claim_id']}: source preselected")
        if claim["raw_payload_committed"] is not False:
            errors.append(f"{claim['claim_id']}: raw payload policy")

    bad_counts = {slug: count for slug, count in counts.items() if count != PER_DOMAIN}
    if bad_counts:
        errors.append(f"domain counts: {bad_counts}")
    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))


def issue_url(claim: dict[str, Any]) -> str:
    body = (
        f"Candidate ID: `{claim['claim_id']}`\n\n"
        f"Domain: **{claim['domain_title']}**\n\n"
        "Frozen candidate claim:\n\n"
        f"> {claim['frozen_candidate_claim']}\n\n"
        "Before the first network fetch, add one exact canonical public source "
        "URL and record the frozen source-manifest SHA-256.\n\n"
        "Honest outcomes: `PASSED_UNDER_PROTOCOL`, `INSUFFICIENT_COVERAGE`, "
        "`NEGATIVE_RESULT_UNDER_PROTOCOL`, `BLOCKED_SOURCE`, or "
        "`SOURCE_DRIFT`.\n"
    )
    query = urllib.parse.urlencode(
        {
            "title": f"Verify {claim['claim_id']}: {claim['topic']}",
            "body": body,
        }
    )
    return "https://github.com/ClaimBound/claimbound-evidence/issues/new?" + query


def shell(title: str, body: str, root: str = "") -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · ClaimBound</title><style>:root{{--ink:#17383a;--paper:#f5f0e4;--card:#fffdf7;--line:#b9b4a7;--accent:#165b5c}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:34px 22px 70px}}a{{color:var(--accent)}}h1,h2{{font-family:Georgia,serif}}h1{{font-size:clamp(34px,6vw,62px);line-height:1.02}}.note,.claim,.domain{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}}.tag{{display:inline-block;padding:3px 8px;border-radius:99px;background:#e6f0eb;margin-right:6px;font-size:13px}}small{{color:#5f6f6f}}code{{overflow-wrap:anywhere}}input{{width:100%;padding:13px;border:1px solid var(--line);border-radius:10px;font:inherit}}[hidden]{{display:none}}blockquote{{margin-left:0;border-left:4px solid var(--accent);padding-left:14px}}nav a{{margin-right:16px}}</style></head><body><main><nav><a href="{root}index.html">Claim catalog home</a><a href="https://github.com/ClaimBound/claimbound-evidence">Repository</a></nav>{body}</main></body></html>'''


def build(
    output: Path,
    domain_rows: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "domains").mkdir(parents=True)
    (output / "issues").mkdir()

    catalog = {
        "catalog_version": VERSION,
        "domain_count": len(domain_rows),
        "claim_count": len(claims),
        "claims_per_domain": PER_DOMAIN,
        "initial_status": "PENDING_SOURCE_SELECTION",
        "honest_outcomes": OUTCOMES,
        "domains": domain_rows,
        "claims": claims,
    }
    (output / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "catalog.jsonl").write_text(
        "".join(json.dumps(claim, ensure_ascii=False) + "\n" for claim in claims),
        encoding="utf-8",
    )

    domain_cards: list[str] = []
    for domain in domain_rows:
        domain_claims = [
            claim for claim in claims if claim["domain_slug"] == domain["slug"]
        ]
        domain_dir = output / "domains" / domain["slug"]
        domain_dir.mkdir()
        searchable = html.escape(
            (
                domain["title"]
                + " "
                + domain["slug"]
                + " "
                + " ".join(domain["topics"])
            ).lower()
        )
        domain_cards.append(
            f'<article class="domain" data-search="{searchable}">'
            f'<h2><a href="domains/{domain["slug"]}/">'
            f'{html.escape(domain["title"])}</a></h2>'
            "<p>70 candidates · 7 topics · 10 gates</p>"
            f'<small>{html.escape(domain["source_hint"])}</small></article>'
        )

        claim_cards: list[str] = []
        for claim in domain_claims:
            searchable_claim = html.escape(
                (
                    claim["claim_id"]
                    + " "
                    + claim["topic"]
                    + " "
                    + claim["gate"]
                ).lower()
            )
            claim_cards.append(
                f'<article class="claim" data-search="{searchable_claim}">'
                f'<span class="tag">{claim["claim_id"]}</span>'
                f'<span class="tag">{html.escape(claim["gate"])}</span>'
                f'<h2>{html.escape(claim["topic"])}</h2>'
                f'<blockquote>{html.escape(claim["frozen_candidate_claim"])}</blockquote>'
                "<p><strong>Before fetch:</strong> "
                f'{html.escape(claim["adjudication_rule"])}</p>'
                f'<p><a href="{html.escape(issue_url(claim), quote=True)}">'
                "Open one verification issue</a></p></article>"
            )

        page_body = (
            "<p>CLAIMBOUND / DOMAIN CANDIDATES</p>"
            f'<h1>{html.escape(domain["title"])}</h1>'
            '<div class="note"><strong>70 pending candidates, not evidence.'</n            "</strong> Initial status: <code>PENDING_SOURCE_SELECTION</code>. "
            "Suggested source boundary: "
            f'{html.escape(domain["source_hint"])}. Freeze one exact URL before '
            "network access and keep every honest non-pass.</div>"
            '<input id="q" placeholder="Filter 70 candidates">'
            + "".join(claim_cards)
            + "<script>const q=document.querySelector('#q');q.oninput=()=>"
            "document.querySelectorAll('.claim').forEach(x=>x.hidden="
            "!x.dataset.search.includes(q.value.toLowerCase()))</script>"
        )
        (domain_dir / "index.html").write_text(
            shell(domain["title"], page_body, "../../"), encoding="utf-8"
        )

    home_body = (
        "<p>CLAIMBOUND / PUBLIC CLAIM CANDIDATE ATLAS</p>"
        "<h1>7,000 claims across 100 domains</h1>"
        '<div class="note"><strong>This is a preregistered backlog, not evidence.'
        "</strong> Every candidate begins at "
        "<code>PENDING_SOURCE_SELECTION</code>. Freeze one exact source before "
        "fetching; preserve PASS, INSUFFICIENT, NEGATIVE, BLOCKED, or DRIFT "
        "without rewriting.</div>"
        '<p><a href="catalog.json">JSON</a> · '
        '<a href="catalog.jsonl">JSONL</a> · '
        '<a href="issues/">Issue-ready batches</a></p>'
        '<input id="q" placeholder="Filter 100 domains"><section class="grid">'
        + "".join(domain_cards)
        + "</section><script>const q=document.querySelector('#q');q.oninput=()=>"
        "document.querySelectorAll('.domain').forEach(x=>x.hidden="
        "!x.dataset.search.includes(q.value.toLowerCase()))</script>"
    )
    (output / "index.html").write_text(
        shell("7,000 public claim candidates", home_body), encoding="utf-8"
    )

    batches = [
        domain_rows[index : index + BATCH_DOMAINS]
        for index in range(0, len(domain_rows), BATCH_DOMAINS)
    ]
    issue_index = [
        "# Issue-ready candidate batches",
        "",
        "> Candidate backlog only; no result is predeclared.",
        "",
    ]
    for batch_index, batch_domains in enumerate(batches, 1):
        batch_slugs = {domain["slug"] for domain in batch_domains}
        batch_claims = [
            claim for claim in claims if claim["domain_slug"] in batch_slugs
        ]
        batch_name = f"batch-{batch_index:02d}.md"
        issue_index.append(
            f"- [Batch {batch_index:02d}]({batch_name}) — "
            f"{', '.join(domain['title'] for domain in batch_domains)} "
            f"({len(batch_claims)} candidates)"
        )
        lines = [
            f"# Public claim catalog batch {batch_index:02d}/{len(batches):02d}",
            "",
            f"**Scope:** {len(batch_domains)} domains × 70 candidates = "
            f"{len(batch_claims)} locally verifiable candidate claims.",
            "",
            "> [!IMPORTANT]",
            "> These are frozen candidate questions, not evidence. Every entry "
            "starts at `PENDING_SOURCE_SELECTION`.",
            "> Freeze one exact public source URL before the first network fetch. "
            "Never replace a blocked or weak source after seeing the result.",
            "",
            "Honest outcomes: `PASSED_UNDER_PROTOCOL`, "
            "`INSUFFICIENT_COVERAGE`, `NEGATIVE_RESULT_UNDER_PROTOCOL`, "
            "`BLOCKED_SOURCE`, `SOURCE_DRIFT`.",
            "",
            "## Local preparation",
            "",
            "```bash",
            "python3 scripts/build_public_claim_catalog.py validate",
            "python3 scripts/build_public_claim_catalog.py build "
            "--output tmp/public-claim-catalog",
            f"cat tmp/public-claim-catalog/issues/{batch_name}",
            "```",
            "",
        ]
        for domain in batch_domains:
            lines.extend(
                [
                    f"## {domain['title']} — `{domain['slug']}`",
                    "",
                    f"Suggested source boundary: {domain['source_hint']}.",
                    "",
                ]
            )
            for claim in batch_claims:
                if claim["domain_slug"] == domain["slug"]:
                    lines.append(
                        f"- [ ] `{claim['claim_id']}` — "
                        f"**{claim['topic']} / {claim['gate']}** — "
                        f"{claim['frozen_candidate_claim']}"
                    )
            lines.append("")
        lines.extend(
            [
                "## Honest completion gate",
                "",
                "- [ ] Exact source URL selected and frozen before fetch for each "
                "executed candidate.",
                "- [ ] Canonical URL, redirects, access time, HTTP result, and "
                "SHA-256 recorded.",
                "- [ ] No source widening or claim rewriting after observing the "
                "result.",
                "- [ ] Every non-pass reviewed and retained.",
                "- [ ] Raw source payload remains local.",
                "- [ ] Published evidence cards pass `uv run claimbound "
                "validate-all` and tests.",
                "",
            ]
        )
        (output / "issues" / batch_name).write_text(
            "\n".join(lines), encoding="utf-8"
        )

    (output / "issues" / "README.md").write_text(
        "\n".join(issue_index) + "\n", encoding="utf-8"
    )
    issue_links = "".join(
        f'<article class="domain"><h2><a href="batch-{index:02d}.md">'
        f"Batch {index:02d}</a></h2><p>{len(batch)} domains · "
        f"{len(batch) * PER_DOMAIN} candidates</p></article>"
        for index, batch in enumerate(batches, 1)
    )
    issue_body = (
        "<p>CLAIMBOUND / ISSUE-READY BACKLOG</p>"
        f"<h1>{len(batches)} batches</h1>"
        '<div class="note">Each batch contains up to 210 candidates and fits '
        "one GitHub issue.</div>"
        f'<section class="grid">{issue_links}</section>'
    )
    (output / "issues" / "index.html").write_text(
        shell("Issue-ready batches", issue_body, "../"), encoding="utf-8"
    )


def freeze(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SystemExit("ERROR: manifest needs non-empty 'sources'")
    for index, source in enumerate(sources, 1):
        source_url = source.get("source_url")
        invalid = (
            not isinstance(source_url, str)
            or not source_url.startswith(("https://", "http://"))
            or "TODO" in source_url.upper()
            or "FILL" in source_url.upper()
        )
        if invalid:
            raise SystemExit(f"ERROR: invalid source #{index}")
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    print(hashlib.sha256(raw).hexdigest())


def run_build(output: Path) -> None:
    domain_rows = domains()
    claims = make_claims(domain_rows)
    validate(domain_rows, claims)
    build(output, domain_rows, claims)


def command_validate() -> None:
    domain_rows = domains()
    claims = make_claims(domain_rows)
    validate(domain_rows, claims)
    with tempfile.TemporaryDirectory() as temporary_directory:
        output = Path(temporary_directory) / "site"
        build(output, domain_rows, claims)
        if len(list((output / "domains").glob("*/index.html"))) != N_DOMAINS:
            raise SystemExit("ERROR: domain page count")
        batches = list((output / "issues").glob("batch-*.md"))
        if len(batches) != 34 or max(path.stat().st_size for path in batches) >= 65_536:
            raise SystemExit("ERROR: issue batches")
        catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
        if catalog["claim_count"] != N_CLAIMS:
            raise SystemExit("ERROR: catalog count")
    print("OK: 7000 unique candidates, 100 domain pages, 34 issue batches")


def publish(output: Path, repository: str, execute: bool) -> None:
    run_build(output)
    files = sorted((output / "issues").glob("batch-*.md"))
    if not execute:
        print(f"DRY RUN: would create {len(files)} issues in {repository}")
        for path in files:
            print(path)
        return
    if shutil.which("gh") is None:
        raise SystemExit("ERROR: gh required; run 'gh auth status'")
    subprocess.run(["gh", "auth", "status"], check=True)
    for index, path in enumerate(files, 1):
        subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                repository,
                "--title",
                f"Public claim catalog batch {index:02d}/{len(files):02d}: "
                "candidate domains",
                "--body-file",
                str(path),
            ],
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/public-claim-catalog"),
    )
    subparsers.add_parser("validate")
    freeze_parser = subparsers.add_parser("freeze-manifest")
    freeze_parser.add_argument("manifest", type=Path)
    publish_parser = subparsers.add_parser("publish-issues")
    publish_parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/public-claim-catalog"),
    )
    publish_parser.add_argument(
        "--repo", default="ClaimBound/claimbound-evidence"
    )
    publish_parser.add_argument("--publish", action="store_true")
    arguments = parser.parse_args()

    if arguments.command == "build":
        run_build(arguments.output)
        print(f"Built 7000 candidates across 100 domains at {arguments.output}")
    elif arguments.command == "validate":
        command_validate()
    elif arguments.command == "freeze-manifest":
        freeze(arguments.manifest)
    else:
        publish(arguments.output, arguments.repo, arguments.publish)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
