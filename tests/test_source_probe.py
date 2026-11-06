# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
import email.message
import io
import urllib.error
import urllib.request

import pytest

from claimbound_evidence.cli import main
from claimbound_evidence.source_probe import probe_url, validate_probe_artifact

PAGE = b'<html><body>Dataset Download <a href="/terms">Terms of use</a></body></html>'
ROUTES = {
    "/ok": (200, PAGE, "text/html"),
    "/big": (200, b"x" * 5000, "text/plain"),
    "/forbidden": (403, b"no", "text/plain"),
    "/error": (503, b"oops", "text/plain"),
    "/captcha": (200, b"<html>please solve the CAPTCHA</html>", "text/html"),
    "/private/x": (200, PAGE, "text/html"),
    "/robots.txt": (200, b"User-agent: *\nDisallow: /private/\n", "text/plain"),
}


class FakeResp:
    def __init__(self, url, status, body, ctype):
        self.status = status
        self._url = url
        self._body = body
        self.headers = {"Content-Type": ctype}

    def geturl(self):
        return self._url

    def read(self, n=-1):
        return self._body if n < 0 else self._body[:n]

    def close(self):
        pass


@pytest.fixture
def base(monkeypatch):
    root = "http://example.test"

    def fake_urlopen(req, timeout=None):
        assert req.get_header("User-agent") == "claimbound-source-probe"
        path = req.full_url[len(root) :]
        if path == "/redir":
            path = "/ok"
        if path == "/down":
            raise urllib.error.URLError("unreachable")
        status, body, ctype = ROUTES.get(path, (404, b"nf", "text/plain"))
        url = root + path
        if status >= 400:
            hdrs = email.message.Message()
            hdrs["Content-Type"] = ctype
            raise urllib.error.HTTPError(url, status, "err", hdrs, io.BytesIO(body))
        return FakeResp(url, status, body, ctype)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return root


def test_ok_with_markers_and_hash(base):
    r = probe_url(base + "/ok", ["Download", "download"])
    assert r["http_status"] == 200
    assert r["sha256"] == hashlib.sha256(PAGE).hexdigest()
    assert r["byte_size"] == len(PAGE)
    assert [c["found"] for c in r["expected_marker_checks"]] == [True, False]
    assert r["license_or_terms_links"] == [base + "/terms"]
    assert r["recommendation"] == "needs_human_review"
    assert r["no_legal_conclusion"] is True
    assert validate_probe_artifact(r) == []


def test_safe_when_all_markers_found(base):
    assert probe_url(base + "/ok", ["Download"])["recommendation"] == "safe_to_continue"


def test_redirect_final_url(base):
    assert probe_url(base + "/redir")["final_url"] == base + "/ok"


def test_cap_blocks_hash(base):
    r = probe_url(base + "/big", max_bytes=100)
    assert r["sha256"] is None and r["body_fully_read"] is False
    assert r["byte_size"] == 100
    assert r["recommendation"] == "needs_human_review"


@pytest.mark.parametrize("path", ["/forbidden", "/error", "/captcha", "/private/x"])
def test_blocked(base, path):
    assert probe_url(base + path)["recommendation"] == "blocked"


def test_robots_hint_flag(base):
    assert probe_url(base + "/private/x")["robots_disallow_hint"] is True
    assert probe_url(base + "/ok")["robots_disallow_hint"] is False


def test_unreachable_is_blocked(base):
    r = probe_url(base + "/down", timeout=2)
    assert r["recommendation"] == "blocked" and r["http_status"] is None


def test_rejects_non_http():
    with pytest.raises(ValueError):
        probe_url("file:///etc/passwd")


def test_validator_rejects_bad_artifacts(base):
    r = probe_url(base + "/ok")
    errs = validate_probe_artifact(dict(r, no_legal_conclusion=False, recommendation="PASS"))
    assert any("no_legal_conclusion" in e for e in errs)
    assert any("recommendation" in e for e in errs)
    assert validate_probe_artifact(dict(r, sha256="ab", body_fully_read=False))
    assert validate_probe_artifact([])


def test_cli_writes_json_without_body(base, tmp_path, capsys):
    out = tmp_path / "p.json"
    assert main(["probe", base + "/ok", "--marker", "Download", "--out", str(out)]) == 0
    capsys.readouterr()
    data = json.loads(out.read_text())
    assert validate_probe_artifact(data) == []
    assert "<html>" not in out.read_text()
    assert main(["probe", base + "/ok", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["no_legal_conclusion"] is True
