# SPDX-License-Identifier: Apache-2.0
"""Random freeze/record/deviation/issue sequences against a small independent model."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from hardening_support import CARD, HASH_A, oracle_entry_hash, ts
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, precondition, rule

from protocolith.core import InputError, Store, deviation, entries, freeze, head, issue, record, scan, verify
from protocolith.core.issue import card_hash
from protocolith.core.ledger import ZERO_HASH
from protocolith.core.canonical import sha256_hex

STATUSES = ["PASSED_UNDER_PROTOCOL", "NEGATIVE_RESULT_UNDER_PROTOCOL", "BLOCKED_SOURCE", "INSUFFICIENT_COVERAGE",
            "SOURCE_DRIFT", "REPRODUCED_OUTCOME"]  # fmt: skip
NEEDS_SOURCES = {"PASSED_UNDER_PROTOCOL", "NEGATIVE_RESULT_UNDER_PROTOCOL", "REPRODUCED_OUTCOME"}


def model_sha(value: Any) -> str:
    """Independent of the core: the standard library only."""
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class LedgerMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.dir = Path(tempfile.mkdtemp(prefix="plith-state-"))
        self.store = Store(self.dir / "store")
        self.clock_s = 0
        self.log: list[dict[str, Any]] = []  # model entries: {"type", "body", "ts"}
        self.protocols: dict[str, tuple[str, str]] = {}  # sha -> (id, version)
        self.versions: set[tuple[str, str]] = set()
        self.deviations: dict[int, str] = {}  # seq -> protocol sha
        self.records: dict[int, str] = {}  # seq -> protocol sha
        self.issued: dict[str, int] = {}  # protocol_id -> record seq whose card file exists (one per id and day)

    def teardown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    # -- helpers --------------------------------------------------------------------------------
    def tick(self, step: int = 1) -> Any:
        self.clock_s += step
        value = ts(self.clock_s)
        return lambda: value

    def commit(self, kind: str, body: dict[str, Any], entry: dict[str, Any]) -> None:
        self.log.append({"type": kind, "body": body, "ts": entry["ts"]})

    # -- rules ----------------------------------------------------------------------------------
    @initialize()
    def start(self) -> None:
        assert not self.store.ledger_path.exists()

    @rule(pid=st.sampled_from(["P1", "P2", "P3"]), version=st.sampled_from(["1", "2", "3"]), note=st.sampled_from(["a", "b"]),
          supersede=st.booleans(), data=st.data())  # fmt: skip
    def freeze_protocol(self, pid: str, version: str, note: str, supersede: bool, data: st.DataObject) -> None:
        protocol = {"gate": note, "protocol_id": pid, "version": version}
        old = None
        if supersede and self.protocols:
            old = data.draw(st.sampled_from(sorted(self.protocols)))
        sha = model_sha(protocol)
        will_fail = (pid, version) in self.versions or sha in self.protocols or (old is not None and self.protocols[old][0] != pid)
        before = self.store.ledger_path.read_bytes() if self.store.ledger_path.exists() else b""
        if will_fail:
            try:
                freeze(self.store, protocol, supersedes=old, clock=self.tick())
            except InputError as exc:
                assert exc.code in {"DUPLICATE_FREEZE", "UNKNOWN_PROTOCOL"}
            else:
                raise AssertionError("freeze should have been rejected")
            assert self.store.ledger_path.read_bytes() == before if before else not self.store.ledger_path.exists()
            return
        entry = freeze(self.store, protocol, supersedes=old, clock=self.tick())
        assert entry["body"]["protocol_sha256"] == sha
        self.versions.add((pid, version))
        self.protocols[sha] = (pid, version)
        self.commit("freeze", entry["body"], entry)

    @precondition(lambda self: bool(self.protocols))
    @rule(data=st.data(), kind=st.sampled_from(["source_change", "late_data"]))
    def add_deviation(self, data: st.DataObject, kind: str) -> None:
        sha = data.draw(st.sampled_from(sorted(self.protocols)))
        entry = deviation(self.store, {"protocol_sha256": sha, "kind": kind, "description": "d"}, clock=self.tick())
        self.deviations[entry["seq"]] = sha
        self.commit("deviation", entry["body"], entry)

    @rule(data=st.data(), status=st.sampled_from(STATUSES), with_sources=st.booleans(), with_reason=st.booleans(),
          pick_dev=st.booleans(), unknown=st.booleans())  # fmt: skip
    def add_record(self, data: st.DataObject, status: str, with_sources: bool, with_reason: bool, pick_dev: bool, unknown: bool) -> None:
        if not self.protocols and not unknown:
            unknown = True
        sha = HASH_A if unknown else data.draw(st.sampled_from(sorted(self.protocols)))
        devs: list[int] = []
        if pick_dev and not unknown:
            devs = [s for s, p in self.deviations.items() if p == sha][:2]
        body: dict[str, Any] = {
            "protocol_sha256": sha, "run_id": f"run-{len(self.log)}", "status": status, "outcome": {"n": len(self.log)},
            "sources": [{"id": "s", "sha256": HASH_A}] if with_sources else [], "reproduction_level": "not independently reproduced",
            "claim_boundary": "bounded", "deviations": devs, "card": dict(CARD),
        }  # fmt: skip
        if with_reason:
            body["block_reason"] = "blocked"
            body["drift_reason"] = "drifted"
        valid = not unknown and not (status in NEEDS_SOURCES and not with_sources)
        valid = valid and not (status == "BLOCKED_SOURCE" and not with_reason) and not (status == "SOURCE_DRIFT" and not with_reason)
        if not valid:
            before = self.store.ledger_path.read_bytes() if self.store.ledger_path.exists() else b""
            try:
                record(self.store, body, clock=self.tick())
            except InputError as exc:
                assert exc.code in {"UNKNOWN_PROTOCOL", "MISSING_FIELD"}
            else:
                raise AssertionError("record should have been rejected")
            after = self.store.ledger_path.read_bytes() if self.store.ledger_path.exists() else b""
            assert after == before
            return
        entry = record(self.store, body, clock=self.tick())
        self.records[entry["seq"]] = sha
        self.commit("record", entry["body"], entry)

    @precondition(lambda self: bool(self.log))
    @rule(back=st.integers(1, 5))
    def clock_regression_is_rejected(self, back: int) -> None:
        earlier = ts(max(self.clock_s - back, 0) if self.log else 0)
        if earlier >= self.log[-1]["ts"]:
            return
        before = self.store.ledger_path.read_bytes()
        try:
            deviation(self.store, {"protocol_sha256": next(iter(self.protocols)), "kind": "k", "description": "d"}, clock=lambda: earlier)
        except InputError as exc:
            assert exc.code == "TS_REGRESSION"
        else:
            raise AssertionError("a regressing clock must be rejected")
        assert self.store.ledger_path.read_bytes() == before

    @precondition(lambda self: bool(self.records))
    @rule(data=st.data())
    def issue_card(self, data: st.DataObject) -> None:
        seq = data.draw(st.sampled_from(sorted(self.records)))
        pid = self.protocols[self.records[seq]][0]
        if self.issued.get(pid, seq) != seq:
            # evidence_id is PLITH-<protocol_id>-<day>: a second record of the same protocol on the same day collides.
            before = self.store.ledger_path.read_bytes()
            try:
                issue(self.store, seq, clock=self.tick())
            except InputError as exc:
                assert exc.code == "CARD_EXISTS"
            else:
                raise AssertionError("a different card under the same evidence_id must be refused")
            assert self.store.ledger_path.read_bytes() == before
            return
        result = issue(self.store, seq, clock=self.tick())
        self.issued[pid] = seq
        assert result["entry"]["body"]["card_sha256"] == model_sha(result["card"])
        self.commit("issue", result["entry"]["body"], result["entry"])

    @precondition(lambda self: bool(self.log))
    @rule(seq=st.integers(0, 40))
    def issue_non_record_is_rejected(self, seq: int) -> None:
        if seq in self.records:
            return
        try:
            issue(self.store, seq, clock=self.tick())
        except InputError as exc:
            assert exc.code == "DANGLING_REF"
        else:
            raise AssertionError("only records can be issued")

    # -- invariants -----------------------------------------------------------------------------
    @invariant()
    def ledger_matches_model(self) -> None:
        if not self.log:
            assert not self.store.ledger_path.exists() or self.store.ledger_path.read_bytes() == b""
            return
        verdict = verify(self.store)
        assert verdict.ok, verdict.violations
        assert verdict.count == len(self.log)
        found = entries(self.store)
        assert len(found) == len(self.log)
        prev = ZERO_HASH
        for seq, (entry, expected) in enumerate(zip(found, self.log, strict=True)):
            assert entry["seq"] == seq and entry["type"] == expected["type"] and entry["body"] == expected["body"]
            assert entry["ts"] == expected["ts"] and entry["prev"] == prev
            assert entry["hash"] == oracle_entry_hash(entry)  # independent hash construction
            prev = entry["hash"]
        info = head(self.store)
        assert info == {"count": len(self.log), "hash": prev, "seq": len(self.log) - 1}
        verdict2, _ = scan(self.store.ledger_path.read_bytes(), card_hash)
        assert verdict2.ok and verdict.head_hash == prev
        assert sha256_hex(found[0]["body"]["protocol"]) == found[0]["body"]["protocol_sha256"]


TestLedgerMachine = LedgerMachine.TestCase
TestLedgerMachine.settings = settings(stateful_step_count=14)
