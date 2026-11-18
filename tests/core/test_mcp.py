# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
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
    assert result["serverInfo"]["name"] == "protocolith" and result["capabilities"] == {
        "prompts": {}, "resources": {}, "tools": {},
    }
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
        "protocolith_verify", "protocolith_claim_check", "protocolith_anchor", "protocolith_issue", "protocolith_log", "protocolith_show",
        "protocolith_summary", "protocolith_capture", "protocolith_atlas", "protocolith_schema",
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
    assert not tool(
        store,
        "protocolith_deviation",
        {"body": {"protocol_sha256": entry["body"]["protocol_sha256"], "kind": "k", "description": "d"}},
    )[0]
    is_error, result = tool(store, "protocolith_issue", {"seq": 1})
    assert not is_error and result["json_path"].startswith(str(store.cards_dir))
    is_error, verdict = tool(store, "protocolith_verify", {})
    assert not is_error and verdict["ok"] and verdict["count"] == 4
    is_error, log = tool(store, "protocolith_log")
    assert not is_error and len(log["entries"]) == 4 and log["head"]["seq"] == 3
    is_error, entry = tool(
        store,
        "protocolith_freeze",
        {"protocol": {**protocol(), "version": "2"}, "supersedes": log["entries"][0]["body"]["protocol_sha256"]},
    )
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
    for bad in (
        [1],
        5,
        {"id": 7, "method": "ping"},
        {"jsonrpc": "2.0", "id": 8, "method": 5},
        {"jsonrpc": "1.0", "method": "ping"},
    ):
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
    assert handle_message({"jsonrpc": "2.0", "id": "x", "method": "ping"}, store) == {
        "jsonrpc": "2.0",
        "id": "x",
        "result": {},
    }


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
    assert set(TOOLS) == {f"protocolith_{n}" for n in ("freeze", "record", "deviation", "verify", "issue", "log", "show", "summary", "capture", "atlas", "schema", "claim_check", "anchor")}


def test_stdio_subprocess(tmp_path: Any) -> None:
    store = tmp_path / "s"
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "protocolith_freeze", "arguments": {"protocol": protocol()}},
        },
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


def test_filtered_log_show_and_summary_tools(recorded: Store) -> None:
    is_error, data = tool(recorded, "protocolith_log", {"type": "record", "tail": 1})
    assert not is_error and [e["seq"] for e in data["entries"]] == [1] and data["head"]["seq"] == 1
    assert tool(recorded, "protocolith_log", {"status": "BLOCKED_SOURCE"})[1]["entries"] == []
    assert tool(recorded, "protocolith_log", {"tail": 0})[1]["error"]["code"] == "BAD_ENTRY"
    is_error, shown = tool(recorded, "protocolith_show", {"seq": 1})
    assert not is_error and shown["protocol"]["protocol_id"] == "DEMO_D001"
    assert tool(recorded, "protocolith_show", {"seq": 9})[1]["error"]["code"] == "DANGLING_REF"
    is_error, summary = tool(recorded, "protocolith_summary")
    assert not is_error and summary["protocols"][0]["records"] == 1
    assert tool(recorded, "protocolith_summary", {"protocol": "NOPE"})[1]["error"]["code"] == "UNKNOWN_PROTOCOL"
    recorded.ledger_path.write_bytes(recorded.ledger_path.read_bytes() + b"x\n")
    is_error, broken = tool(recorded, "protocolith_summary")
    assert is_error and broken["ok"] is False and broken["problems"]


def test_capture_tool_stays_inside_the_working_directory(store: Store, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    work = tmp_path / "work"
    work.mkdir()
    (work / "data.txt").write_text("abc", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("x", encoding="utf-8")
    monkeypatch.chdir(work)
    is_error, data = tool(store, "protocolith_capture", {"files": ["data.txt"]})
    assert not is_error and data["inputs"] == [
        {"path": "data.txt", "sha256": hashlib.sha256(b"abc").hexdigest(), "size": 3}
    ]
    assert "environment" not in data and "environment" in tool(store, "protocolith_capture", {"env": True})[1]
    assert "environment" in tool(store, "protocolith_capture")[1]
    assert tool(store, "protocolith_capture", {"files": ["../secret.txt"]})[1]["error"]["code"] == "BAD_PATH"
    assert tool(store, "protocolith_capture", {"files": [1]})[1]["error"]["code"] == "BAD_ENTRY"
    assert tool(store, "protocolith_capture", {"files": "data.txt"})[1]["error"]["code"] == "BAD_ENTRY"


def test_schema_tool_and_resources(recorded: Store) -> None:
    assert tool(recorded, "protocolith_schema", {"name": "record"})[1]["title"] == "protocolith record"
    assert set(tool(recorded, "protocolith_schema")[1]) == {"freeze", "record", "deviation", "issue", "entry"}
    assert tool(recorded, "protocolith_schema", {"name": "x"})[1]["error"]["code"] == "BAD_ENTRY"
    listed = rpc(recorded, "resources/list")["result"]["resources"]
    uris = [r["uri"] for r in listed]
    assert uris[:2] == ["protocolith://summary", "protocolith://ledger"] and "protocolith://schema/entry" in uris
    for uri in uris:
        contents = rpc(recorded, "resources/read", {"uri": uri})["result"]["contents"]
        assert contents[0]["uri"] == uri and contents[0]["mimeType"] == "application/json"
        json.loads(contents[0]["text"])
    ledger = json.loads(rpc(recorded, "resources/read", {"uri": "protocolith://ledger"})["result"]["contents"][0]["text"])
    assert len(ledger["entries"]) == 2
    for bad in ("protocolith://nope", "protocolith://schema/nope", "http://x", None):
        assert rpc(recorded, "resources/read", {"uri": bad})["error"]["code"] == -32002


def test_resource_read_reports_a_missing_ledger(store: Store) -> None:
    error = rpc(store, "resources/read", {"uri": "protocolith://ledger"})["error"]
    assert error["code"] == -32000 and error["message"].startswith("NO_LEDGER")


def test_atlas_tool(recorded: Store, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    is_error, data = tool(recorded, "protocolith_atlas", {})
    assert not is_error and data["path"] == "protocolith-atlas.html" and data["cards"] == 1 and data["ok"] is True
    assert (tmp_path / "protocolith-atlas.html").is_file()
    (tmp_path / "cards").mkdir()
    (tmp_path / "cards" / "c.json").write_text(
        json.dumps({"evidence_id": "A", "result_status": "BLOCKED_SOURCE"}), encoding="utf-8"
    )
    (tmp_path / "i18n").mkdir()
    (tmp_path / "i18n" / "de.json").write_text('{"_name": "Deutsch"}', encoding="utf-8")
    args = {"cards": ["cards"], "out": "site/atlas.html", "title": "T", "i18n": "i18n", "default_lang": "de", "max_rows": 1}
    is_error, data = tool(recorded, "protocolith_atlas", args)
    assert not is_error and data["path"] == "site/atlas.html" and data["cards"] == 1 and data["warnings"] == []
    assert b'<html lang="de">' in (tmp_path / "site" / "atlas.html").read_bytes()


def test_atlas_tool_refuses_paths_outside_the_working_directory(
    recorded: Store, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    for bad in ({"out": "../x.html"}, {"cards": ["/etc"]}, {"i18n": "../x"}, {"cards": "cards"}, {"cards": [3]}, {"extra": 1}):
        is_error, data = tool(recorded, "protocolith_atlas", bad)
        assert is_error and data["ok"] is False
    assert not (tmp_path.parent / "x.html").exists()


def test_atlas_tool_reports_a_failing_ledger(recorded: Store, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    lines = recorded.ledger_path.read_text().splitlines()
    lines[1] = lines[1].replace("run-1", "run-X")
    recorded.ledger_path.write_text("\n".join(lines) + "\n")
    is_error, data = tool(recorded, "protocolith_atlas", {"out": "bad.html"})
    assert is_error and data["ok"] is False and (tmp_path / "bad.html").is_file()


def test_prompts_list_and_get(store: Store) -> None:
    listing = rpc(store, "prompts/list")["result"]["prompts"]
    assert [p["name"] for p in listing] == ["research-agent-protocol"] and listing[0]["arguments"] == []
    got = rpc(store, "prompts/get", {"name": "research-agent-protocol"})["result"]
    text = got["messages"][0]["content"]["text"]
    assert got["messages"][0]["role"] == "user" and got["description"] == listing[0]["description"]
    for needle in ("protocolith_freeze", "protocolith_record", "protocolith_claim_check", "may_say", "must_not_say", "protocolith_anchor", "BLOCKED_SOURCE"):
        assert needle in text
    assert text.index("Freeze before any run") < text.index("Record every run") < text.index("Check before you claim") < text.index("Anchor at the end")
    assert rpc(store, "prompts/get", {"name": "nope"})["error"]["code"] == -32602
    assert rpc(store, "prompts/get", {"name": 5})["error"]["code"] == -32602
    assert rpc(store, "prompts/get", {})["error"]["code"] == -32602


def test_claim_check_and_anchor_tools(store: Store) -> None:
    freeze(store, protocol(), clock=clock(NOW))
    tool(store, "protocolith_record", {"body": record_body()})
    is_error, found = tool(store, "protocolith_claim_check", {"seq": 1})
    assert not is_error and found["supported"] is True and found["anchored"] is False
    assert tool(store, "protocolith_claim_check", {"protocol": "DEMO_D001"})[1]["seq"] == 1
    assert tool(store, "protocolith_claim_check", {})[1]["error"]["code"] == "BAD_ENTRY"
    is_error, anchored = tool(store, "protocolith_anchor", {})
    assert not is_error and anchored["methods"] == [] and len(anchored["anchor_id"]) == 64
    assert tool(store, "protocolith_claim_check", {"seq": 1})[1]["anchored"] is True
    assert tool(store, "protocolith_anchor", {"git_tag": True})[1]["error"]["code"] == "BAD_ENTRY"
    assert tool(store, "protocolith_anchor", {"write_head": "x"})[1]["error"]["code"] == "BAD_ENTRY"
    assert tool(store, "protocolith_anchor", {"tsa": "ftp://x"})[1]["error"]["code"] == "BAD_URL"
    is_error, verdict = tool(store, "protocolith_verify", {"anchors": True})
    assert not is_error and verdict["anchors"] == 1
    assert "anchors" not in tool(store, "protocolith_verify", {})[1]
    store.ledger_path.write_bytes(store.ledger_path.read_bytes().splitlines(keepends=True)[0])
    is_error, verdict = tool(store, "protocolith_verify", {"anchors": True})
    assert is_error and verdict["codes"] == ["ANCHOR_AHEAD"]
    assert not tool(store, "protocolith_verify", {"anchors": False})[0]


def test_anchor_tool_uses_the_network_only_with_tsa(store: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    import urllib.error

    from protocolith.core import anchor as anchor_module

    seen: list[str] = []

    def refuse(request: Any, timeout: float) -> Any:
        seen.append(request.full_url)
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(anchor_module.urllib.request, "urlopen", refuse)
    freeze(store, protocol(), clock=clock(NOW))
    assert not tool(store, "protocolith_anchor", {})[0] and seen == []
    is_error, error = tool(store, "protocolith_anchor", {"tsa": "https://tsa.example/"})
    assert is_error and error["error"]["code"] == "ANCHOR_FAILED" and seen == ["https://tsa.example/"]
