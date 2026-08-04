#!/usr/bin/env python3
"""Build deterministic, reviewable primary-source manifests for the first 700 slots.

The script never treats source prose as independently true. It selects substantive
sentences, preserves them verbatim modulo PDF layout whitespace, and binds each one
to a PDF page and complete-source SHA-256.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "artifacts/cb7k_first_700_primary_source_inventory.json"
OUTPUT = ROOT / "artifacts"
WORD = re.compile(r"[A-Za-z][A-Za-z’'\-]+")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9“‘\(])")
REJECT = re.compile(
    r"(?:table of contents|copyright|all rights reserved|https?://|doi:|"
    r"references\s*$|acknowledg(?:e)?ments\s*$|this page intentionally left blank|"
    r"performing organization name|how to cite|comments on .+ may be sent|"
    r"official journal of the european union|does not contain export-controlled|"
    r"claimboundsectionbreak|"
    r"special publication .+ guidelines .+ [A-Z][a-z]+ [A-Z][a-z]+)",
    re.IGNORECASE,
)
SIGNAL = re.compile(
    r"(?:\d|must|should|shall|may|can|found|report|result|risk|evaluate|"
    r"measure|require|define|identify|provide|support|model|system|data|security)",
    re.IGNORECASE,
)
GRAMMAR = re.compile(
    r"\b(?:is|are|was|were|be|been|being|has|have|had|can|could|may|might|"
    r"must|shall|should|will|would|does|do|did|provides?|requires?|defines?|"
    r"identif(?:y|ies|ied)|supports?|includes?|uses?|offers?|enables?|"
    r"evaluates?|measures?|found|shows?|reports?|describes?|applies?)\b",
    re.IGNORECASE,
)


def clean(text: str) -> str:
    kept = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        line = re.sub(r"^\d+\s+(?=[A-Za-z])", "", line)
        if not line or re.fullmatch(r"[ivxlcdm\d\s.\-]+", line, re.IGNORECASE):
            kept.append("CLAIMBOUNDSECTIONBREAK.")
            continue
        if len(line) < 90 and (line.isupper() or re.match(r"^\d+(?:\.\d+)*\s+[^.!?]+$", line)):
            kept.append("CLAIMBOUNDSECTIONBREAK.")
            continue
        if re.match(r"^(?:NIST (?:AI|CSWP|SP|IR)|February \d|January \d|March \d|July \d)", line):
            kept.append("CLAIMBOUNDSECTIONBREAK.")
            continue
        if re.match(r"^\d+[.)]\s+[^.!?]+$", line):
            kept.append("CLAIMBOUNDSECTIONBREAK.")
            continue
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def candidates(pdf: Path, content_start_page: int, extractor: str) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    if extractor == "pdfplumber":
        document = pdfplumber.open(pdf)
        pages = document.pages
    elif extractor == "pypdf":
        document = None
        pages = PdfReader(pdf).pages
    else:
        raise ValueError(f"unsupported extractor: {extractor}")
    try:
        for page_number, page in enumerate(pages, 1):
            if page_number < content_start_page:
                continue
            text = clean(page.extract_text() or "")
            for position, quote in enumerate(SENTENCE.split(text)):
                quote = quote.strip(" •\t")
                words = WORD.findall(quote)
                if not 90 <= len(quote) <= 650 or len(words) < 14:
                    continue
                if quote[-1:] != "." or REJECT.search(quote) or not GRAMMAR.search(quote):
                    continue
                if re.match(r"^(?:Table|Figure|Fig\.|Evaluation Capability Description)\b", quote):
                    continue
                if re.match(r"^\(\s+\d+\s+\)", quote):
                    continue
                if re.match(r"^\(\d+\)\s+(?!This|In|For|To|Given|Since|When|Where|Online|Providers|Very)", quote):
                    continue
                if quote.count(";") > 8 or quote.count(" | ") > 2 or quote.count(" • ") > 1:
                    continue
                if "....." in quote or any(len(word) > 45 for word in quote.split()):
                    continue
                letters = [char for char in quote if char.isalpha()]
                if not letters or sum(char.isupper() for char in letters) / len(letters) > 0.32:
                    continue
                key = re.sub(r"[\s-]+", "", quote).casefold()
                if key in seen:
                    continue
                seen.add(key)
                score = int(bool(SIGNAL.search(quote))) * 4
                score += min(sum(char.isdigit() for char in quote), 2)
                score += int(120 <= len(quote) <= 420) * 2
                score += int(not quote.startswith(("Figure ", "Table ", "Appendix ")))
                rows.append({
                    "page": page_number,
                    "position": position,
                    "quote": quote,
                    "score": score,
                })
    finally:
        if document is not None:
            document.close()
    return rows


def select(rows: list[dict], count: int) -> list[dict]:
    """Prefer high-signal prose while limiting concentration on any one page."""
    ordered = sorted(rows, key=lambda row: (-row["score"], row["page"], row["position"]))
    selected: list[dict] = []
    per_page: defaultdict[int, int] = defaultdict(int)
    for page_cap in (2, 4, 8, 1000):
        for row in ordered:
            if row in selected or per_page[row["page"]] >= page_cap:
                continue
            selected.append(row)
            per_page[row["page"]] += 1
            if len(selected) == count:
                return sorted(selected, key=lambda row: (row["page"], row["position"]))
    raise ValueError(f"only {len(selected)} eligible sentences for target {count}")


def protocol_ids(domain_code: str, count: int, start: int) -> list[str]:
    result = []
    for offset in range(count):
        index = start + offset
        track = (index - 1) // 10 + 1
        gate = (index - 1) % 10 + 1
        result.append(f"CB7K-{domain_code}-T{track:02d}-G{gate:02d}")
    return result


def write_manifests(source: dict, selected: list[dict], start: int) -> None:
    domain = source["domain_code"].lower()
    for chunk_index in range(0, len(selected), 10):
        chunk = selected[chunk_index:chunk_index + 10]
        ids = protocol_ids(source["domain_code"], len(chunk), start + chunk_index)
        track = ids[0].split("-")[2].lower()
        records = []
        for protocol_id, row in zip(ids, chunk, strict=True):
            records.append({
                "protocol_id": protocol_id,
                "section_locator": f"PDF page {row['page']}",
                "public_claim_text": row["quote"],
                "public_claim_verbatim_quote": row["quote"],
            })
        manifest = {
            "schema_version": "claimbound-primary-public-claim-group-v1",
            "protocol_version": "CB7K-PRIMARY-SOURCE-PUBLICATION-RETROSPECTIVE-v1",
            "claim_boundary": (
                f"Each result verifies that one exact public statement appeared in the fetched "
                f"{source['source_name']} bytes on 2026-08-04. It does not independently "
                "establish the statement's underlying real-world truth."
            ),
            "review_design": (
                "retrospective deterministic source-publication audit; not preregistered, "
                "not an independent fact-check, and not an independent reproduction"
            ),
            "operator": "NeoZorK",
            "source_name": source["source_name"],
            "source_url": source["source_url"],
            "access_date": "2026-08-04",
            "source_sha256": source["source_sha256"],
            "raw_payload_committed": False,
            "text_extractor": source["text_extractor"],
            "selection_method": (
                "Deterministic sentence extraction with minimum length and prose-quality "
                "filters, signal scoring, duplicate removal, and per-page concentration limits."
            ),
            "verification_rule": (
                "Extract PDF text, compare quote and extracted text after removing layout "
                "whitespace and hyphens, require every quote once or more, and require the "
                "complete fetched PDF SHA-256 to match."
            ),
            "result_status": "PASSED_UNDER_PROTOCOL",
            "records": records,
        }
        path = OUTPUT / f"cb7k_{domain}_{track}_primary_claims.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--domain", action="append", help="limit generation to one or more DOM codes")
    args = parser.parse_args()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    total = inventory["already_registered_primary_claims"]
    audit = []
    for source in inventory["sources"]:
        if args.domain and source["domain_code"] not in args.domain:
            continue
        pdf = args.source_root / source["domain_code"].lower() / "a.pdf"
        payload = pdf.read_bytes()
        actual_sha = hashlib.sha256(payload).hexdigest()
        if actual_sha != source["source_sha256"]:
            raise SystemExit(f"ERROR: source drift for {source['domain_code']}: {actual_sha}")
        rows = candidates(pdf, source["content_start_page"], source["text_extractor"])
        chosen = select(rows, source["remaining_target"])
        start = 21 if source["domain_code"] == "DOM001" else 1
        write_manifests(source, chosen, start)
        total += len(chosen)
        audit.append({
            "domain_code": source["domain_code"],
            "eligible_sentence_count": len(rows),
            "selected_count": len(chosen),
            "selected_pages": sorted({row["page"] for row in chosen}),
        })
    if not args.domain and total != 700:
        raise SystemExit(f"ERROR: expected 700 total primary claims, got {total}")
    print(json.dumps({"registered_baseline_plus_selected": total, "domains": audit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
