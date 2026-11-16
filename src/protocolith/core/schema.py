# SPDX-License-Identifier: Apache-2.0
"""JSON Schema (draft 2020-12) for the input bodies and the entry envelope, derived from the rules.

Every field predicate in ``rules`` has an entry in ``_BY_PRED``; a field whose predicate is missing there raises
``KeyError`` when the schema is built, so the schema cannot silently drift from the rules.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from . import rules
from .errors import InputError
from .ledger import _HASH_RE, _TS_RE, CARD_FORMAT, ENTRY_TYPES, FORMAT_VERSION, RESULT_STATUSES

DIALECT = "https://json-schema.org/draft/2020-12/schema"
NAMES = ("freeze", "record", "deviation", "issue", "entry")

_HASH: dict[str, Any] = {"type": "string", "pattern": "^" + _HASH_RE.pattern + "$"}
_TEXT: dict[str, Any] = {"type": "string", "pattern": r"\S"}
_UINT: dict[str, Any] = {"type": "integer", "minimum": 0}
_SOURCE: dict[str, Any] = {
    "type": "object",
    "properties": {"id": _TEXT, "sha256": _HASH},
    "required": ["id", "sha256"],
    "additionalProperties": False,
}
_BY_PRED: dict[Any, dict[str, Any]] = {
    rules._text: _TEXT,
    rules._obj: {"type": "object"},
    rules._uint: _UINT,
    rules._uint_list: {"type": "array", "items": _UINT},
    rules._sources: {"type": "array", "items": _SOURCE},
    rules.is_hash: _HASH,
    rules._hash_or_null: {"anyOf": [_HASH, {"type": "null"}]},
    rules._protocol_id: {"type": "string", "pattern": "^" + rules._ID_RE.pattern + "$"},
    rules._version: {"type": "string", "pattern": "^" + rules._VERSION_RE.pattern + "$"},
    rules._is_format: {"const": CARD_FORMAT},
    rules.is_ts: {"type": "string", "pattern": "^" + _TS_RE.pattern + "$"},
    rules._any: {},
}
# Fields whose predicate is a closed-set check living outside the predicate itself.
_BY_FIELD: dict[str, dict[str, Any]] = {
    "status": {"enum": sorted(RESULT_STATUSES)},
    "type": {"enum": list(ENTRY_TYPES)},
}
_DESCRIPTIONS = {
    "freeze": "Input of `freeze`: the protocol object. protocol_id and version are required; any other key is part of the protocol.",
    "record": "Input of `record` and body of a record entry.",
    "deviation": "Input of `deviation` and body of a deviation entry.",
    "issue": "Input of `issue`: the seq of the record to issue. (The stored issue body is under $defs of `entry`.)",
    "entry": "One ledger line. The body is checked by the definition for its type.",
}


def _field(name: str, pred: rules.Pred) -> dict[str, Any]:
    return copy.deepcopy(_BY_FIELD[name] if name in _BY_FIELD else _BY_PRED[pred])


def _object(required: Mapping[str, rules.Pred], optional: Mapping[str, rules.Pred]) -> dict[str, Any]:
    fields = {**required, **optional}
    return {
        "type": "object",
        "properties": {name: _field(name, pred) for name, pred in fields.items()},
        "required": list(required),
        "additionalProperties": False,
    }


def _record_body() -> dict[str, Any]:
    schema = _object(rules.RECORD_FIELDS, rules.RECORD_OPTIONAL)
    conditions = []
    for status in sorted(RESULT_STATUSES):
        needed = [rules._BLOCKING[status]] if status in rules._BLOCKING else []
        if status in rules._NEEDS_SOURCES:
            conditions.append(
                {
                    "if": {"properties": {"status": {"const": status}}},
                    "then": {"properties": {"sources": {"minItems": 1}}},
                }
            )
        if needed:
            conditions.append({"if": {"properties": {"status": {"const": status}}}, "then": {"required": needed}})
    schema["allOf"] = conditions
    return schema


def _freeze_input() -> dict[str, Any]:
    keys = ("protocol_id", "version")
    schema = _object({k: rules.FREEZE_FIELDS[k] for k in keys}, {})
    schema["additionalProperties"] = True
    return schema


def _bodies() -> dict[str, dict[str, Any]]:
    return {
        "freeze": _object(rules.FREEZE_FIELDS, {}),
        "record": _record_body(),
        "deviation": _object(rules.DEVIATION_FIELDS, {}),
        "issue": _object(rules.ISSUE_FIELDS, {}),
    }


def _entry() -> dict[str, Any]:
    schema = _object(rules.ENTRY_FIELDS, {})
    schema["properties"]["v"] = {"const": FORMAT_VERSION}
    schema["required"].append("v")
    schema["$defs"] = {f"{name}_body": body for name, body in _bodies().items()}
    schema["allOf"] = [
        {
            "if": {"properties": {"type": {"const": name}}},
            "then": {"properties": {"body": {"$ref": f"#/$defs/{name}_body"}}},
        }
        for name in ENTRY_TYPES
    ]
    return schema


def schema_for(name: str) -> dict[str, Any]:
    """The JSON Schema for one input (``freeze``, ``record``, ``deviation``, ``issue``) or the ledger ``entry``."""
    if name == "freeze":
        body = _freeze_input()
    elif name == "issue":
        body = {"type": "object", "properties": {"seq": _UINT}, "required": ["seq"], "additionalProperties": False}
    elif name == "entry":
        body = _entry()
    elif name in NAMES:
        body = _bodies()[name]
    else:
        raise InputError("BAD_ENTRY", "schema name must be one of: " + ", ".join(NAMES) + ", all")
    return {"$schema": DIALECT, "title": f"protocolith {name}", "description": _DESCRIPTIONS[name], **body}


def all_schemas() -> dict[str, dict[str, Any]]:
    return {name: schema_for(name) for name in NAMES}
