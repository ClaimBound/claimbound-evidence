# SPDX-License-Identifier: Apache-2.0
"""``atlas``: one self-contained, offline HTML page that lets a person browse experiments.

Sources are a local ledger store and/or directories of evidence card JSON files. The page embeds its data as one JSON
block, loads nothing from the network, and is byte-for-byte reproducible: the same input gives the same bytes.
The page script, style and markup are template files (``atlas_assets``); the UI strings are ``atlas_i18n/en.json`` plus
any translation files the user supplies.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import os
import re
import zlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from .errors import InputError, ProtocolithError, io_guard
from .issue import _atomic_write, build_card, card_hash
from .rules import Verdict, Verifier, scan
from .store import Store
from .views import protocol_of

DEFAULT_TITLE = "Protocolith atlas"
DEFAULT_OUT = "protocolith-atlas.html"
DEFAULT_CARDS_DIR = "docs/evidence_cards"
DATA_VERSION = 1
MAX_FILE_BYTES = 2_097_152
MAX_STRING = 2000
MAX_ITEMS = 100
MAX_DEPTH = 8
MAX_PROBLEMS = 20
MAX_ISSUES = 50
BLOCK_ROWS = 128
MAX_SOURCE_TEXT = 600

_CARD_COLUMNS = ("evidence_id", "protocol_id", "result_status", "domain", "reproduction_level", "claim_boundary")
_DATE_KEYS = ("created_at", "last_verified_date", "access_date")
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_LANG_RE = re.compile(r"[a-z]{2,3}(-[A-Za-z0-9]{2,8})*")
_CONTROL_RE = re.compile("[\x00-\x1f\x7f]")
_PLACEHOLDER_RE = re.compile(r"\{\{(T:)?(\w+)\}\}")


@dataclass
class AtlasResult:
    """The page bytes plus what a caller needs to report: counts, warnings and whether the ledger verified."""

    html: bytes
    ok: bool
    total: int
    shown: int
    skipped: int
    warnings: list[str] = field(default_factory=list)
    ledger: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "bytes": len(self.html),
            "cards": self.total,
            "ledger": self.ledger,
            "ok": self.ok,
            "shown": self.shown,
            "skipped": self.skipped,
            "warnings": self.warnings,
        }


def _asset(name: str) -> str:
    return (resources.files("protocolith.core") / "atlas_assets" / name).read_text(encoding="utf-8")


def english_catalog() -> dict[str, str]:
    """The shipped English UI strings, key to text (``_name`` is the language's own name)."""
    text = (resources.files("protocolith.core") / "atlas_i18n" / "en.json").read_text(encoding="utf-8")
    catalog: dict[str, str] = json.loads(text)
    return catalog


def _read_translation(path: Path, english: dict[str, str], warnings: list[str]) -> dict[str, str] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        warnings.append(f"{path.name}: not readable as UTF-8 JSON; skipped")
        return None
    if not isinstance(data, dict):
        warnings.append(f"{path.name}: must be a JSON object; skipped")
        return None
    clean: dict[str, str] = {}
    for key, value in data.items():
        if key not in english:
            warnings.append(f"{path.name}: unknown key {key!r} ignored")
        elif not isinstance(value, str):
            warnings.append(f"{path.name}: value of {key!r} must be a string; ignored")
        elif value:  # an empty value is an untranslated template entry
            clean[key] = value
    return clean


def load_languages(i18n_dir: str | os.PathLike[str] | None) -> tuple[dict[str, dict[str, str]], list[str]]:
    """English plus every ``<code>.json`` in ``i18n_dir``; missing keys fall back to English. Returns (languages, warnings)."""
    english = english_catalog()
    languages = {"en": dict(english)}
    warnings: list[str] = []
    if i18n_dir is None:
        return languages, warnings
    folder = Path(i18n_dir)
    if not folder.is_dir():
        raise InputError("BAD_PATH", f"{i18n_dir}: not a directory")
    with io_guard():
        names = sorted(item.name for item in folder.iterdir() if item.name.endswith(".json") and item.is_file())
    for name in names:
        code = name[: -len(".json")]
        if code == "en" or not _LANG_RE.fullmatch(code):
            warnings.append(f"{name}: not a usable language code (English is built in); skipped")
            continue
        translation = _read_translation(folder / name, english, warnings)
        if translation is not None:
            merged = {**english, **translation}
            merged["_name"] = _CONTROL_RE.sub(" ", merged["_name"])[:60] if "_name" in translation else code
            languages[code] = merged
    return languages, warnings


def _clip(value: Any, depth: int = 0) -> Any:
    """Bound string length, list length and nesting so one hostile card cannot bloat the page."""
    if isinstance(value, str):
        if len(value) <= MAX_STRING:
            return value
        return f"{value[:MAX_STRING]}... [clipped {len(value) - MAX_STRING} characters]"
    if isinstance(value, (list, dict)) and depth >= MAX_DEPTH:
        return "[clipped: nested too deeply]"
    if isinstance(value, list):
        items = [_clip(item, depth + 1) for item in value[:MAX_ITEMS]]
        if len(value) > MAX_ITEMS:
            items.append(f"[clipped {len(value) - MAX_ITEMS} items]")
        return items
    if isinstance(value, dict):
        return {str(key)[:200]: _clip(item, depth + 1) for key, item in value.items()}
    return value


def _finite(text: str) -> float:
    number = float(text)
    if not math.isfinite(number):
        raise ValueError("number out of range")
    return number


def _no_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


Pair = tuple[list[Any], dict[str, Any]]


def _row(card: dict[str, Any], digest: str) -> Pair:
    """A compact table row and the other fields of the card (they travel compressed, in blocks)."""
    clipped = _clip(card)
    in_columns = {key for key in _CARD_COLUMNS if isinstance(card.get(key), str)}
    columns = [clipped[key] if key in in_columns else None for key in _CARD_COLUMNS]
    extra = {key: value for key, value in clipped.items() if key not in in_columns}
    stamps = (card.get(key) for key in _DATE_KEYS)
    date = next((s[:10] for s in stamps if isinstance(s, str) and _DATE_RE.match(s)), "")
    found = [card.get("official_source_name"), card.get("official_source_url"), card.get("sources")]
    text = "\n".join(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) for v in found if v)
    # row layout: id, protocol, status, domain, level, date, claim, hash, source text (see atlas.js)
    row = [*columns[:5], date, columns[5], digest, text[:MAX_SOURCE_TEXT]]
    return row, extra


def _blocks(extras: list[dict[str, Any]]) -> list[str]:
    """Per-block deflate+base64 of the other card fields; the page decodes a block only when a record is opened."""
    blocks = []
    for start in range(0, len(extras), BLOCK_ROWS):
        raw = json.dumps(extras[start : start + BLOCK_ROWS], ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        blocks.append(base64.b64encode(zlib.compress(raw.encode("ascii"), 6)).decode("ascii"))
    return blocks


def _scan_dir(root: Path) -> list[Path]:
    found: list[Path] = []
    for here, dirs, files in os.walk(root):
        dirs.sort()
        found += [Path(here) / name for name in sorted(files) if name.lower().endswith(".json")]
    return found


def _read_card(path: Path) -> tuple[dict[str, Any], str] | str:
    """The card and the sha256 of its file bytes, or the reason the file is skipped."""
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return "larger than 2 MiB"
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        data = json.loads(text, parse_float=_finite, parse_constant=_no_constant)
    except OSError:
        return "unreadable"
    except (ValueError, RecursionError):
        return "not valid UTF-8 JSON"
    ident = data.get("evidence_id") if isinstance(data, dict) else None
    if not (isinstance(ident, str) and ident and isinstance(data.get("result_status"), str)):
        return "not an evidence card (needs evidence_id and result_status)"
    return data, hashlib.sha256(raw).hexdigest()


def _from_cards(folders: Sequence[str | os.PathLike[str]]) -> tuple[list[Pair], list[dict[str, str]]]:
    rows: list[Pair] = []
    issues: list[dict[str, str]] = []
    for folder in folders:
        root = Path(folder)
        if not root.is_dir():
            raise InputError("BAD_PATH", f"{folder}: not a directory")
        with io_guard():
            paths = _scan_dir(root)
        for path in paths:
            found = _read_card(path)
            if isinstance(found, str):
                issues.append({"path": path.relative_to(root).as_posix(), "reason": found})
            else:
                rows.append(_row(*found))
    return rows, issues


def _ledger_card(verifier: Verifier, seq: int) -> dict[str, Any]:
    entry = verifier.entries[seq]
    body = entry["body"]
    try:
        return build_card(verifier, seq)
    except (ProtocolithError, KeyError, TypeError):  # a tampered ledger: show what the record itself says
        return {
            "claim_boundary": body.get("claim_boundary"),
            "created_at": entry["ts"],
            "evidence_id": f"LEDGER-RECORD-{seq:06d}",
            "ledger_record_seq": seq,
            "protocol_id": protocol_of(verifier, entry),
            "reproduction_level": body.get("reproduction_level"),
            "result_status": body.get("status"),
        }


def _from_ledger(store: Store) -> tuple[list[Pair], dict[str, Any]]:
    with io_guard(), store.locked(write=False):
        verdict, verifier = scan(store.read(missing_ok=False), card_hash)
    rows = [
        _row(_ledger_card(verifier, seq), verifier.entries[seq]["hash"])
        for seq in sorted(verifier.entries)
        if verifier.entries[seq]["type"] == "record"
    ]
    return rows, _ledger_integrity(verdict)


def _ledger_integrity(verdict: Verdict) -> dict[str, Any]:
    problems = [v.to_dict() for v in verdict.violations[:MAX_PROBLEMS]]
    return {
        "count": verdict.count,
        "head_hash": verdict.head_hash,
        "head_seq": verdict.head_seq,
        "kind": "ledger",
        "ok": verdict.ok,
        "problem_count": len(verdict.violations),
        "problems": problems,
    }


def _embed(data: Any) -> str:
    """Canonical-ish JSON that cannot end a script block or smuggle markup: ASCII only, no raw < > &."""
    text = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _title(title: str) -> str:
    if not (isinstance(title, str) and title.strip()):
        raise InputError("BAD_ENTRY", "title must be a non-empty string")
    return _CONTROL_RE.sub(" ", title).strip()[:200]


def _auto_sources(
    store: Store | str | os.PathLike[str] | None, cards: Sequence[str | os.PathLike[str]]
) -> tuple[Store | None, Sequence[str | os.PathLike[str]]]:
    if store is not None or cards:
        return (None if store is None else store if isinstance(store, Store) else Store(store)), cards
    from .store import resolve_store

    local = resolve_store(None)
    if local.ledger_path.is_file():
        return local, ()
    if Path(DEFAULT_CARDS_DIR).is_dir():
        return None, (DEFAULT_CARDS_DIR,)
    raise InputError("NO_SOURCE", f"no ledger at {local.path} and no {DEFAULT_CARDS_DIR}; pass --store or --cards")


def build_atlas_result(
    *,
    store: Store | str | os.PathLike[str] | None = None,
    cards: Sequence[str | os.PathLike[str]] = (),
    title: str = DEFAULT_TITLE,
    i18n_dir: str | os.PathLike[str] | None = None,
    default_lang: str = "en",
    max_rows: int | None = None,
) -> AtlasResult:
    """Build the page. With no ``store`` and no ``cards`` a local ledger, else ``docs/evidence_cards``, is used."""
    if max_rows is not None and not (type(max_rows) is int and max_rows >= 1):
        raise InputError("BAD_ENTRY", "max_rows must be an integer of at least 1")
    page_title = _title(title)
    languages, warnings = load_languages(i18n_dir)
    if default_lang not in languages:
        raise InputError(
            "BAD_LANG", f"default language {default_lang!r} is not available: " + ", ".join(sorted(languages))
        )
    real_store, folders = _auto_sources(store, cards)
    rows: list[Pair] = []
    integrity: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    ledger = None
    if real_store is not None:
        rows, ledger = _from_ledger(real_store)
        integrity.append(ledger)
    if folders:
        found, issues = _from_cards(folders)
        rows += found
        integrity.append({"count": len(found), "kind": "cards"})
    seen: set[str] = set()
    unique = []
    for pair in rows:
        if pair[0][0] not in seen:
            seen.add(pair[0][0])
            unique.append(pair)
    if len(unique) < len(rows):
        warnings.append(f"{len(rows) - len(unique)} records with an already used evidence id were left out")
    unique.sort(key=lambda pair: pair[0][0])
    unique.sort(key=lambda pair: pair[0][5], reverse=True)
    statuses: dict[str, int] = {}
    for pair in unique:
        statuses[pair[0][2]] = statuses.get(pair[0][2], 0) + 1
    shown = unique if max_rows is None else unique[:max_rows]
    data = {
        "block": BLOCK_ROWS,
        "blocks": _blocks([extra for _, extra in shown]),
        "i18n": {"default": default_lang, "langs": languages},
        "integrity": integrity,
        "issues": {"count": len(issues), "items": issues[:MAX_ISSUES]},
        "rows": [row for row, _ in shown],
        "shown": len(shown),
        "statuses": dict(sorted(statuses.items())),
        "title": page_title,
        "total": len(unique),
        "v": DATA_VERSION,
    }
    english = languages["en"]
    fill = {
        "CSS": _asset("atlas.css"),
        "DATA": _embed(data),
        "JS": _asset("atlas.js"),
        "LANG": default_lang,
        "TITLE": html.escape(page_title),
    }

    def replace(found: re.Match[str]) -> str:
        return html.escape(english[found.group(2)]) if found.group(1) else fill[found.group(2)]

    page = _PLACEHOLDER_RE.sub(replace, _asset("atlas.html")).encode("utf-8")
    ok = all(group.get("ok", True) for group in integrity)
    return AtlasResult(page, ok, len(unique), len(shown), len(issues), warnings, ledger)


def build_atlas(**options: Any) -> bytes:
    """The atlas page as bytes; see :func:`build_atlas_result` for the options."""
    return build_atlas_result(**options).html


def write_atlas(page: bytes, out: str | os.PathLike[str] = DEFAULT_OUT) -> Path:
    """Write the page atomically. ``out`` is a ``.html`` file, or a directory (existing, or without that suffix)."""
    target = Path(out)
    is_file = (
        target.suffix.lower() in (".html", ".htm") and not target.is_dir() and not str(out).endswith(("/", os.sep))
    )
    path = target if is_file else target / DEFAULT_OUT
    with io_guard():
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(path, page)
    return path


def confine(name: object, base: Path | None = None) -> Path:
    """A path that stays inside ``base`` (default: the working directory) after links are resolved."""
    if not isinstance(name, str) or not name:
        raise InputError("BAD_PATH", "a path must be a non-empty string")
    with io_guard():
        root = (base or Path.cwd()).resolve()
        path = (root / name).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise InputError("BAD_PATH", f"{name}: the path is outside the current directory") from None
    return path
