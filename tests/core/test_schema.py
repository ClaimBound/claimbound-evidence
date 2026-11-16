# SPDX-License-Identifier: Apache-2.0
"""The JSON Schemas are derived from the rules; a tiny checker proves they accept and reject the same inputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from core_support import deviation_body, protocol, record_body

from protocolith.core import decode, rules
from protocolith.core.errors import InputError
from protocolith.core.schema import NAMES, _BY_FIELD, _BY_PRED, all_schemas, schema_for

VECTORS = Path(__file__).resolve().parents[2] / "spec" / "vectors" / "ledgers.json"


def valid(value: Any, schema: dict[str, Any], root: dict[str, Any]) -> bool:
    """Validate ``value`` against the subset of draft 2020-12 used by the generated schemas."""
    if "$ref" in schema:
        return valid(value, root["$defs"][schema["$ref"].rsplit("/", 1)[1]], root)
    types = {"object": dict, "array": list, "string": str, "integer": int, "null": type(None)}
    if "type" in schema and (not isinstance(value, types[schema["type"]]) or isinstance(value, bool)):
        return False
    if "const" in schema and value != schema["const"]:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if "pattern" in schema and re.search(schema["pattern"], value) is None:
        return False
    if "minimum" in schema and value < schema["minimum"]:
        return False
    if "minItems" in schema and len(value) < schema["minItems"]:
        return False
    if "anyOf" in schema and not any(valid(value, option, root) for option in schema["anyOf"]):
        return False
    if "allOf" in schema and not all(valid(value, option, root) for option in schema["allOf"]):
        return False
    if "if" in schema and valid(value, schema["if"], root) and not valid(value, schema["then"], root):
        return False
    if "items" in schema and not all(valid(item, schema["items"], root) for item in value):
        return False
    if isinstance(value, dict):
        if any(key not in value for key in schema.get("required", [])):
            return False
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(props):
            return False
        if any(not valid(value[key], sub, root) for key, sub in props.items() if key in value):
            return False
    return True


def check(name: str, value: Any) -> bool:
    schema = schema_for(name)
    return valid(value, schema, schema)


def test_every_rule_predicate_has_a_schema() -> None:
    groups = (
        rules.FREEZE_FIELDS, rules.RECORD_FIELDS, rules.RECORD_OPTIONAL,
        rules.DEVIATION_FIELDS, rules.ISSUE_FIELDS, rules.ENTRY_FIELDS,
    )  # fmt: skip
    for group in groups:
        for field, pred in group.items():
            assert field in _BY_FIELD or pred in _BY_PRED, field
    assert set(_BY_FIELD["status"]["enum"]) == rules.RESULT_STATUSES
    assert _BY_FIELD["type"]["enum"] == list(rules.ENTRY_TYPES)
    assert schema_for("record")["required"] == list(rules.RECORD_FIELDS)
    assert set(schema_for("record")["properties"]) == set(rules.RECORD_FIELDS) | set(rules.RECORD_OPTIONAL)


def test_schemas_are_json_and_named() -> None:
    everything = all_schemas()
    assert tuple(everything) == NAMES
    json.dumps(everything)
    for name, schema in everything.items():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["title"] == f"protocolith {name}" and schema["description"]
    with pytest.raises(InputError) as info:
        schema_for("nope")
    assert info.value.code == "BAD_ENTRY"


def test_sample_inputs_match_the_schemas() -> None:
    assert check("freeze", protocol())
    assert check("record", record_body())
    assert check("deviation", deviation_body())
    assert check("issue", {"seq": 3})
    assert not check("freeze", {"version": "1"})
    assert not check("freeze", {"protocol_id": "bad id", "version": "1"})
    assert not check("issue", {"seq": -1})
    assert not check("issue", {"seq": 1, "x": 1})
    assert not check("deviation", {**deviation_body(), "extra": 1})
    assert not check("record", record_body(status="MADE_UP"))
    assert not check("record", record_body(run_id="  "))
    assert not check("record", record_body(sources=[{"id": "a"}]))
    assert not check("record", record_body(deviations=[-1]))
    assert not check("record", record_body(status="BLOCKED_SOURCE"))
    assert check("record", record_body(status="BLOCKED_SOURCE", block_reason="robots"))
    assert not check("record", record_body(sources=[]))
    assert check("record", record_body(status="INSUFFICIENT_COVERAGE", sources=[]))


def test_the_entry_schema_agrees_with_the_conformance_vectors() -> None:
    checked = 0
    for case in json.loads(VECTORS.read_text(encoding="utf-8"))["cases"]:
        if not case["expect"]["ok"]:
            continue
        for line in case["ledger"].splitlines():
            assert check("entry", decode(line.encode("utf-8"))), case["name"]
            checked += 1
    assert checked > 5
    entry = {"body": deviation_body(), "hash": "a" * 64, "prev": "0" * 64, "seq": 0, "ts": "2026-11-15T10:00:00Z", "type": "deviation", "v": 1}
    assert check("entry", entry)
    assert not check("entry", {**entry, "v": 2})
    assert not check("entry", {**entry, "type": "freeze"})
    assert not check("entry", {**entry, "ts": "yesterday"})
