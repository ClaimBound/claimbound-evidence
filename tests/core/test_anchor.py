# SPDX-License-Identifier: Apache-2.0
"""Anchoring and anchor verification. No network and no git: openers and runners are fakes."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import subprocess
import urllib.error
from pathlib import Path
from typing import Any

import pytest
from core_support import NOW, clock, protocol, record_body

from protocolith.core import EnvError, InputError, Store, VerificationFailed, anchor_head, freeze, record, sha256_hex, verify, verify_anchors
from protocolith.core import anchor as anchor_module
from protocolith.core.anchor import (
    build_statement,
    build_timestamp_request,
    check_anchors,
    parse_timestamp_response,
)
from protocolith.core.canonical import encode

TLV = anchor_module._tlv
ALG = bytes.fromhex("300d06096086480165030402010500")
GEN = b"20261118101500Z"


def int_(value: int) -> bytes:
    return TLV(0x02, value.to_bytes(value.bit_length() // 8 + 1, "big"))


def tsr(digest: bytes, *, status: int = 0, gen: bytes = GEN, token: bool = True, imprint: bytes | None = None) -> bytes:
    """A TimeStampResp shaped like a real one (signature and certificates left out)."""
    info = TLV(
        0x30,
        int_(1) + TLV(0x06, b"\x2a\x03\x04") + TLV(0x30, ALG + TLV(0x04, imprint or digest)) + int_(7) + TLV(0x18, gen),
    )
    encap = TLV(0x30, TLV(0x06, b"\x2a\x03\x05") + TLV(0xA0, TLV(0x04, info)))
    signed = TLV(0x30, int_(3) + TLV(0x31, b"") + encap + TLV(0xA0, b"\x00" * 400))  # certificates make it long
    content = TLV(0x30, TLV(0x06, b"\x2a\x03\x06") + TLV(0xA0, signed))
    return TLV(0x30, TLV(0x30, int_(status)) + (content if token else b""))


class Response:
    def __init__(self, body: bytes = b"", headers: dict[str, str] | None = None) -> None:
        self.body = body
        self.headers = headers or {}
        self.reads: list[int] = []

    def __enter__(self) -> Response:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self, size: int) -> bytes:
        self.reads.append(size)
        return self.body[:size]


class Opener:
    """Records requests; ``answer`` builds the response from the request."""

    def __init__(self, answer: Any) -> None:
        self.answer = answer
        self.requests: list[Any] = []

    def __call__(self, request: Any, timeout: float) -> Any:
        self.requests.append((request, timeout))
        result = self.answer(request)
        if isinstance(result, BaseException):
            raise result
        return result


def digest_of(request: Any) -> bytes:
    """The SHA-256 imprint inside a TimeStampReq."""
    top = anchor_module._children(anchor_module._read_tlv(request.data, 0)[1])
    return anchor_module._children(top[1][1])[1][1]


def tsa(**changes: Any) -> Opener:
    return Opener(lambda request: Response(tsr(digest_of(request), **changes)))


class Runner:
    def __init__(self, *codes: int, stderr: str | None = "", error: BaseException | None = None) -> None:
        self.codes = list(codes) or [0, 0]
        self.stderr = stderr
        self.error = error
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append((argv, kwargs))
        if self.error is not None:
            raise self.error
        code = self.codes[len(self.calls) - 1]
        return subprocess.CompletedProcess(argv, code, "", self.stderr)  # type: ignore[arg-type]


def anchor_files(store: Store) -> list[str]:
    return sorted(path.name for path in store.anchors_dir.iterdir())


# --- DER -----------------------------------------------------------------------------------------------------------


def test_time_stamp_request_is_the_expected_der() -> None:
    digest = bytes(range(32))
    expected = bytes.fromhex("303c" "020101" "3031" "300d06096086480165030402010500" "0420") + digest
    expected += bytes.fromhex("020105" "0101ff")
    assert build_timestamp_request(digest, 5) == expected


def test_der_integers_stay_positive_and_lengths_use_long_form() -> None:
    assert anchor_module._der_int(0) == b"\x02\x01\x00"
    assert anchor_module._der_int(127) == b"\x02\x01\x7f"
    assert anchor_module._der_int(128) == b"\x02\x02\x00\x80"
    assert anchor_module._der_int(2**63) == b"\x02\x09\x00\x80" + bytes(7)
    assert TLV(0x04, b"a" * 127)[:2] == b"\x04\x7f"
    assert TLV(0x04, b"a" * 128)[:3] == b"\x04\x81\x80"
    assert TLV(0x04, b"a" * 300)[:4] == b"\x04\x82\x01\x2c"


def test_parse_reads_status_and_gen_time_and_ignores_the_signature() -> None:
    digest = hashlib.sha256(b"x").digest()
    assert parse_timestamp_response(tsr(digest), digest) == "2026-11-18T10:15:00Z"
    assert parse_timestamp_response(tsr(digest, status=1, gen=b"20261118101500.25Z"), digest) == "2026-11-18T10:15:00Z"


@pytest.mark.parametrize(
    ("data", "why"),
    [
        (b"", "truncated"),
        (b"\x30", "truncated"),
        (b"\x31\x00", "expected tag"),
        (b"\x30\x80", "unsupported length"),
        (b"\x30\x85\x00\x00\x00\x00\x01\x00", "unsupported length"),
        (b"\x30\x82\x01", "unsupported length"),
        (b"\x30\x05\x00", "runs past the end"),
        (b"\x30\x00", "list index"),
        (b"\x30\x03\x02\x01\x00", "expected tag"),
        (b"\x30\x05\x30\x03\x30\x01\x00", "expected tag"),
        (tsr(b"d" * 32, token=False), "list index"),
    ],
)
def test_parse_rejects_malformed_responses(data: bytes, why: str) -> None:
    with pytest.raises(EnvError) as info:
        parse_timestamp_response(data, b"d" * 32)
    assert info.value.code == "ANCHOR_FAILED" and "malformed" in info.value.message and why in info.value.message


def test_parse_rejects_refusal_wrong_imprint_and_bad_time() -> None:
    digest = b"d" * 32
    with pytest.raises(EnvError, match="PKIStatus 2"):
        parse_timestamp_response(tsr(digest, status=2), digest)
    with pytest.raises(EnvError, match="different data"):
        parse_timestamp_response(tsr(digest, imprint=b"e" * 32), digest)
    for bad in (b"2026-11-18", b"20261118101500", b"\xff"):
        with pytest.raises(EnvError, match="GeneralizedTime"):
            parse_timestamp_response(tsr(digest, gen=bad), digest)


# --- the local anchor ----------------------------------------------------------------------------------------------


def test_local_anchor_files_and_idempotence(recorded: Store) -> None:
    first = anchor_head(recorded, clock=clock("2026-11-18T10:00:00Z"))
    statement = first["statement"]
    assert statement == build_statement(1, recorded_head(recorded), 2, "2026-11-18T10:00:00Z", statement["protocolith_version"])
    assert statement["kind"] == "protocolith-anchor" and statement["v"] == 1
    assert first["anchor_id"] == sha256_hex(statement) and first["methods"] == [] and first["added"] == []
    name = f"1-{statement['head_hash'][:12]}"
    assert anchor_files(recorded) == [f"{name}.json", f"{name}.statement"]
    assert (recorded.anchors_dir / f"{name}.statement").read_bytes() == encode(statement)
    assert hashlib.sha256((recorded.anchors_dir / f"{name}.statement").read_bytes()).hexdigest() == first["anchor_id"]
    again = anchor_head(recorded, clock=clock("2027-01-01T00:00:00Z"))
    assert again["anchor_id"] == first["anchor_id"] and again["statement"]["created_at"] == "2026-11-18T10:00:00Z"
    assert verify(recorded, anchors=True).ok and verify_anchors(recorded).count == 1
    assert not list(recorded.anchors_dir.glob("*.tmp"))


def recorded_head(store: Store) -> str:
    return json.loads(store.ledger_path.read_text().splitlines()[-1])["hash"]


def test_anchor_accepts_a_path_and_rejects_bad_ledgers(tmp_path: Path, recorded: Store) -> None:
    assert anchor_head(str(recorded.path), clock=clock())["methods"] == []
    with pytest.raises(EnvError) as missing:
        anchor_head(tmp_path / "none")
    assert missing.value.code == "NO_LEDGER"
    empty = Store(tmp_path / "empty")
    empty.path.mkdir()
    empty.ledger_path.write_bytes(b"")
    with pytest.raises(InputError) as nothing:
        anchor_head(empty)
    assert nothing.value.code == "EMPTY_LEDGER"
    recorded.ledger_path.write_bytes(recorded.ledger_path.read_bytes().replace(b"run-1", b"run-9"))
    with pytest.raises(VerificationFailed):
        anchor_head(recorded)


def test_write_head_writes_the_statement_bytes(recorded: Store, tmp_path: Path) -> None:
    target = tmp_path / "out dir é"
    target.mkdir()
    result = anchor_head(recorded, write_head=target / "head.txt", clock=clock())
    assert (target / "head.txt").read_bytes() == encode(result["statement"])
    assert result["head_file"] == str(target / "head.txt")
    (target / "head.txt").write_bytes(b"old")
    anchor_head(recorded, write_head=str(target / "head.txt"))
    assert (target / "head.txt").read_bytes() == encode(result["statement"])
    with pytest.raises(EnvError) as info:
        anchor_head(recorded, write_head=target / "missing" / "head.txt")
    assert info.value.code == "IO_ERROR"


def test_a_failed_rename_removes_the_temporary_file(recorded: Store, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(*args: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(anchor_module.os, "replace", broken)
    with pytest.raises(EnvError) as info:
        anchor_head(recorded, write_head=tmp_path / "head.txt")
    assert info.value.code == "IO_ERROR"
    assert list(tmp_path.glob("head.txt*")) == [] and not list(recorded.anchors_dir.glob("*.tmp"))


@pytest.mark.parametrize("value", ["", "ftp://x/y", "https://", "no-scheme.example/x", "file:///etc/passwd"])
def test_urls_must_be_http(recorded: Store, value: str) -> None:
    for option in ("tsa", "wayback"):
        with pytest.raises(InputError) as info:
            anchor_head(recorded, **{option: value})
        assert info.value.code == "BAD_URL"
    with pytest.raises(InputError) as info:
        anchor_head(recorded, tsa=5)  # type: ignore[arg-type]
    assert info.value.code == "BAD_URL" and not recorded.anchors_dir.exists()


def test_sign_needs_git_tag(recorded: Store) -> None:
    with pytest.raises(InputError) as info:
        anchor_head(recorded, sign=True)
    assert info.value.code == "BAD_ENTRY"


# --- RFC 3161 ------------------------------------------------------------------------------------------------------


def test_rfc3161_request_response_and_files(recorded: Store) -> None:
    opener = tsa()
    result = anchor_head(recorded, tsa="https://tsa.example/ts", clock=clock(), opener=opener, random_bytes=lambda n: b"\x00" * (n - 1) + b"\x05")
    request, timeout = opener.requests[0]
    assert request.full_url == "https://tsa.example/ts" and request.get_method() == "POST" and timeout == 30.0
    headers = {key.lower(): value for key, value in request.header_items()}
    assert headers["content-type"] == "application/timestamp-query" and headers["user-agent"].startswith("protocolith/")
    statement = encode(result["statement"])
    assert request.data == build_timestamp_request(hashlib.sha256(statement).digest(), 5)
    method = result["added"][0]
    reply = tsr(hashlib.sha256(statement).digest())
    assert method == {
        "file": f"{result['anchor_id']}.tsr",
        "gen_time": "2026-11-18T10:15:00Z",
        "tsr_sha256": hashlib.sha256(reply).hexdigest(),
        "type": "rfc3161",
        "url": "https://tsa.example/ts",
    }
    assert (recorded.anchors_dir / method["file"]).read_bytes() == reply
    assert result["methods"] == [method]
    assert "did not verify" in result["notes"][0] and "openssl ts -verify" in result["notes"][0]
    assert f"{result['anchor_id']}.tsr" in result["notes"][0] and ".statement" in result["notes"][0]
    assert verify(recorded, anchors=True).ok


def test_default_opener_and_nonce_are_used_when_not_injected(recorded: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    opener = tsa()
    monkeypatch.setattr(anchor_module.urllib.request, "urlopen", opener)
    anchor_head(recorded, tsa="http://tsa.example/", clock=clock())
    assert len(opener.requests) == 1
    nonce = anchor_module._children(anchor_module._read_tlv(opener.requests[0][0].data, 0)[1])[2][1]
    assert 1 <= len(nonce) <= 9


def test_a_second_authority_never_replaces_the_first_response(recorded: Store) -> None:
    first = anchor_head(recorded, tsa="https://a.example/", clock=clock(), opener=tsa())
    second = anchor_head(recorded, tsa="https://b.example/", opener=tsa(gen=b"20261118101501Z"))
    assert [m["file"] for m in second["methods"]][0] == f"{first['anchor_id']}.tsr"
    assert second["methods"][1]["file"] != second["methods"][0]["file"] and second["methods"][1]["file"].endswith(".tsr")
    again = anchor_head(recorded, tsa="https://b.example/", opener=tsa(gen=b"20261118101501Z"))
    assert len(again["methods"]) == 2 and verify(recorded, anchors=True).ok


def test_tsa_failures_keep_the_local_anchor(recorded: Store) -> None:
    cases = [
        (Opener(lambda r: urllib.error.URLError("down")), "URLError"),
        (Opener(lambda r: http.client.IncompleteRead(b"")), "IncompleteRead"),
        (Opener(lambda r: Response(b"x" * (anchor_module.MAX_RESPONSE + 1))), "larger than"),
        (Opener(lambda r: Response(b"junk")), "malformed"),
        (tsa(status=2), "refused"),
    ]
    for opener, text in cases:
        with pytest.raises(EnvError) as info:
            anchor_head(recorded, tsa="https://tsa.example/", clock=clock(), opener=opener)
        assert info.value.code == "ANCHOR_FAILED" and text in info.value.message
    assert len(list(recorded.anchors_dir.glob("*.json"))) == 1 and not list(recorded.anchors_dir.glob("*.tsr"))
    assert verify(recorded, anchors=True).ok


# --- Wayback -------------------------------------------------------------------------------------------------------


def test_wayback_records_the_snapshot_without_reading_the_body(recorded: Store) -> None:
    response = Response(b"page", {"Content-Location": "/web/20261118101500/https://example.org/head.txt"})
    opener = Opener(lambda request: response)
    result = anchor_head(recorded, wayback="https://example.org/head.txt", clock=clock(), opener=opener)
    request, timeout = opener.requests[0]
    assert request.full_url == "https://web.archive.org/save/https://example.org/head.txt" and request.get_method() == "GET"
    assert result["added"] == [
        {
            "snapshot": "https://web.archive.org/web/20261118101500/https://example.org/head.txt",
            "type": "wayback",
            "url": "https://example.org/head.txt",
        }
    ]
    assert response.reads == [] and "serving exactly the statement" not in result["notes"][0]
    assert result["anchor_id"] in result["notes"][0]
    assert verify(recorded, anchors=True).ok


def test_wayback_falls_back_to_location_and_checks_the_host(recorded: Store) -> None:
    ok = Opener(lambda r: Response(b"", {"Location": "https://web.archive.org/web/2026/https://example.org/h"}))
    assert anchor_head(recorded, wayback="https://example.org/h", clock=clock(), opener=ok)["added"][0]["snapshot"].startswith("https://web.archive.org/")
    for headers, text in (({}, "without a snapshot"), ({"Location": "https://evil.example/x"}, "not on the archive host")):
        with pytest.raises(EnvError) as info:
            anchor_head(recorded, wayback="https://example.org/h2", opener=Opener(lambda r, h=headers: Response(b"", h)))
        assert info.value.code == "ANCHOR_FAILED" and text in info.value.message
    with pytest.raises(EnvError):
        anchor_head(recorded, wayback="https://example.org/h3", opener=Opener(lambda r: OSError("reset")))


# --- git -----------------------------------------------------------------------------------------------------------


def test_git_tag_is_a_fixed_argv_and_never_pushes(recorded: Store) -> None:
    runner = Runner()
    result = anchor_head(recorded, git_tag=True, clock=clock(), runner=runner)
    name = f"anchor/1-{result['statement']['head_hash'][:12]}"
    assert runner.calls[0][0] == ["git", "rev-parse", "--is-inside-work-tree"]
    assert runner.calls[1][0] == ["git", "tag", "-a", name, "-m", encode(result["statement"]).decode()]
    assert all(call[1]["check"] is False and call[1]["timeout"] == 60 for call in runner.calls)
    assert all("push" not in call[0] for call in runner.calls)
    assert result["added"] == [{"signed": False, "tag": name, "type": "git-tag"}]
    assert result["notes"] == [f"the tag is local; publish it with: git push origin {name}"]
    signed = Runner()
    anchor_head(recorded, git_tag=True, sign=True, runner=signed)
    assert signed.calls[1][0][:3] == ["git", "tag", "-s"]
    assert verify(recorded, anchors=True).ok


def test_git_failures(recorded: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(InputError) as info:
        anchor_head(recorded, git_tag=True, runner=Runner(128))
    assert info.value.code == "NOT_A_GIT_REPO"
    with pytest.raises(EnvError, match="already exists") as failed:
        anchor_head(recorded, git_tag=True, runner=Runner(0, 1, stderr="  fatal: tag already exists\n"))
    assert failed.value.code == "ANCHOR_FAILED"
    with pytest.raises(EnvError, match="git tag failed: $"):
        anchor_head(recorded, git_tag=True, runner=Runner(0, 1, stderr=None))
    for error in (FileNotFoundError("git"), subprocess.TimeoutExpired("git", 60)):
        with pytest.raises(EnvError, match="could not be run"):
            anchor_head(recorded, git_tag=True, runner=Runner(error=error))
    real = Runner()
    monkeypatch.setattr(anchor_module.subprocess, "run", real)
    anchor_head(recorded, git_tag=True)
    assert len(real.calls) == 2


def test_methods_done_before_a_failure_are_kept(recorded: Store) -> None:
    with pytest.raises(EnvError):
        anchor_head(recorded, tsa="https://tsa.example/", git_tag=True, clock=clock(), opener=tsa(), runner=Runner(0, 1))
    methods = json.loads(next(recorded.anchors_dir.glob("*.json")).read_text())["methods"]
    assert [m["type"] for m in methods] == ["rfc3161"] and verify(recorded, anchors=True).ok


def test_all_methods_in_one_run(recorded: Store) -> None:
    opener = Opener(lambda r: Response(tsr(digest_of(r))) if r.data else Response(b"", {"Content-Location": "/web/1/https://e.org/h"}))
    result = anchor_head(recorded, tsa="https://t.example/", wayback="https://e.org/h", git_tag=True, clock=clock(), opener=opener, runner=Runner())
    assert [m["type"] for m in result["methods"]] == ["rfc3161", "wayback", "git-tag"] and len(result["notes"]) == 3


# --- existing files ------------------------------------------------------------------------------------------------


def test_an_anchor_of_another_head_or_a_changed_statement_file_is_refused(recorded: Store) -> None:
    done = anchor_head(recorded, clock=clock())
    name = Path(done["path"]).stem
    (recorded.anchors_dir / f"{name}.statement").write_bytes(b"{}")
    with pytest.raises(InputError) as changed:
        anchor_head(recorded)
    assert changed.value.code == "ANCHOR_EXISTS"
    (recorded.anchors_dir / f"{name}.statement").write_bytes(encode(done["statement"]))
    doc = json.loads(Path(done["path"]).read_text())
    doc["statement"]["head_hash"] = "f" * 64
    Path(done["path"]).write_bytes(encode(doc))
    with pytest.raises(InputError) as other:
        anchor_head(recorded)
    assert other.value.code == "ANCHOR_EXISTS"
    Path(done["path"]).write_bytes(b"not json")
    with pytest.raises(InputError) as broken:
        anchor_head(recorded)
    assert broken.value.code == "ANCHOR_EXISTS"


def test_a_missing_statement_file_is_recreated_after_an_interrupted_run(recorded: Store) -> None:
    done = anchor_head(recorded, clock=clock())
    statement_file = recorded.anchors_dir / f"{Path(done['path']).stem}.statement"
    statement_file.unlink()
    assert anchor_head(recorded, clock=clock("2030-01-01T00:00:00Z"))["anchor_id"] == done["anchor_id"]
    assert statement_file.read_bytes() == encode(done["statement"])


def test_an_anchor_file_damaged_during_the_run_is_reported(recorded: Store) -> None:
    def answer(request: Any) -> Response:
        for path in recorded.anchors_dir.glob("*.json"):
            path.write_bytes(b"[]")
        return Response(b"", {"Content-Location": "/web/1/https://e.org/h"})

    with pytest.raises(InputError) as info:
        anchor_head(recorded, wayback="https://e.org/h", clock=clock(), opener=Opener(answer))
    assert info.value.code == "ANCHOR_INVALID"


# --- verification --------------------------------------------------------------------------------------------------


def edit_anchor(path: str, change: Any) -> None:
    doc = json.loads(Path(path).read_text())
    change(doc)
    Path(path).write_bytes(encode(doc))


def codes(store: Store) -> list[str]:
    return sorted({v.code for v in verify_anchors(store).violations})


def test_clean_store_without_anchors_reports_zero(recorded: Store) -> None:
    report = verify_anchors(recorded)
    assert report.ok and report.count == 0 and report.last_seq is None
    assert report.to_dict() == {"anchors": 0, "last_anchored_seq": None, "ok": True, "violations": []}
    verdict = verify(recorded, anchors=True)
    assert verdict.ok and verdict.anchors == 0 and verdict.to_dict()["anchors"] == 0
    assert "anchors" not in verify(recorded).to_dict()


def test_statement_edits_and_inconsistent_entries_are_invalid(recorded: Store) -> None:
    done = anchor_head(recorded, clock=clock())
    edit_anchor(done["path"], lambda d: d["statement"].update(created_at="2020-01-01T00:00:00Z"))
    assert codes(recorded) == ["ANCHOR_INVALID"]
    Path(done["path"]).write_bytes(encode({"anchor_id": done["anchor_id"], "methods": [], "statement": done["statement"]}))

    def bump(doc: dict[str, Any]) -> None:
        doc["statement"]["entries"] = 9
        doc["anchor_id"] = sha256_hex(doc["statement"])

    edit_anchor(done["path"], bump)
    assert "entries does not equal" in verify_anchors(recorded).violations[0].message


@pytest.mark.parametrize(
    "content",
    [
        b"not json",
        b"[]",
        b'{"anchor_id":"x"}',
        b"{}",
    ],
)
def test_malformed_anchor_files_are_invalid(recorded: Store, content: bytes) -> None:
    recorded.anchors_dir.mkdir()
    (recorded.anchors_dir / "0-aaaaaaaaaaaa.json").write_bytes(content)
    report = verify_anchors(recorded)
    assert not report.ok and report.count == 1 and report.last_seq is None
    assert [v.code for v in report.violations] == ["ANCHOR_INVALID"]
    assert not verify(recorded, anchors=True).ok and verify(recorded).ok


def test_each_malformation_is_named(recorded: Store) -> None:
    done = anchor_head(recorded, clock=clock())
    good = json.loads(Path(done["path"]).read_text())
    variants: dict[str, Any] = {
        "statement": lambda d: d.update(statement=[]),
        "statement_keys": lambda d: d["statement"].update(extra=1),
        "version": lambda d: d["statement"].update(v=2),
        "kind": lambda d: d["statement"].update(kind="other"),
        "seq": lambda d: d["statement"].update(head_seq=True),
        "hash": lambda d: d["statement"].update(head_hash="Z" * 64),
        "entries": lambda d: d["statement"].update(entries=-1),
        "pversion": lambda d: d["statement"].update(protocolith_version=1),
        "created": lambda d: d["statement"].update(created_at="yesterday"),
        "anchor_id": lambda d: d.update(anchor_id="nope"),
        "methods": lambda d: d.update(methods={}),
        "method_item": lambda d: d.update(methods=[1]),
        "method_type": lambda d: d.update(methods=[{"type": 1}]),
        "tsr_missing_file": lambda d: d.update(methods=[{"type": "rfc3161", "tsr_sha256": "a" * 64}]),
        "tsr_empty_file": lambda d: d.update(methods=[{"type": "rfc3161", "file": "", "tsr_sha256": "a" * 64}]),
        "tsr_path": lambda d: d.update(methods=[{"type": "rfc3161", "file": "../x.tsr", "tsr_sha256": "a" * 64}]),
        "tsr_backslash": lambda d: d.update(methods=[{"type": "rfc3161", "file": "a\\b.tsr", "tsr_sha256": "a" * 64}]),
        "tsr_hash": lambda d: d.update(methods=[{"type": "rfc3161", "file": "a.tsr", "tsr_sha256": "x"}]),
    }
    for name, change in variants.items():
        doc = json.loads(json.dumps(good))
        change(doc)
        Path(done["path"]).write_bytes(encode(doc))
        report = verify_anchors(recorded)
        assert [v.code for v in report.violations] == ["ANCHOR_INVALID"], name
    Path(done["path"]).write_bytes(encode(good))
    assert verify_anchors(recorded).ok


def test_unreadable_anchor_file(recorded: Store) -> None:
    recorded.anchors_dir.mkdir()
    (recorded.anchors_dir / "0-aaaaaaaaaaaa.json").mkdir()
    violation = verify_anchors(recorded).violations[0]
    assert violation.code == "ANCHOR_INVALID" and "cannot be read" in violation.message


def test_time_stamp_response_tampering_and_loss(recorded: Store) -> None:
    done = anchor_head(recorded, tsa="https://t.example/", clock=clock(), opener=tsa())
    target = recorded.anchors_dir / done["methods"][0]["file"]
    target.write_bytes(target.read_bytes() + b"\x00")
    assert "does not match" in verify_anchors(recorded).violations[0].message
    target.unlink()
    assert "cannot be read" in verify_anchors(recorded).violations[0].message
    assert codes(recorded) == ["ANCHOR_INVALID"] and not verify(recorded, anchors=True).ok


def test_crlf_converted_anchor_files_still_verify(recorded: Store) -> None:
    done = anchor_head(recorded, clock=clock())
    path = Path(done["path"])
    path.write_bytes(path.read_bytes().replace(b",", b",\r\n").replace(b"{", b"{\r\n"))
    assert b"\r\n" in path.read_bytes() and verify(recorded, anchors=True).ok


def test_check_anchors_on_a_missing_directory(recorded: Store, tmp_path: Path) -> None:
    from protocolith.core import scan

    verdict, verifier = scan(recorded.ledger_path.read_bytes())
    assert check_anchors(tmp_path / "nowhere", verifier, verdict.count).count == 0


def test_summary_shows_anchors_and_their_problems(recorded: Store) -> None:
    from protocolith.core import summary

    assert summary(recorded)["anchors"] == {"count": 0, "last_seq": None}
    anchor_head(recorded, clock=clock())
    record(recorded, record_body(run_id="run-2"), clock=clock(NOW))
    found = summary(recorded)
    assert found["anchors"] == {"count": 1, "last_seq": 1} and found["ok"] and found["problems"] == []
    ledger = recorded.ledger_path
    ledger.write_bytes(b"".join(ledger.read_bytes().splitlines(keepends=True)[:1]))
    broken = summary(recorded)
    assert not broken["ok"] and broken["problems"][0]["code"] == "ANCHOR_AHEAD" and broken["anchors"]["last_seq"] is None


def test_store_path_with_spaces_and_unicode(tmp_path: Path) -> None:
    store = Store(tmp_path / "my study é" / ".protocolith")
    freeze(store, protocol(), clock=clock(NOW))
    record(store, record_body(), clock=clock(NOW))
    assert anchor_head(store, clock=clock())["methods"] == [] and verify(store, anchors=True).ok
    assert os.path.isdir(store.anchors_dir)
