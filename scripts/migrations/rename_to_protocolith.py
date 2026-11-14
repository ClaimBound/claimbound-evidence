#!/usr/bin/env python3
"""One-off migration ClaimBound Evidence -> Protocolith (roadmap phases P2 and P3).

Phases (idempotent: a second run finds nothing left to change):
  report  count what would change, list hash-pinned files, change nothing
  brand   rewrite brand text and rename files outside docs/evidence_cards
  cards   rename docs/evidence_cards/CLAIMBOUND-* to PLITH-*, add legacy_evidence_id,
          write docs/MIGRATION_ID_MAP.json (old id -> new id, old and new SHA-256)

Never touched: history documents, and any file whose SHA-256
is quoted by another tracked file (rewriting it would break a recorded hash).
Stdlib only. Run from the repository root.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import sys

CARDS_DIR = "docs/evidence_cards/"
MAP_PATH = "docs/MIGRATION_ID_MAP.json"
NEVER_TOUCH_PREFIXES = (".maintainer/", "scripts/migrations/")
HISTORY_FILES = {
    "CHANGELOG.md",
    "docs/AI_PROVENANCE_LOG.md",
    "docs/RELATED_WORK_AND_INDEPENDENCE.md",
    "LICENSE",
    "NOTICE",
    "uv.lock",
    MAP_PATH,
}
# Ordered, case-sensitive. Longer and more specific forms first.
RULES = [
    (r"raw\.githubusercontent\.com/ClaimBound/claimbound-evidence", "raw.githubusercontent.com/protocolith/protocolith"),
    (r"github\.com/ClaimBound/claimbound-evidence", "github.com/protocolith/protocolith"),
    (r"claimbound\.github\.io/claimbound-evidence", "protocolith.github.io/protocolith"),
    (r"github\.com/ClaimBound\b", "github.com/protocolith"),
    (r"(?:ClaimBound|Claimbound)[ -]Evidence", "Protocolith"),
    (r"CLAIMBOUND[ -]EVIDENCE", "PROTOCOLITH"),
    (r"claimbound_evidence", "protocolith"),
    (r"claimbound-evidence", "protocolith"),
    (r"CLAIMBOUND-", "PLITH-"),
    (r"CLAIMBOUND_", "PROTOCOLITH_"),
    (r"claimbound_", "protocolith_"),
    (r"claimbound-", "protocolith-"),
    (r"ClaimBound", "Protocolith"),
    (r"CLAIMBOUND", "PROTOCOLITH"),
    (r"claimbound", "protocolith"),
]
COMPILED = [(re.compile(p), r) for p, r in RULES]
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")


def rewrite(text: str) -> str:
    for rx, repl in COMPILED:
        text = rx.sub(repl, text)
    return text


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def read_text(path: str) -> str | None:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_pinned(files: list[str]) -> set[str]:
    """Tracked files whose SHA-256 is quoted inside some other tracked text file."""
    quoted: set[str] = set()
    for f in files:
        if f in HISTORY_FILES or not f.endswith((".json", ".md", ".yaml", ".yml", ".csv", ".txt")):
            continue
        text = read_text(f)
        if text:
            quoted.update(HEX64.findall(text))
    pinned = set()
    for f in files:
        if f.startswith(CARDS_DIR) or f.startswith(NEVER_TOUCH_PREFIXES):
            continue
        if os.path.isfile(f) and sha256_file(f) in quoted:
            pinned.add(f)
    return pinned


def untouchable(path: str) -> bool:
    return path in HISTORY_FILES or path.startswith(NEVER_TOUCH_PREFIXES)


def phase_report(files: list[str], pinned: set[str]) -> None:
    rewrite_n = rename_n = 0
    residual = collections.Counter()
    for f in files:
        if f.startswith(CARDS_DIR) or untouchable(f):
            continue
        text = read_text(f)
        if text is not None and f not in pinned and rewrite(text) != text:
            rewrite_n += 1
        if rewrite(f) != f and f not in pinned:
            rename_n += 1
        if f in pinned and text and re.search("claimbound", text, re.I):
            residual[f] += 1
    cards = [f for f in files if f.startswith(CARDS_DIR)]
    print(f"tracked files           : {len(files)}")
    print(f"cards-dir files         : {len(cards)}")
    print(f"brand files to rewrite  : {rewrite_n}")
    print(f"brand files to rename   : {rename_n}")
    print(f"hash-pinned (untouched) : {len(pinned)}")
    for f in sorted(pinned)[:15]:
        print("   pinned:", f)
    print(f"pinned files still naming the old brand: {len(residual)}")


def atomic_write(path: str, text: str) -> None:
    tmp = path + ".tmp-migrate"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, path)


def phase_brand(files: list[str], pinned: set[str]) -> None:
    changed = renamed = 0
    for f in files:
        if f.startswith(CARDS_DIR) or untouchable(f) or f in pinned or not os.path.isfile(f):
            continue
        text = read_text(f)
        if text is not None:
            new = rewrite(text)
            if new != text:
                atomic_write(f, new)
                changed += 1
    for f in files:
        if f.startswith(CARDS_DIR) or untouchable(f) or f in pinned or not os.path.isfile(f):
            continue
        dest = rewrite(f)
        if dest != f:
            if os.path.exists(dest):
                sys.exit(f"refusing to overwrite existing {dest} (from {f})")
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            os.rename(f, dest)
            renamed += 1
    print(f"rewrote {changed} files, renamed {renamed} files")


def with_legacy_field(new_text: str, legacy_id: str) -> str:
    """Insert legacy_evidence_id keeping key order and indentation when the card is plain JSON."""
    try:
        data = json.loads(new_text)
    except ValueError:
        return new_text
    if not isinstance(data, dict) or "legacy_evidence_id" in data:
        return new_text
    indent = 2 if new_text.startswith('{\n  "') else None
    data["legacy_evidence_id"] = legacy_id
    keys = list(data)
    if keys[:-1] == sorted(keys[:-1]):
        data = dict(sorted(data.items()))
    dumped = json.dumps(data, indent=indent, ensure_ascii=False)
    return dumped + ("\n" if new_text.endswith("\n") else "")


def phase_cards(files: list[str]) -> None:
    entries: dict[str, dict] = {}
    done = 0
    for f in files:
        if not f.startswith(CARDS_DIR) or not os.path.isfile(f):
            continue
        name = f[len(CARDS_DIR):]
        if not name.startswith("CLAIMBOUND-"):
            continue
        legacy_stem, ext = os.path.splitext(name)
        stem = rewrite(legacy_stem)
        dest = f"{CARDS_DIR}{stem}{ext}"
        if os.path.exists(dest):
            sys.exit(f"refusing to overwrite existing {dest}")
        old_sha = sha256_file(f)
        text = read_text(f)
        if text is None:
            sys.exit(f"card is not UTF-8 text: {f}")
        new = rewrite(text)
        if ext == ".json":
            new = with_legacy_field(new, legacy_stem)
        atomic_write(dest, new)
        os.remove(f)
        entry = entries.setdefault(stem, {"id": stem, "legacy_id": legacy_stem})
        entry[ext.lstrip(".")] = {"legacy_sha256": old_sha, "sha256": sha256_file(dest)}
        done += 1
    if entries:
        previous = {}
        if os.path.exists(MAP_PATH):
            with open(MAP_PATH, encoding="utf-8") as fh:
                previous = {e["id"]: e for e in json.load(fh)["entries"]}
        previous.update(entries)
        ordered = [previous[k] for k in sorted(previous)]
        lines = ",\n".join("    " + json.dumps(e, sort_keys=True, ensure_ascii=False) for e in ordered)
        header = (
            '{\n  "schema": "protocolith-id-map-v1",\n'
            '  "note": "Maps legacy ClaimBound evidence ids to PLITH ids with the SHA-256 of each '
            'file before and after the rename.",\n  "entries": [\n'
        )
        atomic_write(MAP_PATH, header + lines + "\n  ]\n}\n")
    print(f"migrated {done} card files, map has {len(entries)} new entries")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=("report", "brand", "cards"))
    phase = ap.parse_args().phase
    files = tracked()
    if phase == "cards":
        phase_cards(files)
        return
    pinned = hash_pinned(files)
    if phase == "report":
        phase_report(files, pinned)
    else:
        phase_brand(files, pinned)


if __name__ == "__main__":
    main()
