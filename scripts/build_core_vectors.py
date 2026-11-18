#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate the language-neutral conformance vectors in spec/vectors/ deterministically.

Usage: python scripts/build_core_vectors.py [--check]

Every expectation below is written by hand; the generator refuses to write when the reference
implementation disagrees with it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from protocolith.core import MAX_ENTRY_BYTES, CanonError, decode, encode, scan
from protocolith.core.disclosure import disclose_verifier, parse_policy, verify_disclosure
from protocolith.core.issue import card_hash
from protocolith.core.ledger import ZERO_HASH, entry_hash, serialize
from protocolith.core.rules import Verifier, apply_expected_head

VECTOR_DIR = Path(__file__).resolve().parents[1] / "spec" / "vectors"
HASH_A = "a" * 64
HASH_B = "b" * 64
TS = [f"2026-11-15T10:00:0{i}Z" for i in range(10)]
PROTOCOL = {"gate": "pass rate at least 0.5", "protocol_id": "DEMO_D001", "version": "1"}
PROTOCOL_V2 = {"gate": "pass rate at least 0.6", "protocol_id": "DEMO_D001", "version": "2"}
OTHER = {"gate": "other", "protocol_id": "OTHER_D001", "version": "1"}
CARD = {
    "operator": "local operator",
    "official_source_name": "Demo source",
    "official_source_url": "https://example.org/data",
    "domain": "demo",
    "claim_type": "source_audit",
    "access_date": "2026-11-15",
    "source_rights_note": "Public page, no raw payload stored.",
    "raw_payload_manifest": "No raw payload committed.",
    "sanitized_report_path": "artifacts/demo_report.json",
    "sanitized_report_sha256": HASH_A,
    "git_commit": "abc1234",
    "runner_command": "manual",
    "verification_count": 1,
    "verification_level": "SINGLE_OPERATOR",
    "execution_mode": "MANUAL_NO_AI",
    "ai_assistance": "not used",
    "manual_review": "Reviewed by the operator.",
    "known_limitations": ["Single operator."],
    "public_claim_text": "The demo source publishes a statement about demo data.",
    "public_claim_verbatim_quote": "A verbatim quote of the demo statement.",
    "public_claim_source_url": "https://example.org/data",
    "public_claim_locator": "section 1, paragraph 2",
    "public_claim_captured_at": "2026-11-15",
    "public_claim_source_sha256": HASH_B,
}


def sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def freeze_body(protocol: dict[str, Any], supersedes: str | None = None) -> dict[str, Any]:
    return {
        "protocol_id": protocol["protocol_id"],
        "protocol": protocol,
        "protocol_sha256": sha(protocol),
        "supersedes": supersedes,
        "version": protocol["version"],
    }


def record_body(protocol: dict[str, Any] = PROTOCOL, **changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "protocol_sha256": sha(protocol),
        "run_id": "run-1",
        "status": "PASSED_UNDER_PROTOCOL",
        "outcome": {"pass_rate": "0.55"},
        "sources": [{"id": "source-1", "sha256": HASH_A}],
        "reproduction_level": "not independently reproduced",
        "claim_boundary": "Only the stated gate on the stated source and period.",
        "deviations": [],
        "card": {**CARD, "baseline_control_summary": "Baseline: previous value, pass rate 0.50."},
    }
    body.update(changes)
    return {key: value for key, value in body.items() if value is not None}


def deviation_body(protocol: dict[str, Any] = PROTOCOL) -> dict[str, Any]:
    return {"protocol_sha256": sha(protocol), "kind": "source_change", "description": "The source moved to a new URL."}


Spec = tuple[str, dict[str, Any], str, dict[str, Any]]


def spec(kind: str, body: dict[str, Any], ts: str, **over: Any) -> Spec:
    return (kind, body, ts, over)


def chain(specs: list[Spec], tail: str = "") -> str:
    """Build ledger text; per-entry overrides replace fields, then the hash is recomputed unless given."""
    out: list[str] = []
    prev = ZERO_HASH
    for index, (kind, body, ts, over) in enumerate(specs):
        entry: dict[str, Any] = {"body": body, "prev": prev, "seq": index, "ts": ts, "type": kind, "v": 1}
        entry.update({key: value for key, value in over.items() if key not in ("hash", "_spaced")})
        entry["hash"] = over.get("hash", entry_hash(entry))
        if over.get("_spaced"):
            out.append(json.dumps(entry, sort_keys=True) + "\n")
        else:
            out.append(serialize(entry).decode("utf-8"))
        prev = entry["hash"]
    return "".join(out) + tail


def with_line(extra: str) -> str:
    """A valid freeze, then ``extra`` as line 1, then a record that carries seq 2."""
    first, second = chain([BASE[0], spec("record", record_body(), TS[1], seq=2)]).splitlines(keepends=True)
    return first + extra + second


def before_valid(bad_line: str) -> str:
    """``bad_line`` followed by a valid freeze that carries seq 1."""
    return bad_line + chain([spec("freeze", freeze_body(PROTOCOL), TS[1], seq=1)])


def with_issue(specs: list[Spec], record_seq: int, ts: str, **over: Any) -> list[Spec]:
    """Append an issue entry whose card hash is computed by the reference implementation."""
    verifier = Verifier()
    for line in chain(specs).splitlines():
        verifier.feed(line.encode("utf-8"))
    body = {"card_sha256": card_hash(verifier, record_seq), "format": "evidence-card-json-svg", "record_seq": record_seq}
    body.update(over)
    return [*specs, spec("issue", body, ts)]


BASE = [spec("freeze", freeze_body(PROTOCOL), TS[0]), spec("record", record_body(), TS[1])]
FLOW = [
    spec("freeze", freeze_body(PROTOCOL), TS[0]),
    spec("deviation", deviation_body(), TS[1]),
    spec("record", record_body(deviations=[1]), TS[2]),
]


def ledger_case(name: str, rule: str, description: str, text: str, codes: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "rule": rule,
        "description": description,
        "ledger": text,
        "expect": {"ok": not codes, "codes": codes},
    }


def ledger_cases() -> list[dict[str, Any]]:
    flow = with_issue(FLOW, 2, TS[3])
    valid_tail = chain(BASE)
    huge = {"head": '{"body":{"outcome":{"note":"', "fill": "x", "count": MAX_ENTRY_BYTES, "tail": '"}}}' + "\n"}
    deep = '{"body":' + "[" * 70 + "]" * 70 + ',"seq":0}\n'
    unknown_issue = [*BASE, spec("issue", {"card_sha256": HASH_A, "format": "evidence-card-json-svg", "record_seq": 1}, TS[2])]
    v2 = [*BASE, spec("freeze", freeze_body(PROTOCOL_V2, sha(PROTOCOL)), TS[2]), spec("record", record_body(), TS[3])]
    blocked = record_body(status="BLOCKED_SOURCE", block_reason="The source returned HTTP 403.", card=None)
    cases = [
        ledger_case("valid_empty", "-", "An empty ledger is valid.", "", []),
        ledger_case("valid_freeze_only", "-", "One freeze.", chain(BASE[:1]), []),
        ledger_case("valid_full_flow", "-", "Freeze, deviation, record, issue.", chain(flow), []),
        ledger_case("valid_new_version", "-", "A new version supersedes the old; a record keeps its hash.", chain(v2), []),
        ledger_case("valid_equal_ts", "R4", "Equal timestamps are not a regression.", chain([BASE[0], spec("record", record_body(), TS[0])]), []),
        ledger_case("valid_blocked_without_sources", "R7", "BLOCKED_SOURCE with a reason and no sources.", chain([BASE[0], spec("record", {**blocked, "sources": []}, TS[1])]), []),
        ledger_case("r1_seq_gap", "R1", "seq jumps from 1 to 3.", chain([*BASE, spec("deviation", deviation_body(), TS[2], seq=3)]), ["BAD_SEQ"]),
        ledger_case("r1_seq_starts_at_one", "R1", "The first entry has seq 1.", chain([spec("freeze", freeze_body(PROTOCOL), TS[0], seq=1)]), ["BAD_SEQ"]),
        ledger_case("r2_bad_prev", "R2", "prev does not name the previous hash.", chain([*BASE, spec("deviation", deviation_body(), TS[2], prev=HASH_A)]), ["BAD_PREV"]),
        ledger_case("r2_first_prev_not_zero", "R2", "The first prev is not 64 zeros.", chain([spec("freeze", freeze_body(PROTOCOL), TS[0], prev=HASH_A)]), ["BAD_PREV"]),
        ledger_case("r3_bad_hash", "R3", "The stored hash is wrong.", chain([BASE[0], spec("record", record_body(), TS[1], hash=HASH_A)]), ["BAD_HASH"]),
        ledger_case("r3_protocol_hash_mismatch", "R3", "protocol_sha256 is not the hash of protocol.", chain([spec("freeze", {**freeze_body(PROTOCOL), "protocol_sha256": HASH_A}, TS[0])]), ["BAD_HASH"]),
        ledger_case("r3_not_canonical", "R3", "Correct hash but the line has insignificant whitespace.", chain([spec("freeze", freeze_body(PROTOCOL), TS[0], _spaced=True)]), ["NOT_CANONICAL"]),
        ledger_case("r4_ts_regression", "R4", "ts decreases.", chain([*BASE, spec("deviation", deviation_body(), TS[0])]), ["TS_REGRESSION"]),
        ledger_case("r5_record_unknown_protocol", "R5", "A record names a hash that was never frozen.", chain([BASE[0], spec("record", record_body(protocol_sha256=HASH_A), TS[1])]), ["UNKNOWN_PROTOCOL"]),
        ledger_case("r5_record_before_freeze", "R5", "The protocol is frozen only after the record.", chain([spec("record", record_body(), TS[0]), spec("freeze", freeze_body(PROTOCOL), TS[1])]), ["UNKNOWN_PROTOCOL"]),
        ledger_case("r5_deviation_unknown_protocol", "R5", "A deviation names an unfrozen protocol.", chain([BASE[0], spec("deviation", deviation_body(OTHER), TS[1])]), ["UNKNOWN_PROTOCOL"]),
        ledger_case("r5_supersedes_unknown", "R5", "supersedes names an unfrozen hash.", chain([BASE[0], spec("freeze", freeze_body(PROTOCOL_V2, HASH_A), TS[1])]), ["UNKNOWN_PROTOCOL"]),
        ledger_case("r6_duplicate_version", "R6", "The same protocol_id and version are frozen twice with other content.", chain([BASE[0], spec("freeze", freeze_body({**PROTOCOL, "gate": "changed"}), TS[1])]), ["DUPLICATE_FREEZE"]),
        ledger_case("r6_identical_refreeze", "R6", "The same protocol is frozen twice.", chain([BASE[0], spec("freeze", freeze_body(PROTOCOL), TS[1])]), ["DUPLICATE_FREEZE"]),
        ledger_case("r7_bad_status", "R7", "status is not in the closed set.", chain([BASE[0], spec("record", record_body(status="BEST_MODEL"), TS[1])]), ["BAD_STATUS"]),
        ledger_case("r7_blocked_without_reason", "R7", "BLOCKED_SOURCE without block_reason.", chain([BASE[0], spec("record", record_body(status="BLOCKED_SOURCE", card=None), TS[1])]), ["MISSING_FIELD"]),
        ledger_case("r7_drift_without_reason", "R7", "SOURCE_DRIFT without drift_reason.", chain([BASE[0], spec("record", record_body(status="SOURCE_DRIFT", card=None), TS[1])]), ["MISSING_FIELD"]),
        ledger_case("r7_missing_run_id", "R7", "A record without run_id.", chain([BASE[0], spec("record", record_body(run_id=None), TS[1])]), ["MISSING_FIELD"]),
        ledger_case("r7_negative_without_sources", "R7", "An executed result without any source hash.", chain([BASE[0], spec("record", record_body(status="NEGATIVE_RESULT_UNDER_PROTOCOL", sources=[]), TS[1])]), ["MISSING_FIELD"]),
        ledger_case("r8_deviation_ref_missing", "R8", "deviations names a seq that does not exist.", chain([BASE[0], spec("record", record_body(deviations=[7]), TS[1])]), ["DANGLING_REF"]),
        ledger_case("r8_deviation_ref_wrong_type", "R8", "deviations names a freeze.", chain([BASE[0], spec("record", record_body(deviations=[0]), TS[1])]), ["DANGLING_REF"]),
        ledger_case("r8_deviation_other_protocol", "R8", "deviations names a deviation of another protocol.", chain([BASE[0], spec("freeze", freeze_body(OTHER), TS[1]), spec("deviation", deviation_body(OTHER), TS[2]), spec("record", record_body(deviations=[2]), TS[3])]), ["DANGLING_REF"]),
        ledger_case("r8_issue_ref_not_record", "R8", "issue.record_seq names a freeze.", chain([*BASE, spec("issue", {"card_sha256": HASH_A, "format": "evidence-card-json-svg", "record_seq": 0}, TS[2])]), ["DANGLING_REF"]),
        ledger_case("r8_issue_ref_future", "R8", "issue.record_seq names a later seq.", chain([*BASE, spec("issue", {"card_sha256": HASH_A, "format": "evidence-card-json-svg", "record_seq": 5}, TS[2])]), ["DANGLING_REF"]),
        ledger_case("r9_bad_card_hash", "R9", "card_sha256 is not the hash of the rebuilt card.", chain(unknown_issue), ["BAD_CARD"]),
        ledger_case("r9_card_cannot_be_built", "R9", "The record carries no card metadata, so no card can be rebuilt.", chain([BASE[0], spec("record", record_body(card=None), TS[1]), spec("issue", {"card_sha256": HASH_A, "format": "evidence-card-json-svg", "record_seq": 1}, TS[2])]), ["BAD_CARD"]),
        ledger_case("r10_unknown_version", "R10", "v is 2.", chain([spec("freeze", freeze_body(PROTOCOL), TS[0], v=2)]), ["UNKNOWN_VERSION"]),
        ledger_case("r10_version_is_string", "R10", 'v is the string "1".', chain([spec("freeze", freeze_body(PROTOCOL), TS[0], v="1")]), ["UNKNOWN_VERSION"]),
        ledger_case("r11_partial_line", "R11", "The last line is cut and has no newline.", valid_tail + '{"body":{"kind":"sour', ["TRUNCATED_TAIL"]),
        ledger_case("r11_complete_without_newline", "R11", "A complete entry without the final newline.", chain(BASE + [spec("deviation", deviation_body(), TS[2])])[:-1], ["TRUNCATED_TAIL"]),
        ledger_case("r11_terminated_garbage", "R11", "The last line ends with a newline but does not parse.", valid_tail + '{"body"\n', ["TRUNCATED_TAIL"]),
        ledger_case("bad_entry_not_object", "-", "A middle line is not an object.", with_line("[1]\n"), ["BAD_ENTRY"]),
        ledger_case("bad_entry_extra_key", "-", "An entry has an unknown key.", chain([spec("freeze", freeze_body(PROTOCOL), TS[0], extra=1)]), ["BAD_ENTRY"]),
        ledger_case("bad_entry_bad_ts", "-", "ts is not whole-second UTC.", chain([spec("freeze", freeze_body(PROTOCOL), "2026-11-15 10:00:00")]), ["BAD_ENTRY"]),
        ledger_case("bad_entry_empty_line", "-", "An empty line in the middle.", with_line("\n"), ["BAD_ENTRY"]),
        ledger_case("bad_entry_float", "-", "A float anywhere in an entry.", before_valid('{"body":{"x":1.5},"hash":"' + HASH_A + '","prev":"' + ZERO_HASH + '","seq":0,"ts":"' + TS[0] + '","type":"freeze","v":1}\n'), ["BAD_ENTRY"]),
        ledger_case("bad_entry_duplicate_key", "-", "A duplicate key in an entry.", before_valid('{"seq":0,"seq":0}\n'), ["BAD_ENTRY"]),
        ledger_case("too_large_entry", "limit", f"A line longer than {MAX_ENTRY_BYTES} bytes.", "", ["ENTRY_TOO_LARGE"]),
        ledger_case("too_deep_entry", "limit", "Nesting deeper than 64.", deep, ["TOO_DEEP"]),
    ]
    for case in cases:
        if case["name"] == "too_large_entry":
            case.pop("ledger")
            case["ledger_template"] = huge
    return cases


def expand(case: dict[str, Any]) -> bytes:
    if "ledger_template" in case:
        t = case["ledger_template"]
        return (t["head"] + t["fill"] * t["count"] + t["tail"]).encode("utf-8")
    return str(case["ledger"]).encode("utf-8")


def canonical_cases() -> list[dict[str, Any]]:
    deep64 = "[" * 64 + "]" * 64
    deep65 = "[" * 65 + "]" * 65
    ok: list[tuple[str, str, str]] = [
        ("empty_object", "{}", "{}"),
        ("empty_array", "[ ]", "[]"),
        ("scalars", '[null, true, false, 0, -0, 7]', "[null,true,false,0,0,7]"),
        ("whitespace_removed", ' {\n "b" : 1 ,\t"a" : [ 2 , 3 ] }\n', '{"a":[2,3],"b":1}'),
        ("keys_sorted_by_code_point", '{"b":1,"a":2,"B":3,"":4,"\\u00e9":5}', '{"":4,"B":3,"a":2,"b":1,"é":5}'),
        ("keys_code_point_not_utf16", '{"\\ud800\\udc00":1,"\\uffff":2}', '{"￿":2,"\U00010000":1}'),
        ("nested_key_order", '{"z":{"b":1,"a":2},"a":[{"d":1,"c":2}]}', '{"a":[{"c":2,"d":1}],"z":{"a":2,"b":1}}'),
        ("escapes", '"\\"\\\\\\/\\b\\f\\n\\r\\t"', '"\\"\\\\/\\b\\f\\n\\r\\t"'),
        ("control_characters", '"\\u0000\\u001f\\u0007"', '"\\u0000\\u001f\\u0007"'),
        ("del_is_literal", '"\\u007f"', '"\x7f"'),
        ("unicode_literal", '"\\u00e9\\u20ac\\u2028"', '"é€ "'),
        ("surrogate_pair_is_literal", '"\\ud83d\\ude00"', '"\U0001f600"'),
        ("literal_non_bmp_input", '"\U0001f600"', '"\U0001f600"'),
        ("max_safe_integer", "9007199254740991", "9007199254740991"),
        ("min_safe_integer", "-9007199254740991", "-9007199254740991"),
        ("depth_64", deep64, deep64),
        ("top_level_string", '"a"', '"a"'),
    ]
    bad: list[tuple[str, str | None, str | None, str]] = [
        ("integer_2_pow_53", "9007199254740992", None, "INT_RANGE"),
        ("integer_minus_2_pow_53", "-9007199254740992", None, "INT_RANGE"),
        ("integer_huge", "1" + "0" * 40, None, "INT_RANGE"),
        ("float_fraction", "1.5", None, "FLOAT_NOT_ALLOWED"),
        ("float_integral", "1.0", None, "FLOAT_NOT_ALLOWED"),
        ("float_exponent", "1e2", None, "FLOAT_NOT_ALLOWED"),
        ("float_nested", '{"a":[0.1]}', None, "FLOAT_NOT_ALLOWED"),
        ("nan", "NaN", None, "NON_FINITE"),
        ("infinity", "[Infinity]", None, "NON_FINITE"),
        ("minus_infinity", "-Infinity", None, "NON_FINITE"),
        ("duplicate_key", '{"a":1,"a":2}', None, "DUPLICATE_KEY"),
        ("duplicate_key_nested", '{"x":{"a":1,"b":2,"a":3}}', None, "DUPLICATE_KEY"),
        ("duplicate_key_after_escape", '{"a":1,"\\u0061":2}', None, "DUPLICATE_KEY"),
        ("lone_high_surrogate", '"\\ud800"', None, "LONE_SURROGATE"),
        ("lone_low_surrogate", '"\\udc00"', None, "LONE_SURROGATE"),
        ("lone_surrogate_in_key", '{"\\ud800":1}', None, "LONE_SURROGATE"),
        ("depth_65", deep65, None, "TOO_DEEP"),
        ("depth_3000", "[" * 3000 + "]" * 3000, None, "TOO_DEEP"),
        ("empty_input", "", None, "BAD_JSON"),
        ("trailing_garbage", "{} x", None, "BAD_JSON"),
        ("single_quotes", "{'a':1}", None, "BAD_JSON"),
        ("trailing_comma", "[1,]", None, "BAD_JSON"),
        ("leading_zero", "01", None, "BAD_JSON"),
        ("raw_newline_in_string", '"a\nb"', None, "BAD_JSON"),
        ("byte_order_mark", None, "efbbbf7b7d", "BAD_JSON"),
        ("invalid_utf8", None, "22ff22", "BAD_UTF8"),
    ]
    cases: list[dict[str, Any]] = []
    for name, text, canonical in ok:
        cases.append({"name": name, "input_text": text, "expect": {"ok": True, "canonical": canonical}})
    for name, text, hex_input, code in bad:
        case: dict[str, Any] = {"name": name, "expect": {"ok": False, "code": code}}
        case.update({"input_text": text} if text is not None else {"input_hex": hex_input})
        cases.append(case)
    return cases


def hash_cases() -> list[dict[str, Any]]:
    values = ["{}", "[]", "null", '"abc"', '{"b":[1,"é"],"a":null}', "0", '{"a":{"b":{"c":[true,false]}}}']
    return [
        {
            "name": f"hash_{index}",
            "input_text": text,
            "canonical": encode(decode(text)).decode("utf-8"),
            "sha256": hashlib.sha256(encode(decode(text))).hexdigest(),
        }
        for index, text in enumerate(values)
    ]


def head_hashes(text: str) -> list[str]:
    return [json.loads(line)["hash"] for line in text.splitlines()]


def head_cases() -> list[dict[str, Any]]:
    """Cases for ``verify-ledger --expect-head SEQ:HASH``: verify first, then require that entry."""
    three = chain(FLOW)
    h3 = head_hashes(three)
    two = "".join(three.splitlines(keepends=True)[:2])
    broken = chain([*BASE, spec("deviation", deviation_body(), TS[2], seq=3)])

    def case(name: str, description: str, ledger: str, expect_head: str, codes: list[str]) -> dict[str, Any]:
        return {
            "name": name,
            "description": description,
            "ledger": ledger,
            "expect_head": expect_head,
            "expect": {"ok": not codes, "codes": codes},
        }

    return [
        case("head_matches_last", "The expected head is the last entry.", three, f"2:{h3[2]}", []),
        case("head_matches_earlier_entry", "An earlier entry also satisfies the check.", three, f"0:{h3[0]}", []),
        case("head_wrong_hash", "The entry exists but its hash differs.", three, f"2:{HASH_A}", ["HEAD_MISMATCH"]),
        case("head_hash_of_another_seq", "The hash belongs to a different seq.", three, f"1:{h3[2]}", ["HEAD_MISMATCH"]),
        case("head_tail_removed", "The tail was removed: the ledger verifies but has no entry 2.", two, f"2:{h3[2]}", ["HEAD_MISMATCH"]),
        case("head_empty_ledger", "An empty ledger has no entry 0.", "", f"0:{HASH_A}", ["HEAD_MISMATCH"]),
        case("head_ignored_when_ledger_fails", "A ledger that fails verification reports its own codes only.", broken, f"1:{HASH_A}", ["BAD_SEQ"]),
    ]


def anchor_cases() -> list[dict[str, Any]]:
    """Anchor statements: the canonical bytes and their sha256 (the anchor_id), computed independently of the library."""
    statements = [
        ("first_entry", 0, HASH_A, 1, TS[0], "0.6.0"),
        ("third_entry", 2, HASH_B, 3, TS[2], "0.7.0"),
        ("large_seq", 9999, "0123456789abcdef" * 4, 10000, "2026-11-18T10:15:00Z", "unknown"),
    ]
    cases = []
    for name, seq, digest, entries, created, version in statements:
        statement = {
            "created_at": created,
            "entries": entries,
            "head_hash": digest,
            "head_seq": seq,
            "kind": "protocolith-anchor",
            "protocolith_version": version,
            "v": 1,
        }
        text = json.dumps(statement, sort_keys=True, separators=(",", ":"))
        cases.append(
            {
                "name": name,
                "statement": statement,
                "canonical": text,
                "anchor_id": hashlib.sha256(text.encode()).hexdigest(),
                "file_name": f"{seq}-{digest[:12]}.json",
            }
        )
    return cases


DISCLOSURE_POLICIES = {
    "all_full": {"default": "full"},
    "all_summary": {"default": "summary"},
    "all_hidden": {},
    "mixed": {"default": "hidden", "rules": [{"seq": 0, "level": "full"}, {"seq": [1, 2], "level": "summary"}]},
}


def disclosure_cases(ledgers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Disclosures of the valid_full_flow ledger under four policies, plus two edited disclosures that must fail."""
    base = next(case for case in ledgers if case["name"] == "valid_full_flow")
    _, verifier = scan(str(base["ledger"]).encode("utf-8"), card_hash)
    cases: list[dict[str, Any]] = []
    for name, doc in DISCLOSURE_POLICIES.items():
        built = disclose_verifier(verifier, parse_policy(doc))
        cases.append(
            {
                "name": name,
                "ledger": base["ledger"],
                "policy": doc,
                "disclosure": built.data.decode("utf-8"),
                "expect": {"ok": True, "codes": [], "counts": built.counts},
            }
        )
    full = cases[0]["disclosure"].split("\n")
    chain = cases[1]["disclosure"].split("\n")
    edited = json.loads(full[2])
    edited["entry"]["body"]["run_id"] = "edited"
    full[2] = encode(edited).decode("utf-8")
    dropped = chain[:2] + chain[3:]
    cases.append({"name": "edited_full_entry", "disclosure": "\n".join(full), "expect": {"ok": False, "codes": ["DISCLOSURE_HASH"]}})
    cases.append({"name": "dropped_entry", "disclosure": "\n".join(dropped), "expect": {"ok": False, "codes": ["BAD_DISCLOSURE"]}})
    return cases


def check(
    canonical: list[dict[str, Any]],
    hashes: list[dict[str, Any]],
    ledgers: list[dict[str, Any]],
    heads: list[dict[str, Any]],
    anchors: list[dict[str, Any]],
    disclosures: list[dict[str, Any]],
) -> None:
    """Refuse to write vectors the reference implementation does not reproduce."""
    for case in canonical:
        raw = bytes.fromhex(case["input_hex"]) if "input_hex" in case else case["input_text"].encode("utf-8")
        try:
            got: dict[str, Any] = {"ok": True, "canonical": encode(decode(raw)).decode("utf-8")}
        except CanonError as exc:
            got = {"ok": False, "code": exc.code}
        assert got == case["expect"], (case["name"], got)
    for case in hashes:
        manual = hashlib.sha256(case["canonical"].encode("utf-8")).hexdigest()
        assert manual == case["sha256"], case["name"]
    for case in ledgers:
        verdict, _ = scan(expand(case), card_hash)
        assert verdict.codes == case["expect"]["codes"], (case["name"], verdict.codes, verdict.violations)
        assert verdict.ok == case["expect"]["ok"], case["name"]
    for case in heads:
        verdict, verifier = scan(str(case["ledger"]).encode("utf-8"), card_hash)
        seq, digest = str(case["expect_head"]).split(":")
        verdict = apply_expected_head(verdict, verifier, int(seq), digest)
        assert verdict.codes == case["expect"]["codes"] and verdict.ok == case["expect"]["ok"], case["name"]
    for case in anchors:
        text = encode(case["statement"]).decode("utf-8")
        assert text == case["canonical"], case["name"]
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == case["anchor_id"], case["name"]
    for case in disclosures:
        report = verify_disclosure(str(case["disclosure"]).encode("utf-8"))
        assert report.ok == case["expect"]["ok"] and report.codes == case["expect"]["codes"], (case["name"], report.codes)


def dump(name: str, description: str, cases: list[dict[str, Any]]) -> str:
    document = {"format": "protocolith-vectors/1", "kind": name, "description": description, "cases": cases}
    return json.dumps(document, indent=1, ensure_ascii=True) + "\n"


def build_vectors() -> dict[str, str]:
    canonical, hashes, ledgers, heads = canonical_cases(), hash_cases(), ledger_cases(), head_cases()
    anchors = anchor_cases()
    disclosures = disclosure_cases(ledgers)
    check(canonical, hashes, ledgers, heads, anchors, disclosures)
    return {
        "canonical.json": dump(
            "canonical",
            "PCJ-1: parse input (text or hex bytes) strictly and compare the canonical text or the error code.",
            canonical,
        ),
        "hashes.json": dump("hashes", "sha256 of the PCJ-1 bytes of the parsed input.", hashes),
        "ledgers.json": dump(
            "ledgers",
            "Verify the ledger text (or the expanded ledger_template: head + fill*count + tail); "
            "expect ok and the sorted unique rule codes.",
            ledgers,
        ),
        "heads.json": dump(
            "heads",
            "Verify the ledger text, then require the entry named by expect_head (SEQ:HASH) to exist with that hash; "
            "expect ok and the sorted unique codes. A ledger that already fails reports only its own codes.",
            heads,
        ),
        "anchors.json": dump(
            "anchors",
            "An anchor statement (an object): its PCJ-1 text is canonical and the lowercase hex sha256 of those UTF-8 bytes "
            "is the anchor_id; the local anchor file is named file_name.",
            anchors,
        ),
        "disclosures.json": dump(
            "disclosures",
            "A disclosure file (JSON Lines text): verify its structure, hash chain and full entries; expect ok and the sorted "
            "unique codes. Cases that carry a ledger and a policy are what that policy must produce from that ledger, byte for byte.",
            disclosures,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with the committed files instead of writing.")
    args = parser.parse_args(argv)
    built = build_vectors()
    stale = [name for name, text in built.items() if not (VECTOR_DIR / name).is_file() or (VECTOR_DIR / name).read_text(encoding="utf-8") != text]
    if args.check:
        print("vectors up to date" if not stale else "stale vectors: " + ", ".join(stale))
        return 1 if stale else 0
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in built.items():
        (VECTOR_DIR / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(built)} files to {VECTOR_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
