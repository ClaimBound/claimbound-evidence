#!/usr/bin/env python3
"""Build deterministic, reviewable primary-source manifests from an inventory.

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
    r"claimboundsectionbreak|contains nonbinding recommendations|[]|\(fig\.$|"
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
EXTRACT_ARTEFACT = re.compile(
    r"(?:^|\s)(?:è|©)(?:\s|$)|"
    r"^(?:Dotted and dashed lines|Section \d+(?:\.\d+)? was prepared by|"
    r"Acknowledg(?:e)?ments|References)\b|"
    r"\b(?:prepared by|prepared with inputs from)\b|"
    r"\b\w+\s+-\s+\w+\b|"
    r"\b(?:nearly|over|under|above|from|to)\s+(?:and|the|percentage|million|billion)\b|"
    r"\b(?:percent|percentage point)\s+(?:above|below|in|of)\b",
    re.IGNORECASE,
)
PROSE_INTEGRITY_ARTEFACT = re.compile(
    r"\b[A-Z]\s+able\b|"
    r"\.\s+[a-z]|"
    r"\b(?:Key messages|Examples include|Data and methodology used in this chapter|"
    r"Context|Selection)\s+[A-Z]|"
    r"\b(?:See|All)\s+r\s*eferences\b|"
    r"\b(?:Table|Figure)\s*\d|"
    r"\b[A-Za-z]+\s+\d+\s*\.\s*n\.r\.\s*=",
    re.IGNORECASE,
)
# A PDF text layer can insert spaces inside a word or a number.  Those strings can
# still be found by a mechanical re-extraction, but are not faithful public claims
# a reader could quote.  Reject them rather than treating text-search success as a
# semantic pass.
OCR_OR_LAYOUT_ARTEFACT = re.compile(
    r"\b(?:DAL|QAL|YLD|YLL)\s+Ys?\b|"
    r"\b\d\s+\d{1,2}(?:[.,]\d+)?\b|"
    r"\b\d{1,2}\s+\d{3}\b|"
    r"\b(?:Fig|Figs|Table|Tables)\.$|"
    r"\b(?:and|or|of|to|in|for|with|from)\s*$",
    re.IGNORECASE,
)


def automatic_column_split(page) -> float:
    """Find the least text-dense vertical gutter near the page centre."""
    words = page.extract_words()
    candidates = []
    for x in range(int(page.width * 0.35), int(page.width * 0.65)):
        crossings = sum(word["x0"] < x < word["x1"] for word in words)
        candidates.append((crossings, x))
    minimum = min(value for value, _ in candidates)
    best = [x for value, x in candidates if value == minimum]
    runs: list[list[int]] = []
    for x in best:
        if not runs or x != runs[-1][-1] + 1:
            runs.append([x])
        else:
            runs[-1].append(x)
    run = min(runs, key=lambda values: abs(sum(values) / len(values) - page.width / 2))
    return sum(run) / len(run)


def clean(text: str) -> str:
    kept = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        line = re.sub(r"^\d+\s+(?=[A-Za-z•])", "", line)
        line = re.sub(r"^[•]\s*", "", line)
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
    # Turn discretionary line-break hyphens into spaces, but retain semantic
    # hyphens in uppercase compounds such as WHO-UNICEF-UNFPA.
    def repair_line_hyphen(match: re.Match[str]) -> str:
        word = match.group("word")
        return f"{word}{'-' if word.isupper() else ' '}{match.group('next')}"

    text = re.sub(
        r"(?P<word>[A-Za-z]+)-\s*\n\s*(?P<next>[A-Za-z])",
        repair_line_hyphen,
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def normalized_document_text(pdf: Path, extractor: str) -> str:
    """Return layout-normalized text from a separate PDF implementation."""
    if extractor == "pypdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)
    elif extractor == "pdfplumber":
        with pdfplumber.open(pdf) as document:
            text = "\n".join(page.extract_text() or "" for page in document.pages)
    else:
        raise ValueError(f"unsupported independent text extractor: {extractor}")
    # Keep this normalization aligned with the publication verifier: remove
    # extractor-specific page-number prefixes before collapsing layout
    # whitespace/hyphens.  The independent gate below must match the complete
    # candidate quote, not merely a weak key fragment.
    text = "\n".join(
        re.sub(r"^\d+\s+(?=[A-Za-z])", "", line)
        for line in text.splitlines()
    )
    return re.sub(r"[\s-]+", "", text)


def candidates(
    pdf: Path,
    content_start_page: int,
    extractor: str,
    min_quote_characters: int = 90,
    min_quote_words: int = 14,
    excluded_keys: set[str] | None = None,
    column_split_ratio: float | None = None,
    content_end_page: int | None = None,
    reject_pattern: str | None = None,
    independent_extractor: str | None = None,
) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set(excluded_keys or ())
    independent_text = (
        normalized_document_text(pdf, independent_extractor)
        if independent_extractor
        else None
    )
    if extractor in {"pdfplumber", "pdfplumber_columns"}:
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
            if content_end_page is not None and page_number > content_end_page:
                continue
            if extractor == "pdfplumber_columns":
                middle = (
                    page.width * column_split_ratio
                    if column_split_ratio is not None
                    else automatic_column_split(page)
                )
                page_texts = [
                    page.crop((0, 0, middle, page.height)).extract_text() or "",
                    page.crop((middle, 0, page.width, page.height)).extract_text() or "",
                ]
            else:
                page_texts = [page.extract_text() or ""]
            page_quotes = []
            for page_text in page_texts:
                page_quotes.extend(SENTENCE.split(clean(page_text)))
            for position, quote in enumerate(page_quotes):
                quote = quote.strip(" •\t")
                words = WORD.findall(quote)
                if not min_quote_characters <= len(quote) <= 650 or len(words) < min_quote_words:
                    continue
                if (
                    quote[-1:] != "."
                    or REJECT.search(quote)
                    or EXTRACT_ARTEFACT.search(quote)
                    or PROSE_INTEGRITY_ARTEFACT.search(quote)
                    or OCR_OR_LAYOUT_ARTEFACT.search(quote)
                    or (reject_pattern and re.search(reject_pattern, quote, re.IGNORECASE))
                    or not GRAMMAR.search(quote)
                ):
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
                key = re.sub(r"[\s-]+", "", quote)
                # Require the complete quote with original casing in the
                # independent extraction.  Case-folding here would permit a
                # quote that the publication verifier cannot reproduce.
                if independent_text is not None and key not in independent_text:
                    continue
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


def write_manifests(source: dict, selected: list[dict], start: int, access_date: str) -> None:
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
                f"{source['source_name']} bytes on {access_date}. It does not independently "
                "establish the statement's underlying real-world truth."
            ),
            "review_design": (
                "retrospective deterministic source-publication audit; not preregistered, "
                "not an independent fact-check, and not an independent reproduction"
            ),
            "operator": "NeoZorK",
            "source_name": source["source_name"],
            "source_url": source["source_url"],
            "access_date": access_date,
            "source_sha256": source["source_sha256"],
            "raw_payload_committed": False,
            "text_extractor": source["text_extractor"],
            # A second implementation must recover the same quote before a new
            # batch is eligible for registration.  This prevents a pass that is
            # merely an artefact of the extractor that selected the sentence.
            "independent_text_extractor": source.get(
                "independent_text_extractor",
                "pdfplumber" if source["text_extractor"] == "pypdf" else "pypdf",
            ),
            **(
                {"column_split_ratio": source["column_split_ratio"]}
                if "column_split_ratio" in source
                else {}
            ),
            "selection_method": (
                "Deterministic sentence extraction with minimum length and prose-quality "
                "filters, signal scoring, duplicate removal, and per-page concentration limits."
            ),
            "verification_rule": (
                "Extract PDF text with the selecting extractor and an independent extractor, "
                "compare each quote after removing layout whitespace and hyphens, require every "
                "quote once or more in both extractions, and require the complete fetched PDF "
                "SHA-256 to match."
            ),
            "result_status": "PASSED_UNDER_PROTOCOL",
            "records": records,
        }
        path = OUTPUT / f"cb7k_{domain}_{track}_primary_claims.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=INVENTORY)
    parser.add_argument("--domain", action="append", help="limit generation to one or more DOM codes")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    total = inventory["already_registered_primary_claims"]
    target_domains = {
        source["domain_code"]
        for source in inventory["sources"]
        if not args.domain or source["domain_code"] in args.domain
    }
    excluded_keys: set[str] = set()
    for path in OUTPUT.glob("cb7k_dom*_primary_claims.json"):
        match = re.match(r"cb7k_(dom\d{3})_", path.name)
        if match and match.group(1).upper() in target_domains:
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for record in manifest.get("records", []):
            quote = record.get("public_claim_verbatim_quote", "")
            excluded_keys.add(re.sub(r"[\s-]+", "", quote).casefold())
    audit = []
    for source in inventory["sources"]:
        if args.domain and source["domain_code"] not in args.domain:
            continue
        pdf = args.source_root / source.get("source_subdir", source["domain_code"].lower()) / "a.pdf"
        payload = pdf.read_bytes()
        actual_sha = hashlib.sha256(payload).hexdigest()
        if actual_sha != source["source_sha256"]:
            raise SystemExit(f"ERROR: source drift for {source['domain_code']}: {actual_sha}")
        rows = candidates(
            pdf,
            source["content_start_page"],
            source["text_extractor"],
            source.get("min_quote_characters", 90),
            source.get("min_quote_words", 14),
            excluded_keys,
            source.get("column_split_ratio"),
            source.get("content_end_page"),
            source.get("reject_pattern"),
            source.get(
                "independent_text_extractor",
                "pdfplumber" if source["text_extractor"] == "pypdf" else "pypdf",
            ),
        )
        chosen = select(rows, source["remaining_target"])
        start = source.get("start_index", 21 if source["domain_code"] == "DOM001" else 1)
        write_manifests(source, chosen, start, inventory["created_at"])
        excluded_keys.update(
            re.sub(r"[\s-]+", "", row["quote"]).casefold() for row in chosen
        )
        total += len(chosen)
        audit.append({
            "domain_code": source["domain_code"],
            "eligible_sentence_count": len(rows),
            "selected_count": len(chosen),
            "selected_pages": sorted({row["page"] for row in chosen}),
        })
    expected_total = inventory.get("expected_total_primary_claims", 700)
    if not args.domain and total != expected_total:
        raise SystemExit(f"ERROR: expected {expected_total} total primary claims, got {total}")
    print(json.dumps({"registered_baseline_plus_selected": total, "domains": audit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
