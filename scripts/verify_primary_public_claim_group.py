#!/usr/bin/env python3
"""Verify one primary-source public-claim group without storing raw bytes."""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import urllib.request

import pdfplumber
from pypdf import PdfReader


def automatic_column_split(page) -> float:
    words = page.extract_words()
    candidates = []
    for x in range(int(page.width * 0.35), int(page.width * 0.65)):
        crossings = sum(word["x0"] < x < word["x1"] for word in words)
        candidates.append((crossings, x))
    minimum = min(value for value, _ in candidates)
    best = [x for value, x in candidates if value == minimum]
    runs = []
    for x in best:
        if not runs or x != runs[-1][-1] + 1:
            runs.append([x])
        else:
            runs[-1].append(x)
    run = min(runs, key=lambda values: abs(sum(values) / len(values) - page.width / 2))
    return sum(run) / len(run)

def normalized_text(
    payload: bytes,
    extractor: str = "pdfplumber",
    column_split_ratio: float | None = None,
) -> str:
    if extractor == "pdfplumber":
        with pdfplumber.open(BytesIO(payload)) as reader:
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif extractor == "pdfplumber_columns":
        with pdfplumber.open(BytesIO(payload)) as reader:
            parts = []
            for page in reader.pages:
                middle = (
                    page.width * column_split_ratio
                    if column_split_ratio is not None
                    else automatic_column_split(page)
                )
                parts.append(page.crop((0, 0, middle, page.height)).extract_text() or "")
                parts.append(page.crop((middle, 0, page.width, page.height)).extract_text() or "")
            text = "\n".join(parts)
    elif extractor == "pypdf":
        reader = PdfReader(BytesIO(payload))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        raise ValueError(f"unsupported text extractor: {extractor}")
    text = "\n".join(
        re.sub(r"^\d+\s+(?=[A-Za-z])", "", line)
        for line in text.splitlines()
    )
    # PDF extractors may retain discretionary line-break hyphens. Removing
    # whitespace and hyphens on both sides preserves the textual gate while
    # making the check independent of page layout.
    return re.sub(r"[\s-]+", "", text)


def verify(manifest_path: Path, source_file: Path | None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if source_file:
        payload = source_file.read_bytes()
    else:
        request = urllib.request.Request(
            manifest["source_url"], headers={"User-Agent": "ClaimBound/primary-claim-verifier"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
    actual_sha = hashlib.sha256(payload).hexdigest()
    text = normalized_text(
        payload,
        manifest.get("text_extractor", "pdfplumber"),
        manifest.get("column_split_ratio"),
    )
    independent_extractor = manifest.get("independent_text_extractor")
    independent_text = (
        normalized_text(payload, independent_extractor)
        if independent_extractor
        else None
    )
    rows = []
    for record in manifest["records"]:
        normalized_quote = re.sub(
            r"[\s-]+", "", record["public_claim_verbatim_quote"]
        )
        count = text.count(normalized_quote)
        independent_count = (
            independent_text.count(normalized_quote)
            if independent_text is not None
            else None
        )
        rows.append({
            "protocol_id": record["protocol_id"],
            "quote_occurrences": count,
            "independent_quote_occurrences": independent_count,
        })
    report = {
        "source_url": manifest["source_url"],
        "expected_source_sha256": manifest["source_sha256"],
        "actual_source_sha256": actual_sha,
        "source_hash_matches": actual_sha == manifest["source_sha256"],
        "independent_text_extractor": independent_extractor,
        "records": rows,
        "passed": actual_sha == manifest["source_sha256"] and all(
            row["quote_occurrences"] >= 1
            and (row["independent_quote_occurrences"] is None or row["independent_quote_occurrences"] >= 1)
            for row in rows
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-file", type=Path)
    args = parser.parse_args()
    report = verify(args.manifest, args.source_file)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
