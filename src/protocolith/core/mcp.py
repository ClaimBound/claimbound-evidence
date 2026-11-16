# SPDX-License-Identifier: Apache-2.0
"""Minimal MCP server over stdio: newline-delimited JSON-RPC 2.0, tools and read-only resources, no network."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from . import ops
from .atlas import DEFAULT_OUT, DEFAULT_TITLE, build_atlas_result, confine, write_atlas
from .capture import capture
from .canonical import CanonError, decode, encode
from .clock import Clock
from .errors import InputError, ProtocolithError
from .schema import NAMES, all_schemas, schema_for
from .ledger import ENTRY_TYPES, RESULT_STATUSES
from .store import Store

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_NAME = "protocolith"
SERVER_VERSION = "0.6.0"

Handler = Callable[[Store, dict[str, Any], Clock | None], Any]


class RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _take(arguments: dict[str, Any], required: tuple[str, ...], optional: tuple[str, ...] = ()) -> dict[str, Any]:
    missing = [key for key in required if key not in arguments]
    if missing:
        raise InputError("MISSING_FIELD", "missing arguments: " + ", ".join(missing))
    extra = sorted(key for key in arguments if key not in required + optional)
    if extra:
        raise InputError("BAD_ENTRY", "unexpected arguments: " + ", ".join(extra))
    return arguments


def _freeze(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    args = _take(arguments, ("protocol",), ("supersedes",))
    return ops.freeze(store, args["protocol"], supersedes=args.get("supersedes"), clock=clock)


def _record(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    return ops.record(store, _take(arguments, ("body",))["body"], clock=clock)


def _deviation(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    return ops.deviation(store, _take(arguments, ("body",))["body"], clock=clock)


def _verify(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    args = _take(arguments, (), ("expect_head",))
    return ops.verify(store, args.get("expect_head")).to_dict()


def _issue(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    return ops.issue(store, _take(arguments, ("seq",))["seq"], clock=clock)


def _log(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    args = _take(arguments, (), ("protocol", "type", "status", "tail"))
    return {"entries": ops.log(store, **args), "head": ops.head(store)}


def _show(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    return ops.show(store, _take(arguments, ("seq",))["seq"])


def _summary(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    return ops.summary(store, _take(arguments, (), ("protocol",)).get("protocol"))


def _capture(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    args = _take(arguments, (), ("files", "env"))
    files = args.get("files", [])
    if not (isinstance(files, list) and all(isinstance(name, str) for name in files)):
        raise InputError("BAD_ENTRY", "files must be a list of strings")
    return capture(files, env=args.get("env") is True)


def _schema(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    name = _take(arguments, (), ("name",)).get("name", "all")
    return all_schemas() if name == "all" else schema_for(name)


def _atlas(store: Store, arguments: dict[str, Any], clock: Clock | None) -> Any:
    args = _take(arguments, (), ("out", "title", "cards", "i18n", "default_lang", "max_rows"))
    cards = args.get("cards", [])
    if not (isinstance(cards, list) and all(isinstance(name, str) for name in cards)):
        raise InputError("BAD_ENTRY", "cards must be a list of strings")
    folders = [confine(name) for name in cards]
    i18n = confine(args["i18n"]) if "i18n" in args else None
    out = confine(args.get("out", DEFAULT_OUT))
    result = build_atlas_result(
        store=None if folders else store,
        cards=folders,
        title=args.get("title", DEFAULT_TITLE),
        i18n_dir=i18n,
        default_lang=args.get("default_lang", "en"),
        max_rows=args.get("max_rows"),
    )
    path = write_atlas(result.html, out)
    return {**result.to_dict(), "path": path.relative_to(Path.cwd().resolve()).as_posix()}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    properties: Mapping[str, Any]
    required: tuple[str, ...]
    run: Handler

    def listing(self) -> dict[str, Any]:
        schema = {
            "type": "object",
            "properties": dict(self.properties),
            "required": list(self.required),
            "additionalProperties": False,
        }
        return {"name": self.name, "description": self.description, "inputSchema": schema}


_OBJECT = {"type": "object"}
TOOLS: dict[str, Tool] = {
    tool.name: tool
    for tool in (
        Tool(
            "protocolith_freeze",
            "Freeze a protocol (an object with protocol_id and version) before a run.",
            {
                "protocol": _OBJECT,
                "supersedes": {"type": ["string", "null"], "description": "sha256 of the old version"},
            },
            ("protocol",),
            _freeze,
        ),
        Tool(
            "protocolith_record",
            "Record the outcome of a run against a frozen protocol.",
            {"body": _OBJECT},
            ("body",),
            _record,
        ),
        Tool(
            "protocolith_deviation",
            "Record a deviation from a frozen protocol.",
            {"body": _OBJECT},
            ("body",),
            _deviation,
        ),
        Tool(
            "protocolith_verify",
            "Verify the whole ledger; isError is true when it does not verify. "
            "With expect_head (SEQ:HASH) the ledger must also contain that entry, else HEAD_MISMATCH.",
            {"expect_head": {"type": "string", "description": "SEQ:HASH of a previously published head"}},
            (),
            _verify,
        ),
        Tool(
            "protocolith_issue",
            "Issue the evidence card (JSON and SVG, inside the store) for the record at seq.",
            {"seq": {"type": "integer", "minimum": 0}},
            ("seq",),
            _issue,
        ),
        Tool(
            "protocolith_log",
            "List ledger entries (optionally filtered) and the current head.",
            {
                "protocol": {"type": "string", "description": "only entries of this protocol_id"},
                "type": {"enum": list(ENTRY_TYPES)},
                "status": {"enum": sorted(RESULT_STATUSES), "description": "only records with this status"},
                "tail": {"type": "integer", "minimum": 1, "description": "keep the last N matches"},
            },
            (),
            _log,
        ),
        Tool(
            "protocolith_show",
            "One entry with its protocol, the entries it points at and the entries that point at it.",
            {"seq": {"type": "integer", "minimum": 0}},
            ("seq",),
            _show,
        ),
        Tool(
            "protocolith_summary",
            "What was done and which results are honest: verdict, head, counts by type and status, "
            "a per-protocol table and the problems found. One fast call; start here.",
            {"protocol": {"type": "string", "description": "only this protocol_id"}},
            (),
            _summary,
        ),
        Tool(
            "protocolith_capture",
            "Describe the environment (Python, platform, machine, protocolith version) and hash input files inside "
            "the current directory. Returns a fragment for the outcome object of a record. Runs nothing; reads no "
            "environment values.",
            {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "paths inside the working directory",
                },
                "env": {"type": "boolean", "description": "include the environment (default when no file is given)"},
            },
            (),
            _capture,
        ),
        Tool(
            "protocolith_atlas",
            "Write a self-contained offline HTML atlas of the experiments (the ledger records, or the evidence card "
            "directories named in cards) and return the path written, inside the working directory. "
            "isError is true when the ledger fails verification; the atlas is still written, with a warning banner.",
            {
                "out": {"type": "string", "description": "output .html file or directory (default protocolith-atlas.html)"},
                "title": {"type": "string"},
                "cards": {"type": "array", "items": {"type": "string"}, "description": "card directories, used instead of the ledger"},
                "i18n": {"type": "string", "description": "directory of <code>.json translation files"},
                "default_lang": {"type": "string"},
                "max_rows": {"type": "integer", "minimum": 1},
            },
            (),
            _atlas,
        ),
        Tool(
            "protocolith_schema",
            "JSON Schema (draft 2020-12) of the inputs: freeze, record, deviation, issue, entry, or all.",
            {"name": {"enum": [*NAMES, "all"]}},
            (),
            _schema,
        ),
    )
}


def _result(data: Any, *, is_error: bool) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": encode(data).decode("utf-8")}], "isError": is_error}


def _initialize(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    wanted = params.get("protocolVersion")
    version = wanted if wanted in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
    return {
        "protocolVersion": version,
        "capabilities": {"resources": {}, "tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


def _ping(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    return {}


def _resources_list(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    items = [("summary", "Ledger summary"), ("ledger", "All ledger entries and the head")]
    items += [(f"schema/{name}", f"JSON Schema: {name}") for name in NAMES]
    return {
        "resources": [
            {"uri": f"protocolith://{path}", "name": path, "description": text, "mimeType": "application/json"}
            for path, text in items
        ]
    }


def _resource_data(store: Store, uri: Any) -> Any:
    prefix = "protocolith://"
    path = uri[len(prefix) :] if isinstance(uri, str) and uri.startswith(prefix) else ""
    if path == "summary":
        return ops.summary(store)
    if path == "ledger":
        return {"entries": ops.entries(store), "head": ops.head(store)}
    if path.startswith("schema/") and path[7:] in NAMES:
        return schema_for(path[7:])
    raise RpcError(-32002, f"resource not found: {uri!r}")


def _resources_read(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    uri = params.get("uri")
    try:
        data = _resource_data(store, uri)
    except ProtocolithError as exc:
        raise RpcError(-32000, f"{exc.code}: {exc.message}") from None
    return {"contents": [{"uri": uri, "mimeType": "application/json", "text": encode(data).decode("utf-8")}]}


def _tools_list(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    return {"tools": [tool.listing() for tool in TOOLS.values()]}


def _tools_call(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    name = params.get("name")
    tool = TOOLS.get(name) if isinstance(name, str) else None
    if tool is None:
        raise RpcError(-32602, f"unknown tool: {name!r}")
    arguments = params.get("arguments", {})
    if not isinstance(arguments, dict):
        raise RpcError(-32602, "arguments must be an object")
    try:
        data = tool.run(store, arguments, clock)
    except ProtocolithError as exc:
        return _result(exc.to_dict(), is_error=True)
    return _result(data, is_error=isinstance(data, dict) and data.get("ok") is False)


METHODS: dict[str, Callable[[Store, dict[str, Any], Clock | None], dict[str, Any]]] = {
    "initialize": _initialize,
    "ping": _ping,
    "resources/list": _resources_list,
    "resources/read": _resources_read,
    "tools/list": _tools_list,
    "tools/call": _tools_call,
}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_message(message: Any, store: Store, clock: Clock | None = None) -> dict[str, Any] | None:
    """Answer one decoded JSON-RPC message; notifications get no answer."""
    if not (isinstance(message, dict) and message.get("jsonrpc") == "2.0" and isinstance(message.get("method"), str)):
        request_id = message.get("id") if isinstance(message, dict) else None
        return _error(request_id, -32600, "invalid request")
    is_request = "id" in message
    request_id = message.get("id")
    method = METHODS.get(message["method"])
    params = message.get("params", {})
    if not is_request:
        return None
    if method is None:
        return _error(request_id, -32601, f"method not found: {message['method']}")
    if not isinstance(params, dict):
        return _error(request_id, -32602, "params must be an object")
    try:
        return {"jsonrpc": "2.0", "id": request_id, "result": method(store, params, clock)}
    except RpcError as exc:
        return _error(request_id, exc.code, exc.message)
    except Exception as exc:  # a bug must not kill the server or leak a traceback to stdout
        return _error(request_id, -32603, f"internal error: {type(exc).__name__}")


def handle_line(raw: bytes, store: Store, clock: Clock | None = None) -> bytes | None:
    try:
        message = decode(raw)
    except CanonError as exc:
        reply: dict[str, Any] | None = _error(None, -32700, f"parse error: {exc.code}: {exc.message}")
    else:
        reply = handle_message(message, store, clock)
    if reply is None:
        return None
    return json.dumps(reply, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def serve(store: Store, stdin: Iterable[bytes], stdout: BinaryIO, clock: Clock | None = None) -> None:
    """Read requests line by line until EOF. Nothing but JSON-RPC replies is written to ``stdout``."""
    for raw in stdin:
        if not raw.strip():
            continue
        reply = handle_line(raw, store, clock)
        if reply is not None:
            stdout.write(reply + b"\n")
            stdout.flush()
