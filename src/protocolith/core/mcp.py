# SPDX-License-Identifier: Apache-2.0
"""Minimal MCP server over stdio: newline-delimited JSON-RPC 2.0, six tools, no network."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, BinaryIO

from . import ops
from .canonical import CanonError, decode, encode
from .clock import Clock
from .errors import InputError, ProtocolithError
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
    _take(arguments, ())
    return {"entries": ops.entries(store), "head": ops.head(store)}


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
            {"protocol": _OBJECT, "supersedes": {"type": ["string", "null"], "description": "sha256 of the old version"}},
            ("protocol",),
            _freeze,
        ),
        Tool("protocolith_record", "Record the outcome of a run against a frozen protocol.", {"body": _OBJECT}, ("body",), _record),
        Tool("protocolith_deviation", "Record a deviation from a frozen protocol.", {"body": _OBJECT}, ("body",), _deviation),
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
        Tool("protocolith_log", "List all ledger entries and the current head.", {}, (), _log),
    )
}


def _result(data: Any, *, is_error: bool) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": encode(data).decode("utf-8")}], "isError": is_error}


def _initialize(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    wanted = params.get("protocolVersion")
    version = wanted if wanted in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
    return {
        "protocolVersion": version,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


def _ping(store: Store, params: dict[str, Any], clock: Clock | None) -> dict[str, Any]:
    return {}


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
