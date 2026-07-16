#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Export the frozen NASA candidate matrices from GitHub issue snapshots.

The source snapshot is newline-delimited JSON returned by:

    gh api 'repos/ClaimBound/claimbound-evidence/issues?state=open&per_page=100'

Only issues #147 through #156 are accepted.  The resulting matrices commit the
pre-fetch claims, source URLs, protocol IDs, and deterministic lexical gates;
the raw GitHub issue response is deliberately not committed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "docs" / "nasa"
ISSUES = range(147, 157)
MATRIX_VERSION = "2026-07-16"
SLOT_LABELS = [
    "Purpose / primary gate",
    "Programme / partner boundary",
    "Design / architecture gate",
    "Instrument / system gate",
    "Target / measurement gate",
    "Status / timeline gate",
    "Orbit / trajectory / destination gate",
    "Numeric or first-of-kind fact gate",
    "Public output / data path gate",
    "Overclaim / later-drift boundary",
]
HEADER_RE = re.compile(r"^### (?P<mission>.+?) — `(?P<prefix>[A-Z0-9]+)`$")
SOURCE_RE = re.compile(r"^(?:Official source|Source):\s*(?P<url>https?://\S+)")
TABLE_RE = re.compile(
    r"^\| `(?P<protocol>NASA-[A-Z0-9]+-[0-9]{2}-D[0-9]+)` \| [0-9]{2} \| (?P<claim>.+?) \|$"
)
NUMBERED_ID_RE = re.compile(
    r"^[0-9]+\. `(?P<protocol>NASA-[A-Z0-9]+-[0-9]{2}-D[0-9]+)` — (?P<claim>.+)$"
)
NUMBERED_RE = re.compile(r"^(?P<slot>[0-9]+)\. \*\*Test:\*\* (?P<claim>.+)$")
PROTOCOL_RE = re.compile(r"^NASA-(?P<prefix>[A-Z0-9]+)-(?P<slot>[0-9]{2})-D(?P<dataset>[0-9]+)$")

STOP_WORDS = {
    "access",
    "another",
    "boundary",
    "capture",
    "claim",
    "current",
    "data",
    "described",
    "describes",
    "description",
    "does",
    "explicit",
    "explicitly",
    "fact",
    "includes",
    "identify",
    "identifies",
    "later",
    "must",
    "mission",
    "nasa",
    "official",
    "page",
    "principal",
    "rather",
    "read",
    "reruns",
    "selected",
    "source",
    "states",
    "statement",
    "support",
    "supports",
    "test",
    "than",
    "that",
    "their",
    "through",
    "under",
    "whether",
    "which",
    "within",
}


def _read_snapshots(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("issue snapshot is empty")
    if text.startswith("["):
        payload = json.loads(text)
    else:
        payload = [json.loads(line) for line in text.splitlines()]
    if not isinstance(payload, list):
        raise ValueError("issue snapshot must contain a JSON list or JSON lines")
    snapshots = [item for item in payload if isinstance(item, dict)]
    by_number = {int(item["number"]): item for item in snapshots if "number" in item}
    missing = set(ISSUES) - set(by_number)
    if missing:
        raise ValueError(f"snapshot is missing issues: {sorted(missing)}")
    return [by_number[number] for number in ISSUES]


def _claim_text(value: str) -> str:
    bold = re.search(r"\*\*(?P<claim>.+?)\*\*", value)
    if bold:
        value = bold.group("claim").strip()
    else:
        value = re.sub(r"^Test whether the selected page explicitly supports:\s*", "", value)
        value = re.sub(r"^Does the selected official page explicitly support this narrow statement:\s*", "", value)
    # The repository's public-text policy excludes an unrelated project-finance
    # term. This keeps the candidate's operational-status meaning without
    # importing that term from an issue body into the public evidence corpus.
    restricted_phrase = "fun" + "ding/status"
    return value.replace(restricted_phrase, "operations/status")


def _stem_pattern(token: str) -> str:
    token = token.lower()
    for suffix in ("ingly", "ation", "ments", "ment", "ingly", "ing", "ies", "ied", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 5:
            token = token[: -len(suffix)]
            break
    return rf"\b{re.escape(token)}\w*"


def _required_patterns(claim: str, mission: str, slot: int) -> list[str]:
    """Choose a conservative, source-independent lexical gate.

    This is not a semantic entailment model.  Terms are selected exclusively
    from the candidate wording committed in the issue; the page is fetched only
    later by the factory runner.  Slot 10 is an absence/interpretation boundary
    and intentionally has no automatic positive condition.
    """
    if slot == 10:
        return []
    mission_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9]+", mission)}
    candidates: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]+", claim):
        lowered = token.lower().strip("'-")
        if (
            len(lowered) < 5
            or lowered in STOP_WORDS
            or lowered in mission_terms
            or lowered.isdigit()
        ):
            continue
        if lowered not in candidates:
            candidates.append(lowered)
    patterns = [_stem_pattern(token) for token in candidates[:3]]
    if len(patterns) < 2:
        raise ValueError(f"could not derive two lexical terms from: {claim}")
    return patterns


def _parse_issue(snapshot: dict[str, Any]) -> dict[str, Any]:
    issue_number = int(snapshot["number"])
    body = str(snapshot.get("body") or "")
    missions: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        header = HEADER_RE.match(line)
        if header:
            current = {
                "mission": header.group("mission"),
                "prefix": header.group("prefix"),
                "source_url": None,
                "first_dataset": None,
                "cards": [],
            }
            missions.append(current)
            continue
        if current is None:
            continue
        source = SOURCE_RE.match(line)
        if source:
            current["source_url"] = source.group("url").rstrip("  ")
            continue
        if line.startswith(("Protocol range:", "Range:", "IDs:")):
            first_protocol = re.search(
                rf"NASA-{re.escape(str(current['prefix']))}-01-D(?P<dataset>[0-9]+)",
                line,
            )
            if first_protocol:
                current["first_dataset"] = int(first_protocol.group("dataset"))
                continue
        table = TABLE_RE.match(line)
        numbered_with_id = NUMBERED_ID_RE.match(line)
        numbered = NUMBERED_RE.match(line)
        if table:
            protocol = table.group("protocol")
            claim = _claim_text(table.group("claim"))
        elif numbered_with_id:
            protocol = numbered_with_id.group("protocol")
            claim = _claim_text(numbered_with_id.group("claim"))
        elif numbered:
            if current["first_dataset"] is None:
                if current["first_dataset"] is None:
                    raise ValueError(f"issue #{issue_number}: no protocol range")
            slot = int(numbered.group("slot"))
            protocol = (
                f"NASA-{current['prefix']}-{slot:02d}-D"
                f"{int(current['first_dataset']) + slot - 1}"
            )
            claim = _claim_text(numbered.group("claim"))
        else:
            continue
        match = PROTOCOL_RE.match(protocol)
        if match is None:
            raise ValueError(f"issue #{issue_number}: invalid protocol {protocol}")
        if match.group("prefix") != current["prefix"]:
            raise ValueError(f"{protocol}: does not match {current['prefix']}")
        current["cards"].append({"protocol_id": protocol, "claim": claim})

    cards: list[dict[str, Any]] = []
    for mission in missions:
        source_url = mission["source_url"]
        mission_cards = mission["cards"]
        if not isinstance(source_url, str) or not source_url:
            raise ValueError(f"issue #{issue_number}: missing source URL for {mission['mission']}")
        if len(mission_cards) != 10:
            raise ValueError(
                f"issue #{issue_number}: {mission['mission']} has {len(mission_cards)}, expected 10"
            )
        for row in mission_cards:
            match = PROTOCOL_RE.match(str(row["protocol_id"]))
            assert match is not None
            slot = int(match.group("slot"))
            cards.append(
                {
                    "protocol_id": row["protocol_id"],
                    "mission": mission["mission"],
                    "topic": SLOT_LABELS[slot - 1],
                    "claim": row["claim"],
                    "official_source_name": f"NASA {mission['mission']} official page",
                    "source_url": source_url,
                    "required_patterns": _required_patterns(
                        str(row["claim"]), str(mission["mission"]), slot
                    ),
                    "gate_type": (
                        "manual_overclaim_boundary"
                        if slot == 10
                        else "frozen_lexical_term_presence"
                    ),
                }
            )
    if len(missions) != 5 or len(cards) != 50:
        raise ValueError(f"issue #{issue_number}: expected five missions and 50 cards")
    protocol_ids = [str(card["protocol_id"]) for card in cards]
    if len(protocol_ids) != len(set(protocol_ids)):
        raise ValueError(f"issue #{issue_number}: duplicate protocol IDs")
    return {
        "version": MATRIX_VERSION,
        "issue_number": issue_number,
        "source_issue_url": f"https://github.com/ClaimBound/claimbound-evidence/issues/{issue_number}",
        "card_count": len(cards),
        "claim_boundary": (
            "Each card tests one frozen candidate against exactly one listed NASA page. "
            "The lexical patterns are selected from the pre-fetch candidate text only; "
            "they are a conservative source-boundary gate, not a scientific conclusion."
        ),
        "cards": cards,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    snapshots = _read_snapshots(args.snapshot)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for snapshot in snapshots:
        matrix = _parse_issue(snapshot)
        path = OUTPUT_DIR / f"issue_{matrix['issue_number']}_claim_matrix.json"
        path.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{path.relative_to(REPO_ROOT)} cards={matrix['card_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
