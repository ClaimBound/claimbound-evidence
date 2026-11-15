# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from typing import Any

import pytest
from core_support import NOW, clock, protocol, record_body

from protocolith.core import Store, freeze
from protocolith.core import mcp as mcp_module
from protocolith.core.mcp import TOOLS, handle_line, handle_message, serve


def call(store: Store, payload: Any, raw: bool = False) -> Any:
    data = payload if raw else json.dumps(payload)
    reply = handle_line(data.encode() if isinstance(data, str) else data, store, clock(NOW))
    return None if reply is None else json.loads(reply)


def rpc(store: Store, method: str, params: Any = None, request_id: Any = 1) -> Any:
    message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return call(store, message)


def tool(store: Store, name: str, arguments: Any = None) -> tuple[bool, Any]:
    params: dict[str, Any] = {"name": name}
    if arguments is not None:
        params["arguments"] = arguments
    result = rpc(store, "tools/call", params)["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def test_initialize_negotiates_the_protocol_version(store: Store) -> None:
    result = rpc(store, "initialize", {"protocolVersion": "2025-03-26"})["result"]
    assert result["protocolVersion"] == "2025-03-26"
    assert result["serverInfo"]["name"] == "protocolith" and result["capabilities"] == {"tools": {}}
    assert rpc(store, "initialize", {"protocolVersion": "1999-01-01"})["result"]["protocolVersion"] == "2025-06-18"
    assert rpc(store, "initialize", {})["result"]["protocolVersion"] == "2025-06-18"


def test_ping_and_notifications(store: Store) -> None:
    assert rpc(store, "ping") == {"jsonrpc": "2.0", "id": 1, "result": {}}
    assert call(store, {"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert call(store, {"jsonrpc": "2.0", "method": "no/such/notification"}) is None


def test_tools_list_names_and_schemas(store: Store) -> None:
    tools = rpc(store, "tools/list")["result"]["tools"]
    assert [t["name"] for t in tools] == [
        "protocolith_freeze", "protocolith_record", "protocolith_deviation",
        "protocolith_verify", "protocolith_issue", "protocolith_log",
    ]  # fmt: skip
    for entry in tools:
        schema = entry["inputSchema"]
        assert schema["type"] == "object" and schema["additionalProperties"] is False
        assert set(schema["required"]) <= set(schema["properties"])
        assert entry["description"]


def test_tool_flow(store: Store) -> None:
    is_error, entry = tool(store, "protocolith_freeze", {"protocol": protocol()})
    assert not is_error and entry["seq"] == 0
    is_error, entry = tool(store, "protocolith_record", {"body": record_body()})
    assert not is_error and entry["type"] == "record"
    assert not tool(store, "protocolith_deviation", {"body": {"protocol_sha256": entry["body"]["protocol_sha256"], "kind": "k", "description": "d"}})[0]
    is_error, result = tool(store, "protocolith_issue", {"seq": 1})
    assert not is_error and result["json_path"].startswith(str(store.cards_dir))
    is_error, verdict = tool(store, "protocolith_verify", {})
    assert not is_error and verdict["ok"] and verdict["count"] == 4
    is_error, log = tool(store, "protocolith_log")
    assert not is_error and len(log["entries"]) == 4 and log["head"]["seq"] == 3
    is_error, entry = tool(store, "protocolith_freeze", {"protocol": {**protocol(), "version": "2"}, "supersedes": log["entries"][0]["body"]["protocol_sha256"]})
    assert not is_error


def test_tool_failures_return_is_error_with_code(store: Store) -> None:
    is_error, error = tool(store, "protocolith_record", {"body": record_body()})
    assert is_error and error["error"]["code"] == "UNKNOWN_PROTOCOL" and error["ok"] is False
    assert tool(store, "protocolith_record", {})[1]["error"]["code"] == "MISSING_FIELD"
    assert tool(store, "protocolith_record", {"body": {}, "extra": 1})[1]["error"]["code"] == "BAD_ENTRY"
    assert tool(store, "protocolith_verify", {"x": 1})[1]["error"]["code"] == "BAD_ENTRY"
    assert tool(store, "protocolith_verify")[1]["error"]["code"] == "NO_LEDGER"
    assert tool(store, "protocolith_issue", {"seq": 3})[1]["error"]["code"] == "NO_LEDGER"


def test_verify_failure_is_an_error_result(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    store.ledger_path.write_bytes(store.ledger_path.read_bytes() + b"{")
    is_error, verdict = tool(store, "protocolith_verify", {})
    assert is_error and verdict["codes"] == ["TRUNCATED_TAIL"]


def test_json_rpc_errors(store: Store) -> None:
    assert rpc(store, "nope")["error"]["code"] == -32601
    assert rpc(store, "tools/call", {"name": "nope"})["error"]["code"] == -32602
    assert rpc(store, "tools/call", {})["error"]["code"] == -32602
    assert rpc(store, "tools/call", {"name": "protocolith_log", "arguments": []})["error"]["code"] == -32602
    assert rpc(store, "ping", [1])["error"]["code"] == -32602
    assert call(store, "{not json", raw=True)["error"]["code"] == -32700
    assert call(store, '{"id":1.5}', raw=True)["error"]["code"] == -32700
    assert call(store, b"\xff", raw=True)["error"]["code"] == -32700
    for bad in ([1], 5, {"id": 7, "method": "ping"}, {"jsonrpc": "2.0", "id": 8, "method": 5}, {"jsonrpc": "1.0", "method": "ping"}):
        reply = call(store, bad)
        assert reply["error"]["code"] == -32600 and reply["jsonrpc"] == "2.0"
    assert call(store, {"id": 7, "method": "ping"})["id"] == 7


def test_internal_errors_do_not_kill_the_server(store: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: Any) -> Any:
        raise RuntimeError("secret detail")

    monkeypatch.setitem(mcp_module.METHODS, "ping", boom)
    reply = rpc(store, "ping")
    assert reply["error"] == {"code": -32603, "message": "internal error: RuntimeError"}


def test_handle_message_direct(store: Store) -> None:
    assert handle_message({"jsonrpc": "2.0", "method": "ping"}, store) is None
    assert handle_message({"jsonrpc": "2.0", "id": "x", "method": "ping"}, store) == {"jsonrpc": "2.0", "id": "x", "result": {}}


def test_serve_loop_skips_blank_lines_and_writes_only_replies(store: Store) -> None:
    lines = [
        b"\n",
        b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n',
        b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n',
        b"garbage\n",
    ]
    out = io.BytesIO()
    serve(store, lines, out, clock(NOW))
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [r.get("id") for r in replies] == [1, None]
    assert replies[1]["error"]["code"] == -32700


def test_tools_table_matches_the_spec_names() -> None:
    assert set(TOOLS) == {f"protocolith_{n}" for n in ("freeze", "record", "deviation", "verify", "issue", "log")}


def test_stdio_subprocess(tmp_path: Any) -> None:
    store = tmp_path / "s"
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "protocolith_freeze", "arguments": {"protocol": protocol()}}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "protocolith_verify", "arguments": {}}},
    ]
    stdin = "".join(json.dumps(r) + "\n" for r in requests)
    done = subprocess.run(
        [sys.executable, "-m", "protocolith.cli", "mcp", "--store", str(store)],
        input=stdin, capture_output=True, text=True, timeout=60, cwd=tmp_path, env={**os.environ, "PROTOCOLITH_NOW": NOW},
    )  # fmt: skip
    assert done.returncode == 0 and done.stderr == ""
    replies = [json.loads(line) for line in done.stdout.splitlines()]
    assert [r["id"] for r in replies] == [1, 2, 3]
    assert json.loads(replies[2]["result"]["content"][0]["text"])["ok"] is True
