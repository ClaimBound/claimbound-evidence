# SPDX-License-Identifier: Apache-2.0
"""External anchoring of the ledger head, and verification of the anchors later.

An anchor statement is canonical JSON naming the head of the ledger. Its sha256 is the ``anchor_id``. Local anchor files
live in ``<store>/anchors``; the statement can also be stamped by an RFC 3161 time-stamp authority, archived by the Wayback
Machine, tagged in git, or written to a file that you publish yourself. All network and subprocess access goes through
injectable callables, and nothing networked or git-related happens unless asked for.
"""

from __future__ import annotations

import hashlib
import http.client
import os
import re
import secrets
import subprocess
import tempfile
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import CanonError, decode, encode, sha256_hex
from .capture import _version
from .clock import Clock, now_utc
from .errors import EnvError, InputError, VerificationFailed, Violation, io_guard
from .issue import card_hash
from .ledger import is_hash, is_ts
from .rules import Verifier, scan
from .store import Store

STATEMENT_KIND = "protocolith-anchor"
MAX_RESPONSE = 1 << 20
TIMEOUT = 30.0
WAYBACK_HOST = "web.archive.org"

_STATEMENT_KEYS = frozenset({"created_at", "entries", "head_hash", "head_seq", "kind", "protocolith_version", "v"})
_DOC_KEYS = frozenset({"anchor_id", "methods", "statement"})
_SHA256_ALGORITHM = bytes.fromhex("300d06096086480165030402010500")  # AlgorithmIdentifier: sha256, NULL parameters
_GEN_TIME = re.compile(r"([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})(?:\.[0-9]+)?Z")

Opener = Callable[..., Any]  # urllib.request.urlopen-like: opener(request, timeout=...) is a context manager
Runner = Callable[..., "subprocess.CompletedProcess[str]"]  # subprocess.run-like
StoreLike = Store | str | os.PathLike[str]


# --- statement ---------------------------------------------------------------------------------------------------


def build_statement(head_seq: int, head_hash: str, entries: int, created_at: str, version: str) -> dict[str, Any]:
    """The anchor statement: what is anchored (the head) and when."""
    return {
        "created_at": created_at,
        "entries": entries,
        "head_hash": head_hash,
        "head_seq": head_seq,
        "kind": STATEMENT_KIND,
        "protocolith_version": version,
        "v": 1,
    }


def anchor_name(head_seq: int, head_hash: str) -> str:
    return f"{head_seq}-{head_hash[:12]}"


def _uint(value: object) -> bool:
    return type(value) is int and value >= 0


def _method_problem(method: object) -> str | None:
    if not (isinstance(method, dict) and isinstance(method.get("type"), str)):
        return "a method is not an object with a type"
    if method["type"] == "rfc3161":
        name = method.get("file")
        if not (isinstance(name, str) and name and Path(name).name == name and "\\" not in name and is_hash(method.get("tsr_sha256"))):
            return "an rfc3161 method needs a plain file name and tsr_sha256"
    return None


def _problem(doc: object) -> str | None:
    """Why ``doc`` is not a well-formed anchor file, or None."""
    if not (isinstance(doc, dict) and set(doc) == _DOC_KEYS):
        return "not an anchor file (expected anchor_id, methods and statement)"
    statement = doc["statement"]
    if not (
        isinstance(statement, dict)
        and set(statement) == _STATEMENT_KEYS
        and statement["v"] == 1
        and statement["kind"] == STATEMENT_KIND
        and _uint(statement["head_seq"])
        and is_hash(statement["head_hash"])
        and _uint(statement["entries"])
        and isinstance(statement["protocolith_version"], str)
        and is_ts(statement["created_at"])
    ):
        return "the statement is malformed"
    if not (is_hash(doc["anchor_id"]) and isinstance(doc["methods"], list)):
        return "anchor_id or methods is malformed"
    for method in doc["methods"]:
        found = _method_problem(method)
        if found is not None:
            return found
    return None


def _read_doc(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """The parsed anchor file and None, or None and a reason."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"cannot be read ({type(exc).__name__})"
    try:
        doc = decode(raw)
    except CanonError as exc:
        return None, f"is not valid JSON ({exc.code})"
    problem = _problem(doc)
    return (None, problem) if problem is not None else (doc, None)


# --- verification ------------------------------------------------------------------------------------------------


@dataclass
class AnchorReport:
    """Result of checking every anchor file: ``last_seq`` is the highest head_seq of an anchor that checks out."""

    ok: bool
    count: int
    last_seq: int | None
    violations: list[Violation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchors": self.count,
            "last_anchored_seq": self.last_seq,
            "ok": self.ok,
            "violations": [v.to_dict() for v in self.violations],
        }


def _check_one(directory: Path, path: Path, entries: Mapping[int, Mapping[str, Any]], count: int) -> tuple[int | None, list[Violation]]:
    """Problems of one anchor file, and its head_seq when it is clean."""
    doc, why = _read_doc(path)
    if doc is None:
        return None, [Violation("ANCHOR_INVALID", 0, f"{path.name}: {why}")]
    statement = doc["statement"]
    seq, digest = statement["head_seq"], statement["head_hash"]
    found: list[Violation] = []
    if sha256_hex(statement) != doc["anchor_id"]:
        found.append(Violation("ANCHOR_INVALID", seq, f"{path.name}: the statement does not hash to anchor_id"))
    if statement["entries"] != seq + 1:
        found.append(Violation("ANCHOR_INVALID", seq, f"{path.name}: entries does not equal head_seq + 1"))
    for method in doc["methods"]:
        if method["type"] == "rfc3161":
            found += _check_tsr(directory, path, seq, method)
    if count <= seq:
        found.append(
            Violation("ANCHOR_AHEAD", seq, f"{path.name}: anchored entry {seq} but the ledger has {count} entries: truncated")
        )
    elif seq not in entries or entries[seq]["hash"] != digest:
        found.append(
            Violation("ANCHOR_MISMATCH", seq, f"{path.name}: entry {seq} is not the anchored one: the ledger was rewritten")
        )
    return (None if found else seq), found


def _check_tsr(directory: Path, anchor_path: Path, seq: int, method: dict[str, Any]) -> list[Violation]:
    target = directory / method["file"]
    try:
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
    except OSError as exc:
        return [Violation("ANCHOR_INVALID", seq, f"{anchor_path.name}: {method['file']} cannot be read ({type(exc).__name__})")]
    if digest != method["tsr_sha256"]:
        return [Violation("ANCHOR_INVALID", seq, f"{anchor_path.name}: {method['file']} does not match its recorded sha256")]
    return []


def check_anchors(directory: Path, verifier: Verifier, count: int) -> AnchorReport:
    """Check every ``*.json`` file in ``directory`` against a scanned ledger of ``count`` lines."""
    return _check_all(directory, verifier.entries, count)


def check_anchor_hashes(directory: Path, hashes: Mapping[int, str], count: int) -> AnchorReport:
    """Check every anchor against known entry hashes (a disclosure holds the hash of each entry, not its content)."""
    return _check_all(directory, {seq: {"hash": digest} for seq, digest in hashes.items()}, count)


def _check_all(directory: Path, entries: Mapping[int, Mapping[str, Any]], count: int) -> AnchorReport:
    violations: list[Violation] = []
    clean: list[int] = []
    paths = sorted(directory.glob("*.json"))
    for path in paths:
        seq, found = _check_one(directory, path, entries, count)
        violations += found
        if seq is not None:
            clean.append(seq)
    return AnchorReport(not violations, len(paths), max(clean, default=None), violations)


def _as_store(store: StoreLike) -> Store:
    return store if isinstance(store, Store) else Store(store)


def verify_anchors(store: StoreLike) -> AnchorReport:
    """Compare every anchor with the ledger: ANCHOR_MISMATCH (rewritten), ANCHOR_AHEAD (truncated), ANCHOR_INVALID."""
    real = _as_store(store)
    with io_guard(), real.locked(write=False):
        verdict, verifier = scan(real.read(missing_ok=False), card_hash)
        return check_anchors(real.anchors_dir, verifier, verdict.count)


# --- files -------------------------------------------------------------------------------------------------------


def _atomic_write(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` through a temporary file in the same directory, then rename."""
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temp, 0o644)
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def _write_once(path: Path, data: bytes) -> None:
    """Create ``path``; an existing file must hold exactly ``data`` (never overwritten with different content)."""
    if path.exists():
        if path.read_bytes() != data:
            raise InputError("ANCHOR_EXISTS", f"{path.name} exists with different content")
        return
    _atomic_write(path, data)


def _ensure_anchor(store: Store, seq: int, digest: str, entries: int, created_at: str, version: str) -> tuple[Path, dict[str, Any]]:
    """The local anchor file of this head: reused when present (statement and anchor_id never change), else created."""
    store.anchors_dir.mkdir(parents=True, exist_ok=True)
    name = anchor_name(seq, digest)
    path = store.anchors_dir / f"{name}.json"
    if path.exists():
        doc, _ = _read_doc(path)
        if doc is None or (doc["statement"]["head_seq"], doc["statement"]["head_hash"]) != (seq, digest):
            raise InputError("ANCHOR_EXISTS", f"{path.name} exists and is not an anchor of this head")
    else:
        statement = build_statement(seq, digest, entries, created_at, version)
        doc = {"anchor_id": sha256_hex(statement), "methods": [], "statement": statement}
        _atomic_write(path, encode(doc))
    _write_once(store.anchors_dir / f"{name}.statement", encode(doc["statement"]))
    return path, doc


def _merge_methods(path: Path, added: list[dict[str, Any]]) -> dict[str, Any]:
    """Append new methods to the anchor file (the statement is untouched) and return the document."""
    doc, why = _read_doc(path)
    if doc is None:
        raise InputError("ANCHOR_INVALID", f"{path.name}: {why}")
    fresh = [method for method in added if method not in doc["methods"]]
    if fresh:
        doc["methods"] = [*doc["methods"], *fresh]
        _atomic_write(path, encode(doc))
    return doc


def _store_tsr(directory: Path, anchor_id: str, data: bytes) -> str:
    """Save a time-stamp response next to the anchor; a different response never replaces an existing one."""
    name = f"{anchor_id}.tsr"
    target = directory / name
    if target.exists() and target.read_bytes() != data:
        name = f"{anchor_id}.{hashlib.sha256(data).hexdigest()[:12]}.tsr"
    _write_once(directory / name, data)
    return name


# --- network and processes ---------------------------------------------------------------------------------------


def _check_url(value: object, what: str) -> str:
    parsed = urllib.parse.urlparse(value) if isinstance(value, str) else None
    if parsed is None or parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InputError("BAD_URL", f"{what} must be an http or https URL")
    return str(value)


def _fetch(opener: Opener, request: urllib.request.Request, limit: int) -> tuple[bytes, Any]:
    """Send a request and return the body (read up to ``limit`` bytes, none when 0) and the response headers."""
    try:
        with opener(request, timeout=TIMEOUT) as response:
            body = response.read(limit + 1) if limit else b""
            headers = response.headers
    except (OSError, http.client.HTTPException) as exc:
        raise EnvError("ANCHOR_FAILED", f"request to {request.full_url} failed: {type(exc).__name__}") from exc
    if limit and len(body) > limit:
        raise EnvError("ANCHOR_FAILED", f"the response to {request.full_url} is larger than {limit} bytes")
    return body, headers


# --- RFC 3161 (DER by hand; the signature is not verified here) ---------------------------------------------------


def _tlv(tag: int, content: bytes) -> bytes:
    size = len(content)
    if size < 0x80:
        return bytes([tag, size]) + content
    length = size.to_bytes((size.bit_length() + 7) // 8, "big")
    return bytes([tag, 0x80 | len(length)]) + length + content


def _der_int(value: int) -> bytes:
    """DER INTEGER of a non-negative number (a leading zero byte keeps it positive)."""
    return _tlv(0x02, value.to_bytes(value.bit_length() // 8 + 1, "big"))


def build_timestamp_request(digest: bytes, nonce: int) -> bytes:
    """DER TimeStampReq (RFC 3161): version 1, a SHA-256 message imprint, a nonce and certReq true."""
    imprint = _tlv(0x30, _SHA256_ALGORITHM + _tlv(0x04, digest))
    return _tlv(0x30, _der_int(1) + imprint + _der_int(nonce) + _tlv(0x01, b"\xff"))


def _read_tlv(data: bytes, pos: int) -> tuple[int, bytes, int]:
    """One DER element at ``pos``: (tag, content, position after it). Raises ValueError when malformed."""
    if pos + 2 > len(data):
        raise ValueError("truncated element")
    tag, first = data[pos], data[pos + 1]
    pos += 2
    if first < 0x80:
        size = first
    else:
        width = first & 0x7F
        if not 1 <= width <= 4 or pos + width > len(data):
            raise ValueError("unsupported length")
        size = int.from_bytes(data[pos : pos + width], "big")
        pos += width
    if pos + size > len(data):
        raise ValueError("element runs past the end")
    return tag, data[pos : pos + size], pos + size


def _children(content: bytes) -> list[tuple[int, bytes]]:
    found: list[tuple[int, bytes]] = []
    pos = 0
    while pos < len(content):
        tag, body, pos = _read_tlv(content, pos)
        found.append((tag, body))
    return found


def _expect(item: tuple[int, bytes], tag: int) -> bytes:
    if item[0] != tag:
        raise ValueError(f"expected tag {tag:#x}, found {item[0]:#x}")
    return item[1]


def _gen_time(text: bytes) -> str:
    found = _GEN_TIME.fullmatch(text.decode("ascii", "replace"))
    if found is None:
        raise ValueError("genTime is not a GeneralizedTime")
    year, month, day, hour, minute, second = found.groups()
    return f"{year}-{month}-{day}T{hour}:{minute}:{second}Z"


def parse_timestamp_response(response: bytes, digest: bytes) -> str:
    """Check a TimeStampResp for status 0 or 1 and a message imprint equal to ``digest``; return genTime as ISO text.

    The signature of the time-stamp token is NOT verified: use ``openssl ts -verify``.
    """
    try:
        top = _children(_expect(_read_tlv(response, 0)[:2], 0x30))
        status_info = _children(_expect(top[0], 0x30))
        status = int.from_bytes(_expect(status_info[0], 0x02), "big")
        if status not in (0, 1):
            raise EnvError("ANCHOR_FAILED", f"the time-stamp authority refused the request (PKIStatus {status})")
        signed = _children(_expect(_children(_expect(top[1], 0x30))[1], 0xA0))
        signed_data = _children(_expect(signed[0], 0x30))
        content = _children(_expect(signed_data[2], 0x30))
        tst = _children(_expect(_children(_expect(content[1], 0xA0))[0], 0x04))
        info = _children(_expect(tst[0], 0x30))
        imprint = _children(_expect(info[2], 0x30))
        if _expect(imprint[1], 0x04) != digest:
            raise EnvError("ANCHOR_FAILED", "the time-stamp is for different data than the statement")
        return _gen_time(_expect(info[4], 0x18))
    except (ValueError, IndexError) as exc:
        raise EnvError("ANCHOR_FAILED", f"the time-stamp response is malformed: {exc}") from exc


def _rfc3161(
    directory: Path,
    anchor_id: str,
    statement: bytes,
    url: str,
    opener: Opener,
    random_bytes: Callable[[int], bytes],
    version: str,
) -> dict[str, Any]:
    digest = hashlib.sha256(statement).digest()
    body = build_timestamp_request(digest, int.from_bytes(random_bytes(8), "big"))
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/timestamp-reply",
            "Content-Type": "application/timestamp-query",
            "User-Agent": f"protocolith/{version}",
        },
    )
    reply, _ = _fetch(opener, request, MAX_RESPONSE)
    gen_time = parse_timestamp_response(reply, digest)
    name = _store_tsr(directory, anchor_id, reply)
    return {
        "file": name,
        "gen_time": gen_time,
        "tsr_sha256": hashlib.sha256(reply).hexdigest(),
        "type": "rfc3161",
        "url": url,
    }


def _wayback(url: str, opener: Opener, version: str) -> dict[str, Any]:
    request = urllib.request.Request(f"https://{WAYBACK_HOST}/save/{url}", headers={"User-Agent": f"protocolith/{version}"})
    _, headers = _fetch(opener, request, 0)
    location = headers.get("Content-Location") or headers.get("Location")
    if not location:
        raise EnvError("ANCHOR_FAILED", "the archive answered without a snapshot location")
    snapshot = urllib.parse.urljoin(f"https://{WAYBACK_HOST}/", location)
    if urllib.parse.urlparse(snapshot).netloc != WAYBACK_HOST:
        raise EnvError("ANCHOR_FAILED", "the snapshot location is not on the archive host")
    return {"snapshot": snapshot, "type": "wayback", "url": url}


def _git(runner: Runner, argv: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return runner(argv, capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise EnvError("ANCHOR_FAILED", f"git could not be run: {type(exc).__name__}") from exc


def _git_tag(runner: Runner, name: str, message: str, sign: bool) -> dict[str, Any]:
    if _git(runner, ["git", "rev-parse", "--is-inside-work-tree"]).returncode != 0:
        raise InputError("NOT_A_GIT_REPO", "the current directory is not inside a git repository")
    done = _git(runner, ["git", "tag", "-s" if sign else "-a", name, "-m", message])
    if done.returncode != 0:
        raise EnvError("ANCHOR_FAILED", f"git tag failed: {(done.stderr or '').strip()[:200]}")
    return {"signed": sign, "tag": name, "type": "git-tag"}


# --- the operation -----------------------------------------------------------------------------------------------


def anchor_head(
    store: StoreLike,
    *,
    tsa: str | None = None,
    wayback: str | None = None,
    git_tag: bool = False,
    sign: bool = False,
    write_head: str | os.PathLike[str] | None = None,
    clock: Clock | None = None,
    opener: Opener | None = None,
    runner: Runner | None = None,
    random_bytes: Callable[[int], bytes] | None = None,
) -> dict[str, Any]:
    """Anchor the ledger head: always a local anchor file; each option adds one method.

    ``tsa`` is the URL of an RFC 3161 service, ``wayback`` the URL where you published the statement, ``git_tag`` creates
    an (optionally signed) tag in the current repository without pushing it, ``write_head`` writes the statement to a file.
    The result lists ``anchor_id``, the files, all ``methods``, the ``added`` ones and ``notes`` (what is not verified here).
    """
    if sign and not git_tag:
        raise InputError("BAD_ENTRY", "sign needs git_tag")
    tsa_url = None if tsa is None else _check_url(tsa, "tsa")
    wayback_url = None if wayback is None else _check_url(wayback, "wayback")
    real = _as_store(store)
    version = _version()
    with io_guard(), real.locked(write=True):
        verdict, verifier = scan(real.read(missing_ok=False), card_hash)
        if not verdict.ok:
            raise VerificationFailed(verdict.violations)
        if verdict.count == 0:
            raise InputError("EMPTY_LEDGER", "the ledger has no entries to anchor")
        seq, digest = verdict.count - 1, verifier.tip_hash
        path, doc = _ensure_anchor(real, seq, digest, verdict.count, now_utc(clock), version)
    statement = encode(doc["statement"])
    anchor_id = doc["anchor_id"]
    name = anchor_name(seq, digest)
    added: list[dict[str, Any]] = []
    notes: list[str] = []
    try:
        if tsa_url is not None:
            with io_guard():
                found = _rfc3161(
                    real.anchors_dir,
                    anchor_id,
                    statement,
                    tsa_url,
                    opener or urllib.request.urlopen,
                    random_bytes or secrets.token_bytes,
                    version,
                )
            added.append(found)
            notes.append(
                "protocolith did not verify the time-stamp signature; verify it offline with: "
                f"openssl ts -verify -in {real.anchors_dir / found['file']} "
                f"-data {real.anchors_dir / (name + '.statement')} -CAfile CA.pem -untrusted TSA-CERT.pem"
            )
        if wayback_url is not None:
            added.append(_wayback(wayback_url, opener or urllib.request.urlopen, version))
            notes.append(
                f"the snapshot is only evidence if {wayback_url} served exactly the statement "
                f"(sha256 {anchor_id}); fetch the snapshot and compare"
            )
        if git_tag:
            tag = f"anchor/{name}"
            added.append(_git_tag(runner or subprocess.run, tag, statement.decode("utf-8"), sign))
            notes.append(f"the tag is local; publish it with: git push origin {tag}")
    finally:
        with io_guard(), real.locked(write=True):
            final = _merge_methods(path, added)
    if write_head is not None:
        with io_guard():
            _atomic_write(Path(write_head), statement)
    return {
        "added": added,
        "anchor_id": anchor_id,
        "head_file": None if write_head is None else str(write_head),
        "methods": final["methods"],
        "notes": notes,
        "path": str(path),
        "statement": final["statement"],
        "statement_path": str(real.anchors_dir / f"{name}.statement"),
    }
