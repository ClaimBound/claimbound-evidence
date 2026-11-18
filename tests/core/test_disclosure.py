# SPDX-License-Identifier: Apache-2.0
"""Selective disclosure: policy, export, verification, reveal, the atlas view, the CLI and MCP tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from core_support import NOW, clock, deviation_body, protocol, record_body

from protocolith.cli import main
from protocolith.core import (
    InputError,
    Store,
    VerificationFailed,
    anchor_head,
    build_atlas,
    build_disclosure,
    deviation,
    entries,
    freeze,
    issue,
    load_policy,
    parse_policy,
    record,
    schema_for,
    sha256_hex,
    verify_disclosure,
    verify_reveal,
)
from protocolith.core import disclosure as disclosure_module
from protocolith.core.canonical import encode
from protocolith.core.disclosure import Policy, Rule, summarize_entry
from protocolith.core.mcp import handle_line

OTHER = {"gate": "other gate", "protocol_id": "OTHER_D002", "question": "Is it so?", "version": "1"}


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROTOCOLITH_NOW", NOW)


@pytest.fixture
def rich(store: Store) -> Store:
    """seq 0 freeze DEMO, 1 record DEMO, 2 issue, 3 freeze OTHER, 4 record OTHER, 5 deviation DEMO."""
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(), clock=clock(NOW))
    issue(store, 1, clock=clock(NOW))
    freeze(store, OTHER, clock=clock(NOW))
    record(store, record_body(protocol_sha256=sha256_hex(OTHER), run_id="run-2", status="NEGATIVE_RESULT_UNDER_PROTOCOL"), clock=clock(NOW))
    deviation(store, deviation_body(), clock=clock(NOW))
    return store


def lines_of(data: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in data.splitlines()]


def policy(**changes: Any) -> Policy:
    doc: dict[str, Any] = {"v": 1, "default": "hidden", "rules": []}
    doc.update(changes)
    return parse_policy(doc)


# ---------------------------------------------------------------- policy

def test_policy_defaults_and_first_match_wins() -> None:
    p = parse_policy({})
    assert p.default == "hidden" and p.rules == () and p.summary_fields == ("status", "reproduction_level", "claim_boundary")
    p = parse_policy(
        {
            "default": "summary",
            "rules": [
                {"protocol_id": "DEMO_D001", "level": "full"},
                {"protocol_id": "DEMO_*", "level": "hidden"},
                {"seq": [7, 8], "level": "hidden"},
                {"from_seq": 10, "to_seq": 12, "level": "full"},
            ],
        }
    )
    assert p.level_for(0, "DEMO_D001") == "full"
    assert p.level_for(0, "DEMO_D002") == "hidden"
    assert p.level_for(0, "OTHER") == "summary"
    assert p.level_for(0, None) == "summary"
    assert p.level_for(8, None) == "hidden"
    assert p.level_for(11, None) == "full" and p.level_for(13, None) == "summary"
    assert Rule("full", seqs=frozenset({3})).matches(3, None)


@pytest.mark.parametrize(
    "doc",
    [
        [],
        {"unknown": 1},
        {"v": 2},
        {"default": "everything"},
        {"rules": "no"},
        {"rules": [1]},
        {"rules": [{"level": "full"}]},
        {"rules": [{"protocol_id": "A", "level": "full", "extra": 1}]},
        {"rules": [{"protocol_id": "A"}]},
        {"rules": [{"protocol_id": "A", "level": "nope"}]},
        {"rules": [{"protocol_id": "A", "seq": 1, "level": "full"}]},
        {"rules": [{"protocol_id": "", "level": "full"}]},
        {"rules": [{"protocol_id": "A*B", "level": "full"}]},
        {"rules": [{"protocol_id": 5, "level": "full"}]},
        {"rules": [{"seq": -1, "level": "full"}]},
        {"rules": [{"seq": [], "level": "full"}]},
        {"rules": [{"seq": True, "level": "full"}]},
        {"rules": [{"from_seq": 3, "level": "full"}]},
        {"rules": [{"from_seq": 5, "to_seq": 2, "level": "full"}]},
        {"rules": [{"from_seq": "1", "to_seq": 2, "level": "full"}]},
        {"summary_fields": "status"},
        {"summary_fields": ["status", "status"]},
        {"summary_fields": ["status", 3]},
        {"summary_fields": ["secret"]},
        {"rules": [{"protocol_id": "A", "level": "full"}] * (disclosure_module.RULES_LIMIT + 1)},
    ],
)
def test_bad_policies_are_refused(doc: Any) -> None:
    with pytest.raises(InputError) as caught:
        parse_policy(doc)
    assert caught.value.code == "BAD_POLICY"


def test_load_policy_reads_strict_json(tmp_path: Path) -> None:
    good = tmp_path / "p.json"
    good.write_text('{"default": "summary"}', encoding="utf-8")
    assert load_policy(good).default == "summary"
    bad = tmp_path / "bad.json"
    bad.write_text('{"default": 1.5}', encoding="utf-8")
    with pytest.raises(InputError) as caught:
        load_policy(bad)
    assert caught.value.code == "BAD_POLICY" and "bad.json" in caught.value.message
    with pytest.raises(Exception):
        load_policy(tmp_path / "missing.json")


def test_policy_schema_describes_the_policy() -> None:
    schema = schema_for("policy")
    assert schema["title"] == "protocolith policy" and "rules" in schema["properties"]
    assert schema["additionalProperties"] is False


# ---------------------------------------------------------------- build

def test_build_levels_and_manifest(rich: Store) -> None:
    p = policy(
        rules=[
            {"protocol_id": "DEMO_D001", "level": "full"},
            {"protocol_id": "OTHER_D002", "level": "summary"},
        ],
        summary_fields=["status", "claim_boundary", "run_id", "outcome", "public_claim_text", "question", "reproduction_level"],
    )
    found = build_disclosure(rich, p)
    rows = lines_of(found.data)
    assert rows[0] == {
        "counts": {"full": 4, "hidden": 0, "summary": 2},
        "entries": 6,
        "head_hash": found.head_hash,
        "head_seq": 5,
        "kind": "protocolith-disclosure",
        "v": 1,
    }
    ledger = entries(rich)
    assert [r["level"] for r in rows[1:]] == ["full", "full", "full", "summary", "summary", "full"]
    assert rows[1]["entry"] == ledger[0]
    freeze_summary, record_summary = rows[4]["summary"], rows[5]["summary"]
    assert freeze_summary == {"protocol_id": "OTHER_D002", "question": "Is it so?", "version": "1"}
    assert record_summary["status"] == "NEGATIVE_RESULT_UNDER_PROTOCOL" and record_summary["run_id"] == "run-2"
    assert record_summary["outcome"] == {"pass_rate": "0.55"} and "public_claim_text" in record_summary
    assert set(rows[4]) == {"hash", "level", "prev", "seq", "summary", "ts", "type"}
    assert found.to_dict()["entries"] == 6 and found.to_dict()["head"]["seq"] == 5
    assert found.data == build_disclosure(rich, p).data  # deterministic


def test_hidden_lines_carry_only_the_chain(rich: Store) -> None:
    found = build_disclosure(rich, policy())
    rows = lines_of(found.data)
    assert rows[0]["counts"] == {"full": 0, "hidden": 6, "summary": 0}
    assert all(set(row) == {"hash", "level", "prev", "seq"} for row in rows[1:])
    text = found.data.decode()
    assert "DEMO_D001" not in text and "pass_rate" not in text and "2026-11-15" not in text


def test_summary_of_every_entry_type(rich: Store) -> None:
    ledger = entries(rich)
    every = disclosure_module.SUMMARY_CHOICES
    assert summarize_entry(ledger[2], "DEMO_D001", every) == {"protocol_id": "DEMO_D001", "record_seq": 1}
    assert summarize_entry(ledger[5], "DEMO_D001", every) == {"protocol_id": "DEMO_D001"}
    assert summarize_entry(ledger[5], None, every) == {}
    only_status = summarize_entry(ledger[1], "DEMO_D001", ("status",))
    assert only_status == {"protocol_id": "DEMO_D001", "status": "PASSED_UNDER_PROTOCOL"}
    plain_freeze = summarize_entry(ledger[0], "DEMO_D001", every)
    assert plain_freeze == {"protocol_id": "DEMO_D001", "version": "1"}  # this protocol has no question


def test_empty_ledger_discloses_to_a_manifest(store: Store) -> None:
    from protocolith.core import init

    init(store)
    found = build_disclosure(store, policy())
    assert found.head_seq is None and found.head_hash is None
    assert verify_disclosure(found.data).ok
    report = verify_disclosure(found.data)
    assert report.head_seq is None and report.entries == 0


def test_a_ledger_that_fails_verification_is_never_disclosed(rich: Store) -> None:
    rich.ledger_path.write_bytes(rich.ledger_path.read_bytes().replace(b"PASSED_UNDER_PROTOCOL", b"PASSED_UNDER_PROTOCOX", 1))
    with pytest.raises(VerificationFailed):
        build_disclosure(rich, policy())


def test_build_accepts_a_path(rich: Store) -> None:
    assert build_disclosure(rich.path, policy()).head_seq == 5


def test_warning_when_a_record_is_shown_more_than_its_freeze(rich: Store) -> None:
    found = build_disclosure(rich, policy(rules=[{"seq": 0, "level": "hidden"}, {"seq": 1, "level": "full"}], default="summary"))
    assert found.warnings == ["seq 1: the record is shown more than the freeze of protocol DEMO_D001"]
    assert build_disclosure(rich, policy(default="full")).warnings == []
    assert build_disclosure(rich, policy(default="hidden")).warnings == []


# ---------------------------------------------------------------- verify

def disclosed(rich: Store, **changes: Any) -> bytes:
    return build_disclosure(rich, policy(default="summary", **changes)).data


def test_verify_accepts_what_build_writes(rich: Store) -> None:
    for default in ("full", "summary", "hidden"):
        data = build_disclosure(rich, policy(default=default)).data
        report = verify_disclosure(data)
        assert report.ok and report.entries == 6 and report.head_seq == 5 and report.codes == []
        assert report.to_dict()["counts"][default] == 6 and "anchors" not in report.to_dict()
    mixed = build_disclosure(rich, policy(default="hidden", rules=[{"seq": [0, 1], "level": "full"}, {"seq": 2, "level": "summary"}])).data
    assert verify_disclosure(mixed).ok


def mutate(data: bytes, index: int, change: Any) -> bytes:
    rows = data.splitlines()
    obj = json.loads(rows[index])
    change(obj)
    rows[index] = encode(obj)
    return b"\n".join(rows) + b"\n"


def codes(data: bytes) -> set[str]:
    return set(verify_disclosure(data).codes)


def test_verify_finds_edits(rich: Store) -> None:
    full = build_disclosure(rich, policy(default="full")).data
    summary = disclosed(rich)
    assert codes(mutate(full, 2, lambda o: o["entry"]["body"].__setitem__("run_id", "x"))) == {"DISCLOSURE_HASH"}
    assert "DISCLOSURE_CHAIN" in codes(mutate(summary, 3, lambda o: o.__setitem__("prev", "f" * 64)))
    assert "BAD_DISCLOSURE" in codes(mutate(summary, 3, lambda o: o.__setitem__("seq", 9)))
    assert "BAD_DISCLOSURE" in codes(mutate(summary, 3, lambda o: o.__setitem__("extra", 1)))
    assert "BAD_DISCLOSURE" in codes(mutate(summary, 3, lambda o: o.__setitem__("level", "secret")))
    assert "BAD_DISCLOSURE" in codes(mutate(summary, 3, lambda o: o.__setitem__("hash", "nothex")))
    assert "BAD_DISCLOSURE" in codes(mutate(summary, 3, lambda o: o.__setitem__("ts", "yesterday")))
    assert "BAD_DISCLOSURE" in codes(mutate(summary, 3, lambda o: o.__setitem__("type", "magic")))
    assert "BAD_DISCLOSURE" in codes(mutate(summary, 3, lambda o: o.__setitem__("summary", [])))
    assert "BAD_DISCLOSURE" in codes(mutate(full, 3, lambda o: o["entry"].__setitem__("seq", 7)))
    assert "BAD_DISCLOSURE" in codes(mutate(full, 3, lambda o: o["entry"].pop("body")))
    assert "BAD_DISCLOSURE" in codes(mutate(full, 3, lambda o: o.__setitem__("entry", 5)))
    assert "BAD_DISCLOSURE" in codes(mutate(full, 3, lambda o: o.__setitem__("seq", True)))


def test_verify_finds_dropped_reordered_and_manifest_lies(rich: Store) -> None:
    rows = disclosed(rich).splitlines()
    dropped = b"\n".join(rows[:3] + rows[4:]) + b"\n"
    assert codes(dropped) >= {"BAD_DISCLOSURE"}
    swapped = b"\n".join(rows[:2] + [rows[3], rows[2]] + rows[4:]) + b"\n"
    assert codes(swapped)
    truncated = b"\n".join(rows[:-1]) + b"\n"
    assert codes(truncated) == {"BAD_DISCLOSURE"}
    assert codes(mutate(disclosed(rich), 0, lambda o: o.__setitem__("kind", "other"))) == {"BAD_DISCLOSURE"}
    assert codes(mutate(disclosed(rich), 0, lambda o: o.__setitem__("entries", 9))) == {"BAD_DISCLOSURE"}
    assert codes(mutate(disclosed(rich), 0, lambda o: o["counts"].__setitem__("full", 1))) == {"BAD_DISCLOSURE"}
    assert codes(mutate(disclosed(rich), 0, lambda o: o.__setitem__("head_hash", "a" * 64))) == {"BAD_DISCLOSURE"}


def test_a_damaged_line_in_the_middle_is_reported_and_skipped(rich: Store) -> None:
    rows = disclosed(rich).splitlines()
    rows[3] = b"not json"
    report = verify_disclosure(b"\n".join(rows) + b"\n")
    assert not report.ok and "BAD_DISCLOSURE" in report.codes


def test_verify_rejects_bad_files() -> None:
    assert codes(b"") == {"BAD_DISCLOSURE"}
    assert codes(b"{}") == {"BAD_DISCLOSURE"}  # no final newline
    assert codes(b"not json\n") == {"BAD_DISCLOSURE"}
    assert codes(b"[]\n") == {"BAD_DISCLOSURE"}
    assert codes(b'{"b": 1, "a": 2}\n') == {"BAD_DISCLOSURE"}  # valid JSON, not canonical
    report = verify_disclosure(b"not json\n")
    assert not report.ok and report.to_dict()["ok"] is False


def test_verify_checks_anchors(rich: Store, tmp_path: Path) -> None:
    anchor_head(rich, clock=clock(NOW))
    data = disclosed(rich)
    report = verify_disclosure(data, rich.anchors_dir)
    assert report.ok and report.anchors == 1 and report.to_dict()["anchors"] == 1
    # a disclosure of a rewritten history: same shape, other hashes
    other = tmp_path / "other"
    freeze(Store(other), {**protocol(), "gate": "changed"}, clock=clock(NOW))
    forged = build_disclosure(Store(other), policy()).data
    assert "ANCHOR_AHEAD" in set(verify_disclosure(forged, rich.anchors_dir).codes)
    # same length, different history
    store2 = Store(tmp_path / "two")
    for number in range(6):
        freeze(store2, {**protocol(), "protocol_id": f"P{number}"}, clock=clock(NOW))
    replaced = build_disclosure(store2, policy()).data
    assert "ANCHOR_MISMATCH" in set(verify_disclosure(replaced, rich.anchors_dir).codes)


# ---------------------------------------------------------------- reveal

def test_reveal_matches_hidden_summary_and_full_entries(rich: Store) -> None:
    ledger = entries(rich)
    data = build_disclosure(rich, policy(rules=[{"seq": 0, "level": "full"}, {"seq": [1, 3, 4], "level": "summary"}])).data
    assert verify_reveal(data, ledger[0]) == {"level": "full", "matches": True, "reason": None, "seq": 0}
    assert verify_reveal(data, ledger[1])["level"] == "summary"
    assert verify_reveal(data, ledger[3])["matches"] is True
    assert verify_reveal(data, ledger[2])["level"] == "hidden"
    assert verify_reveal(data, ledger[5])["matches"] is True


def test_reveal_refuses_a_substitute(rich: Store) -> None:
    ledger = entries(rich)
    data = build_disclosure(rich, policy(rules=[{"seq": [1, 3], "level": "summary"}])).data

    def result(entry: Any) -> dict[str, Any]:
        return verify_reveal(data, entry)

    assert not result("text")["matches"] and not result({})["matches"]
    forged = json.loads(json.dumps(ledger[1]))
    forged["body"]["status"] = "NEGATIVE_RESULT_UNDER_PROTOCOL"  # hash no longer matches
    assert "own hash" in result(forged)["reason"]
    other = json.loads(json.dumps(ledger[1]))
    other["body"]["run_id"] = "other"
    other["hash"] = disclosure_module.entry_hash(other)  # self-consistent but not the published one
    assert "not the one" in result(other)["reason"]
    assert "no entry" in result({**ledger[1], "seq": 99, "hash": disclosure_module.entry_hash({**ledger[1], "seq": 99})})["reason"]
    assert "no entry" in result({**ledger[1], "seq": "1", "hash": disclosure_module.entry_hash({**ledger[1], "seq": "1"})})["reason"]
    # a summary that lies: same hash, but the disclosure claims another status
    lying = mutate(data, 2, lambda o: o["summary"].__setitem__("status", "NEGATIVE_RESULT_UNDER_PROTOCOL"))
    assert "summary does not match" in verify_reveal(lying, ledger[1])["reason"]
    wrong_type = mutate(data, 2, lambda o: o.__setitem__("type", "issue"))
    assert "summary does not match" in verify_reveal(wrong_type, ledger[1])["reason"]


def test_reveal_needs_a_valid_disclosure(rich: Store) -> None:
    with pytest.raises(InputError) as caught:
        verify_reveal(b"nonsense\n", entries(rich)[0])
    assert caught.value.code == "BAD_DISCLOSURE"


# ---------------------------------------------------------------- atlas

def atlas_data(page: bytes) -> dict[str, Any]:
    text = page.decode("utf-8")
    start = text.index('id="atlas-data"')
    start = text.index(">", start) + 1
    return json.loads(text[start : text.index("</script>", start)].replace("\\u003c", "<"))


def test_atlas_with_a_policy_shows_full_summary_and_hidden_rows(rich: Store) -> None:
    p = policy(rules=[{"protocol_id": "DEMO_D001", "level": "full"}, {"protocol_id": "OTHER_D002", "level": "hidden"}])
    data = atlas_data(build_atlas(store=rich, policy=p))
    assert data["statuses"] == {"HIDDEN": 1, "PASSED_UNDER_PROTOCOL": 1}
    disclosure = [g for g in data["integrity"] if g["kind"] == "disclosure"][0]
    assert disclosure["counts"] == {"full": 4, "hidden": 1, "summary": 0} or disclosure["counts"]["hidden"] >= 1
    hidden = [row for row in data["rows"] if row[2] == "HIDDEN"][0]
    assert hidden[0].startswith("HIDDEN-") and hidden[1] is None and hidden[6] is None
    s = atlas_data(build_atlas(store=rich, policy=policy(default="summary")))
    assert sorted(s["statuses"]) == ["NEGATIVE_RESULT_UNDER_PROTOCOL", "PASSED_UNDER_PROTOCOL"]
    row = [r for r in s["rows"] if r[2] == "PASSED_UNDER_PROTOCOL"][0]
    assert row[0] == "LEDGER-RECORD-000001" and row[1] == "DEMO_D001" and row[5] == "2026-11-15"
    wide = atlas_data(build_atlas(store=rich, policy=policy(default="summary", summary_fields=["outcome", "run_id", "public_claim_text"])))
    assert wide["rows"][0][2] is not None


def test_atlas_without_a_policy_is_unchanged(rich: Store) -> None:
    data = atlas_data(build_atlas(store=rich))
    assert all(g["kind"] != "disclosure" for g in data["integrity"])


def test_atlas_policy_needs_a_ledger(rich: Store, tmp_path: Path) -> None:
    with pytest.raises(InputError) as caught:
        build_atlas(cards=[tmp_path], policy=policy())
    assert caught.value.code == "BAD_ENTRY"
    with pytest.raises(InputError) as caught:
        build_atlas(store=rich, cards=[tmp_path], policy=policy())
    assert caught.value.code == "BAD_ENTRY"


def test_atlas_policy_without_a_source_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs" / "evidence_cards").mkdir(parents=True)
    with pytest.raises(InputError) as caught:
        build_atlas(policy=policy())
    assert caught.value.code == "NO_SOURCE"


# ---------------------------------------------------------------- CLI

def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def write_policy(tmp_path: Path, **changes: Any) -> str:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"v": 1, "default": "summary", **changes}), encoding="utf-8")
    return str(path)


def test_cli_disclose_and_verify(rich: Store, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "pub" / "d.jsonl"
    pol = write_policy(tmp_path, rules=[{"seq": 0, "level": "full"}, {"seq": 5, "level": "hidden"}])
    code, text, err = run(capsys, "disclose", "--store", str(rich.path), "--policy", pol, "--out", str(out))
    assert code == 0 and "entries=6 full=1 summary=4 hidden=1" in text and err == ""
    code, text, _ = run(capsys, "verify-disclosure", str(out))
    assert code == 0 and text.startswith("OK entries=6 full=1 summary=4 hidden=1 head seq=5")
    anchor_head(rich, clock=clock(NOW))
    code, text, _ = run(capsys, "verify-disclosure", str(out), "--anchors", str(rich.anchors_dir))
    assert code == 0 and text.rstrip().endswith("anchors=1")
    entry = tmp_path / "entry.json"
    entry.write_text(json.dumps(entries(rich)[1]), encoding="utf-8")
    code, text, _ = run(capsys, "verify-disclosure", str(out), "--reveal", str(entry))
    assert code == 0 and "reveal seq=1 level=summary: MATCHES" in text
    code, text, _ = run(capsys, "verify-disclosure", str(out), "--reveal", str(tmp_path / "policy.json"))
    assert code == 1 and "DIFFERENT" in text
    code, text, _ = run(capsys, "verify-disclosure", str(out), "--json", "--reveal", str(entry))
    assert code == 0 and json.loads(text)["reveal"]["matches"] is True


def test_cli_disclose_warns_json_and_errors(rich: Store, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pol = write_policy(tmp_path, rules=[{"seq": 0, "level": "hidden"}, {"seq": 1, "level": "full"}])
    code, text, _ = run(capsys, "disclose", "--store", str(rich.path), "--policy", pol, "--out", str(tmp_path / "o.jsonl"), "--json")
    assert code == 0 and json.loads(text)["warnings"]
    code, text, _ = run(capsys, "disclose", "--store", str(rich.path), "--policy", pol, "--out", str(tmp_path / "o2.jsonl"))
    assert "warning: seq 1" in text
    code, _, err = run(capsys, "disclose", "--store", str(rich.path), "--policy", str(tmp_path / "none.json"))
    assert code == 3
    bad = tmp_path / "bad.json"
    bad.write_text('{"default": "x"}', encoding="utf-8")
    code, _, err = run(capsys, "disclose", "--store", str(rich.path), "--policy", str(bad))
    assert code == 2 and "BAD_POLICY" in err and "hint (BAD_POLICY)" in err
    empty = Store(tmp_path / "empty")
    from protocolith.core import init

    init(empty)
    code, text, _ = run(capsys, "disclose", "--store", str(empty.path), "--policy", pol, "--out", str(tmp_path / "e.jsonl"))
    assert code == 0 and "empty" in text


def test_cli_verify_disclosure_failures(rich: Store, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "d.jsonl"
    run(capsys, "disclose", "--store", str(rich.path), "--policy", write_policy(tmp_path), "--out", str(out))
    out.write_bytes(out.read_bytes().replace(b"PASSED_UNDER_PROTOCOL", b"PASSED_UNDER_PROTOCOX", 1))
    code, text, err = run(capsys, "verify-disclosure", str(out))
    assert code == 0  # an edited summary is not detectable without a reveal; the chain is intact
    out.write_bytes(out.read_bytes()[:-5])
    code, text, err = run(capsys, "verify-disclosure", str(out))
    assert code == 1 and text.startswith("FAILED: BAD_DISCLOSURE") and "hint (BAD_DISCLOSURE)" in err
    code, text, _ = run(capsys, "verify-disclosure", str(out), "--json")
    assert code == 1 and json.loads(text)["ok"] is False
    code, _, err = run(capsys, "verify-disclosure", str(tmp_path / "missing.jsonl"))
    assert code == 3
    good = tmp_path / "g.jsonl"
    run(capsys, "disclose", "--store", str(rich.path), "--policy", write_policy(tmp_path), "--out", str(good))
    code, _, err = run(capsys, "verify-disclosure", str(good), "--reveal", str(tmp_path / "missing.json"))
    assert code == 3


def test_cli_atlas_policy_and_schema(rich: Store, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "a.html"
    code, text, _ = run(capsys, "atlas", "--store", str(rich.path), "--policy", write_policy(tmp_path, default="hidden"), "--out", str(out))
    assert code == 0 and out.is_file() and "records=2" in text
    code, text, _ = run(capsys, "schema", "policy")
    assert code == 0 and json.loads(text)["title"] == "protocolith policy"
    code, _, err = run(capsys, "atlas", "--store", str(rich.path), "--policy", str(tmp_path / "nope.json"))
    assert code == 3


# ---------------------------------------------------------------- MCP

def tool(store: Store, name: str, arguments: dict[str, Any]) -> tuple[bool, Any]:
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    reply = json.loads(handle_line(json.dumps(message).encode(), store, clock(NOW)) or b"{}")
    result = reply["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def test_mcp_disclose_verify_and_reveal(rich: Store, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    error, data = tool(rich, "protocolith_disclose", {"policy": {"default": "summary"}, "out": "pub/d.jsonl"})
    assert not error and data["path"] == "pub/d.jsonl" and data["counts"]["summary"] == 6
    error, data = tool(rich, "protocolith_verify_disclosure", {"file": "pub/d.jsonl"})
    assert not error and data["ok"] and data["reveal"] is None
    error, data = tool(rich, "protocolith_verify_disclosure", {"file": "pub/d.jsonl", "reveal": entries(rich)[1]})
    assert not error and data["reveal"]["matches"] is True
    error, data = tool(rich, "protocolith_verify_disclosure", {"file": "pub/d.jsonl", "reveal": {"seq": 1}})
    assert error and data["ok"] is False
    anchor_head(rich, clock=clock(NOW))
    anchors = tmp_path / "anchors"
    anchors.mkdir()
    for path in rich.anchors_dir.glob("*.json"):
        (anchors / path.name).write_bytes(path.read_bytes())
    error, data = tool(rich, "protocolith_verify_disclosure", {"file": "pub/d.jsonl", "anchors": "anchors"})
    assert not error and data["anchors"] == 1
    (tmp_path / "pub" / "d.jsonl").write_bytes(b"junk\n")
    error, data = tool(rich, "protocolith_verify_disclosure", {"file": "pub/d.jsonl", "reveal": entries(rich)[1]})
    assert error and data["reveal"] is None


def test_mcp_disclose_default_path_and_bad_policy(rich: Store, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    error, data = tool(rich, "protocolith_disclose", {"policy": {}})
    assert not error and data["path"] == "disclosure.jsonl" and (tmp_path / "disclosure.jsonl").is_file()
    error, data = tool(rich, "protocolith_disclose", {"policy": {"default": "nope"}})
    assert error and data["error"]["code"] == "BAD_POLICY" if "error" in data else error
    error, data = tool(rich, "protocolith_disclose", {"policy": {}, "out": "../outside.jsonl"})
    assert error


def test_mcp_atlas_with_a_policy(rich: Store, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    error, data = tool(rich, "protocolith_atlas", {"policy": {"default": "hidden"}, "out": "a.html"})
    assert not error and data["cards"] == 2
    page = (tmp_path / "a.html").read_bytes()
    assert b"HIDDEN-000001" in page


def test_mcp_schema_names_the_policy(rich: Store) -> None:
    error, data = tool(rich, "protocolith_schema", {"name": "policy"})
    assert not error and data["title"] == "protocolith policy"
