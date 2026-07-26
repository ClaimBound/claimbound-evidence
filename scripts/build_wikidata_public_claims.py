#!/usr/bin/env python3
"""Discover and freeze 7,000 distinct revision-bound Wikidata statements.

The resulting manifest proves only that a structured statement was published in
the named Wikidata revision.  It does not treat Wikidata publication as proof of
the statement's real-world truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from build_public_claim_catalog import domains

API = "https://www.wikidata.org/w/api.php"
USER_AGENT = (
    "ClaimBoundEvidence/1.0 "
    "(https://github.com/ClaimBound/claimbound-evidence; maintainer NeoZorK)"
)
EXCLUDED_DATATYPES = {"commonsMedia", "external-id", "url"}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


class Client:
    def __init__(self, cache: Path, delay: float = 0.12) -> None:
        self.cache = cache
        self.cache.mkdir(parents=True, exist_ok=True)
        self.delay = delay

    def get(self, params: dict[str, Any]) -> dict[str, Any]:
        params = {**params, "format": "json", "maxlag": 5}
        key = hashlib.sha256(canonical(params).encode()).hexdigest()
        path = self.cache / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        url = API + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    raw = response.read()
                payload = json.loads(raw)
                if "error" in payload:
                    raise RuntimeError(payload["error"])
                path.write_bytes(raw)
                time.sleep(self.delay)
                return payload
            except (urllib.error.URLError, TimeoutError, RuntimeError):
                if attempt == 5:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")


def load_revision(client: Client, revision: int) -> tuple[str, str]:
    payload = client.get(
        {
            "action": "query",
            "prop": "revisions",
            "revids": revision,
            "rvprop": "ids|timestamp|content",
            "rvslots": "main",
            "formatversion": 2,
        }
    )
    row = payload["query"]["pages"][0]["revisions"][0]
    return row["timestamp"], row["slots"]["main"]["content"]


def display_value(value: Any) -> str:
    if isinstance(value, dict):
        if "id" in value:
            return str(value["id"])
        if "text" in value:
            return str(value["text"])
        if "time" in value:
            return str(value["time"])
        if "amount" in value:
            return str(value["amount"])
    text = canonical(value)
    return text if len(text) <= 180 else text[:177] + "..."


def verbatim_statement(raw: str, statement_id: str) -> str:
    marker = json.dumps(statement_id, ensure_ascii=False)
    marker_at = raw.find(marker)
    if marker_at < 0:
        raise ValueError(f"statement id absent from revision: {statement_id}")
    start = raw.rfind('{"mainsnak"', 0, marker_at)
    if start < 0:
        raise ValueError(f"statement object start absent: {statement_id}")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(raw)):
        char = raw[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                excerpt = raw[start : index + 1]
                if statement_id not in excerpt:
                    raise ValueError(f"wrong statement object located: {statement_id}")
                return excerpt
    raise ValueError(f"unterminated statement object: {statement_id}")


def search_terms(domain: dict[str, Any]) -> list[str]:
    terms = [domain["title"], *domain["topics"]]
    terms.extend(f"{domain['title']} {topic}" for topic in domain["topics"])
    result: list[str] = []
    for term in terms:
        term = " ".join(term.split())
        if term and term.lower() not in {item.lower() for item in result}:
            result.append(term)
    return result


def entity_ids(client: Client, domain: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for term in search_terms(domain):
        payload = client.get(
            {
                "action": "wbsearchentities",
                "search": term,
                "language": "en",
                "uselang": "en",
                "type": "item",
                "limit": 50,
            }
        )
        for row in payload.get("search", []):
            if row["id"] not in found:
                found.append(row["id"])
        if len(found) >= 100:
            break
    if len(found) < 100:
        for term in search_terms(domain):
            payload = client.get(
                {
                    "action": "query",
                    "list": "search",
                    "srsearch": term,
                    "srnamespace": 0,
                    "srlimit": 50,
                }
            )
            for row in payload.get("query", {}).get("search", []):
                title = str(row.get("title", ""))
                if title.startswith("Q") and title[1:].isdigit() and title not in found:
                    found.append(title)
            if len(found) >= 100:
                break
    return found


def fetch_entities(client: Client, ids: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for start in range(0, len(ids), 50):
        payload = client.get(
            {
                "action": "wbgetentities",
                "ids": "|".join(ids[start : start + 50]),
                "props": "claims|labels|descriptions|info",
                "languages": "en",
            }
        )
        result.update(payload["entities"])
    return result


def fetch_labels(client: Client, ids: set[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    ordered = sorted(ids, key=lambda value: (value[0], int(value[1:])))
    for start in range(0, len(ordered), 50):
        payload = client.get(
            {
                "action": "wbgetentities",
                "ids": "|".join(ordered[start : start + 50]),
                "props": "labels",
                "languages": "en",
            }
        )
        for entity_id, entity in payload["entities"].items():
            result[entity_id] = entity.get("labels", {}).get("en", {}).get(
                "value", entity_id
            )
    return result


def collect(cache: Path, output: Path) -> dict[str, Any]:
    client = Client(cache)
    used_statement_ids: set[str] = set()
    records: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for domain_number, domain in enumerate(domains(), 1):
        ids = entity_ids(client, domain)
        entities = fetch_entities(client, ids)
        selected: list[tuple[dict[str, Any], str, dict[str, Any]]] = []
        for entity_id in ids:
            entity = entities.get(entity_id, {})
            for property_id in sorted(entity.get("claims", {})):
                for statement in entity["claims"][property_id]:
                    mainsnak = statement.get("mainsnak", {})
                    statement_id = str(statement.get("id", ""))
                    if (
                        statement_id
                        and statement_id not in used_statement_ids
                        and statement.get("rank") != "deprecated"
                        and mainsnak.get("snaktype") == "value"
                        and mainsnak.get("datatype") not in EXCLUDED_DATATYPES
                        and "datavalue" in mainsnak
                    ):
                        selected.append((entity, property_id, statement))
                    if len(selected) >= 70:
                        break
                if len(selected) >= 70:
                    break
            if len(selected) >= 70:
                break
        coverage.append(
            {
                "domain_code": f"DOM{domain_number:03d}",
                "slug": domain["slug"],
                "searched_entities": len(ids),
                "eligible_statements": len(selected),
            }
        )
        if len(selected) != 70:
            raise SystemExit(
                f"ERROR: {domain['slug']} has {len(selected)} eligible unique statements"
            )
        revision_cache: dict[int, tuple[str, str, dict[str, Any]]] = {}
        for ordinal, (entity, property_id, statement) in enumerate(selected, 1):
            entity_id = entity["id"]
            revision = int(entity["lastrevid"])
            if revision not in revision_cache:
                timestamp, raw_content = load_revision(client, revision)
                revision_cache[revision] = (timestamp, raw_content, json.loads(raw_content))
            timestamp, raw_content, frozen_entity = revision_cache[revision]
            frozen_statement = next(
                row
                for row in frozen_entity["claims"][property_id]
                if row.get("id") == statement["id"]
            )
            quote = verbatim_statement(raw_content, statement["id"])
            if quote not in raw_content:
                raise SystemExit(
                    f"ERROR: statement {statement['id']} is not verbatim in revision {revision}"
                )
            label = entity.get("labels", {}).get("en", {}).get("value", entity_id)
            value = frozen_statement["mainsnak"]["datavalue"]["value"]
            claim_id = f"CB7K-DOM{domain_number:03d}-C{ordinal:02d}"
            records.append(
                {
                    "claim_id": claim_id,
                    "domain_code": f"DOM{domain_number:03d}",
                    "domain_slug": domain["slug"],
                    "domain_title": domain["title"],
                    "entity_id": entity_id,
                    "entity_label": label,
                    "property_id": property_id,
                    "property_label": property_id,
                    "statement_id": statement["id"],
                    "revision_id": revision,
                    "revision_timestamp": timestamp,
                    "public_claim_text": (
                        f"In Wikidata revision {revision}, {label} ({entity_id}) "
                        f"publishes property {property_id} with value {display_value(value)}."
                    ),
                    "value_display": display_value(value),
                    "value_entity_id": (
                        value.get("id") if isinstance(value, dict) else None
                    ),
                    "public_claim_verbatim_quote": quote,
                    "public_claim_source_url": (
                        f"https://www.wikidata.org/w/api.php?action=query&format=json&"
                        f"prop=revisions&revids={revision}&rvprop=ids%7Ctimestamp%7Ccontent&"
                        "rvslots=main&formatversion=2"
                    ),
                    "public_claim_locator": (
                        f"entity {entity_id}; claims.{property_id}; statement {statement['id']}"
                    ),
                    "public_claim_captured_at": timestamp,
                    "public_claim_source_sha256": hashlib.sha256(
                        raw_content.encode("utf-8")
                    ).hexdigest(),
                    "statement_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(),
                    "verification_scope": "publication-in-revision-only",
                    "result_status": "PASSED_UNDER_PROTOCOL",
                }
            )
            used_statement_ids.add(statement["id"])
        print(f"collected {domain_number:03d}/100 {domain['slug']}: 70", flush=True)
    label_ids = {row["property_id"] for row in records}
    label_ids.update(
        row["value_entity_id"]
        for row in records
        if row["value_entity_id"]
        and row["value_entity_id"][0] in {"Q", "P", "L"}
    )
    labels = fetch_labels(client, label_ids)
    for row in records:
        property_label = labels.get(row["property_id"], row["property_id"])
        value_label = (
            labels.get(row["value_entity_id"], row["value_entity_id"])
            if row["value_entity_id"]
            else row["value_display"]
        )
        row["property_label"] = property_label
        row["value_label"] = value_label
        row["public_claim_text"] = (
            f"Wikidata statement {row['statement_id']} in revision {row['revision_id']} "
            f"asserts that {row['entity_label']} "
            f"({row['entity_id']}) publishes {property_label} ({row['property_id']}) "
            f"with value {value_label}"
            + (f" ({row['value_entity_id']})." if row["value_entity_id"] else ".")
        )
        row.pop("value_display")
        row.pop("value_entity_id")
    payload = {
        "schema_version": "CB7K-WIKIDATA-PUBLIC-CLAIMS-v1",
        "claim_count": len(records),
        "category_count": len(coverage),
        "claim_boundary": (
            "Each result verifies publication of one exact structured statement in one "
            "frozen Wikidata revision; it does not establish real-world truth."
        ),
        "raw_payload_committed": False,
        "license": "Wikidata structured data: CC0",
        "verification_scope": "statement publication in one frozen Wikidata revision",
        "records": records,
        "coverage": coverage,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def validate(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["records"]
    assert payload["claim_count"] == 7000 == len(rows)
    assert payload["category_count"] == 100
    assert len({row["claim_id"] for row in rows}) == 7000
    assert len({row["statement_id"] for row in rows}) == 7000
    assert all(row["public_claim_source_url"].startswith("https://") for row in rows)
    assert all(len(row["public_claim_verbatim_quote"]) >= 20 for row in rows)
    assert all(len(row["public_claim_source_sha256"]) == 64 for row in rows)
    print("VALID: 7000 distinct revision-bound public statements across 100 categories")


def verify_sources(path: Path, cache: Path, claim_id: str | None = None) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["records"]
    if claim_id is not None:
        rows = [row for row in rows if row["claim_id"] == claim_id]
        if not rows:
            raise SystemExit(f"ERROR: unknown claim ID: {claim_id}")
    client = Client(cache, delay=0)
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["revision_id"]), []).append(row)
    checked = 0
    for revision, revision_rows in grouped.items():
        timestamp, raw_content = load_revision(client, revision)
        digest = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        for row in revision_rows:
            assert row["public_claim_source_sha256"] == digest
            assert row["revision_timestamp"] == timestamp
            assert row["statement_id"] in row["public_claim_verbatim_quote"]
            assert row["public_claim_verbatim_quote"] in raw_content
            assert hashlib.sha256(
                row["public_claim_verbatim_quote"].encode("utf-8")
            ).hexdigest() == row["statement_sha256"]
            checked += 1
    assert checked == len(rows)
    print(
        f"VERIFIED: {checked} exact statements against {len(grouped)} frozen revision payloads"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--cache", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate")
    check.add_argument("manifest", type=Path)
    verify = sub.add_parser("verify-sources")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("--cache", type=Path, required=True)
    verify.add_argument("--claim-id")
    args = parser.parse_args()
    if args.command == "build":
        collect(args.cache, args.output)
    elif args.command == "validate":
        validate(args.manifest)
    else:
        verify_sources(args.manifest, args.cache, args.claim_id)


if __name__ == "__main__":
    main()
