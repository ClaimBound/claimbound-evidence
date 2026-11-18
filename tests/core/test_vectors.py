# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from protocolith.core import CanonError, decode, encode, scan
from protocolith.core.issue import card_hash

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "spec" / "vectors"
SCRIPT = ROOT / "scripts" / "build_core_vectors.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_core_vectors", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_core_vectors"] = module
    spec.loader.exec_module(module)
    return module


def cases(name: str) -> list[dict[str, Any]]:
    document = json.loads((VECTORS / name).read_text(encoding="utf-8"))
    found: list[dict[str, Any]] = document["cases"]
    return found


def test_committed_vectors_are_identical_to_a_fresh_build() -> None:
    built = load_script().build_vectors()
    assert sorted(built) == sorted(path.name for path in VECTORS.glob("*.json"))
    for name, text in built.items():
        assert (VECTORS / name).read_text(encoding="utf-8") == text, f"{name} is stale: run scripts/build_core_vectors.py"


def test_build_is_deterministic() -> None:
    module = load_script()
    assert module.build_vectors() == module.build_vectors()


@pytest.mark.parametrize("case", cases("canonical.json"), ids=lambda c: c["name"])
def test_canonical_vector(case: dict[str, Any]) -> None:
    raw = bytes.fromhex(case["input_hex"]) if "input_hex" in case else case["input_text"].encode("utf-8")
    expect = case["expect"]
    if expect["ok"]:
        assert encode(decode(raw)).decode("utf-8") == expect["canonical"]
    else:
        with pytest.raises(CanonError) as info:
            decode(raw)
        assert info.value.code == expect["code"]


@pytest.mark.parametrize("case", cases("hashes.json"), ids=lambda c: c["name"])
def test_hash_vector(case: dict[str, Any]) -> None:
    canonical = encode(decode(case["input_text"]))
    assert canonical.decode("utf-8") == case["canonical"]
    assert hashlib.sha256(canonical).hexdigest() == case["sha256"]


def expand(case: dict[str, Any]) -> bytes:
    if "ledger_template" in case:
        t = case["ledger_template"]
        return (t["head"] + t["fill"] * t["count"] + t["tail"]).encode("utf-8")
    return str(case["ledger"]).encode("utf-8")


@pytest.mark.parametrize("case", cases("ledgers.json"), ids=lambda c: c["name"])
def test_ledger_vector(case: dict[str, Any]) -> None:
    verdict, _ = scan(expand(case), card_hash)
    assert verdict.ok == case["expect"]["ok"]
    assert verdict.codes == case["expect"]["codes"]


def test_every_rule_has_a_failing_vector() -> None:
    codes = {code for case in cases("ledgers.json") for code in case["expect"]["codes"]}
    required = {
        "BAD_SEQ", "BAD_PREV", "BAD_HASH", "NOT_CANONICAL", "TS_REGRESSION", "UNKNOWN_PROTOCOL", "DUPLICATE_FREEZE",
        "BAD_STATUS", "MISSING_FIELD", "DANGLING_REF", "BAD_CARD", "UNKNOWN_VERSION", "TRUNCATED_TAIL",
        "ENTRY_TOO_LARGE", "TOO_DEEP",
    }  # fmt: skip
    assert required <= codes
    rules = {case["rule"] for case in cases("ledgers.json")}
    assert {f"R{n}" for n in range(1, 12)} <= rules


@pytest.mark.parametrize("case", cases("disclosures.json"), ids=lambda c: c["name"])
def test_disclosure_vector(case: dict[str, Any]) -> None:
    from protocolith.core import parse_policy, verify_disclosure
    from protocolith.core.disclosure import disclose_verifier

    report = verify_disclosure(case["disclosure"].encode("utf-8"))
    assert report.ok == case["expect"]["ok"] and report.codes == case["expect"]["codes"]
    if "ledger" in case:
        _, verifier = scan(case["ledger"].encode("utf-8"), card_hash)
        built = disclose_verifier(verifier, parse_policy(case["policy"]))
        assert built.data.decode("utf-8") == case["disclosure"] and built.counts == case["expect"]["counts"]


@pytest.mark.parametrize("case", cases("anchors.json"), ids=lambda c: c["name"])
def test_anchor_vector(case: dict[str, Any]) -> None:
    from protocolith.core.anchor import anchor_name, build_statement
    from protocolith.core import sha256_hex

    statement = case["statement"]
    assert encode(statement).decode("utf-8") == case["canonical"]
    assert hashlib.sha256(case["canonical"].encode("utf-8")).hexdigest() == case["anchor_id"] == sha256_hex(statement)
    rebuilt = build_statement(
        statement["head_seq"], statement["head_hash"], statement["entries"], statement["created_at"], statement["protocolith_version"]
    )
    assert rebuilt == statement and f"{anchor_name(statement['head_seq'], statement['head_hash'])}.json" == case["file_name"]
