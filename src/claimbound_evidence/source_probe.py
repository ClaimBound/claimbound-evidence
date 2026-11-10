# SPDX-License-Identifier: Apache-2.0
"""SourceProbe v1: a bounded, metadata-only probe of one public source URL.

The probe never writes the response body anywhere. It records only metadata,
marker checks and link hints. It does not make legal conclusions and never
emits a PASS status.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, UTC
from html.parser import HTMLParser
from typing import Any

USER_AGENT = "claimbound-source-probe"
DEFAULT_TIMEOUT = 15.0
DEFAULT_MAX_BYTES = 1_048_576
RECOMMENDATIONS = ("safe_to_continue", "needs_human_review", "blocked")
BLOCKING_STATUSES = frozenset({401, 403, 429})
CAPTCHA_MARKERS = (
    "captcha",
    "g-recaptcha",
    "hcaptcha",
    "cf-challenge",
    "are you a robot",
    "verify you are human",
)
TERMS_HINT = re.compile(
    r"licen[cs]e|terms|copyright|legal|conditions|creativecommons|reuse|policy",
    re.IGNORECASE,
)
REQUIRED_FIELDS = (
    "probe_version",
    "url",
    "final_url",
    "http_status",
    "content_type",
    "byte_size",
    "body_fully_read",
    "sha256",
    "expected_marker_checks",
    "license_or_terms_links",
    "robots_disallow_hint",
    "recommendation",
    "reasons",
    "no_legal_conclusion",
    "probed_at_utc",
)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            label = " ".join(self._text)
            if TERMS_HINT.search(self._href) or TERMS_HINT.search(label):
                self.links.append(self._href)
            self._href = None


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_capped(resp: Any, max_bytes: int) -> tuple[bytes, bool]:
    body = resp.read(max_bytes + 1)
    if len(body) > max_bytes:
        return body[:max_bytes], False
    return body, True


def _open(url: str, timeout: float) -> tuple[int, str, str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
    except urllib.error.HTTPError as exc:
        return exc.code, exc.geturl() or url, exc.headers.get("Content-Type", "") or "", exc
    return resp.status, resp.geturl() or url, resp.headers.get("Content-Type", "") or "", resp


def _robots_disallows(final_url: str, timeout: float) -> bool:
    parts = urllib.parse.urlsplit(final_url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        status, _, _, resp = _open(robots_url, timeout)
        try:
            if status != 200:
                return False
            body, _ = _read_capped(resp, 65_536)
        finally:
            resp.close()
    except (OSError, ValueError):
        return False
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.decode("utf-8", errors="replace").splitlines())
    return not parser.can_fetch(USER_AGENT, final_url)


def probe_url(
    url: str,
    markers: list[str] | tuple[str, ...] = (),
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    check_robots: bool = True,
) -> dict[str, Any]:
    """Probe one URL and return a metadata-only result dictionary."""
    scheme = urllib.parse.urlsplit(url).scheme
    if scheme not in ("http", "https"):
        raise ValueError("SourceProbe supports only http and https URLs")
    reasons: list[str] = []
    result: dict[str, Any] = {
        "probe_version": "1",
        "url": url,
        "final_url": url,
        "http_status": None,
        "content_type": "",
        "byte_size": 0,
        "body_fully_read": False,
        "sha256": None,
        "expected_marker_checks": [],
        "license_or_terms_links": [],
        "robots_disallow_hint": False,
        "recommendation": "needs_human_review",
        "reasons": reasons,
        "no_legal_conclusion": True,
        "probed_at_utc": _utc_now(),
    }
    try:
        status, final_url, ctype, resp = _open(url, timeout)
        try:
            body, complete = _read_capped(resp, max_bytes)
        finally:
            resp.close()
    except (OSError, ValueError) as exc:
        reasons.append(f"request_failed: {type(exc).__name__}")
        result["recommendation"] = "blocked"
        return result

    result.update(http_status=status, final_url=final_url, content_type=ctype)
    result["byte_size"] = len(body)
    result["body_fully_read"] = complete
    if complete:
        result["sha256"] = hashlib.sha256(body).hexdigest()
    else:
        reasons.append("body_exceeded_max_bytes_not_hashed")

    text = body.decode("utf-8", errors="replace")
    result["expected_marker_checks"] = [{"marker": m, "found": m in text} for m in markers]
    if "html" in ctype.lower() or not ctype:
        parser = _LinkParser()
        try:
            parser.feed(text)
        except Exception:  # noqa: BLE001 - hints only, never fail the probe
            pass
        links = {urllib.parse.urljoin(final_url, h) for h in parser.links if h}
        result["license_or_terms_links"] = sorted(links)[:20]

    if check_robots:
        result["robots_disallow_hint"] = _robots_disallows(final_url, timeout)

    lowered = text.lower()
    blocked = False
    if status in BLOCKING_STATUSES or status >= 500:
        blocked = True
        reasons.append(f"http_status_{status}")
    if any(marker in lowered for marker in CAPTCHA_MARKERS):
        blocked = True
        reasons.append("captcha_like_marker")
    if result["robots_disallow_hint"]:
        blocked = True
        reasons.append("robots_disallow_hint")

    if blocked:
        result["recommendation"] = "blocked"
    else:
        missing = [c["marker"] for c in result["expected_marker_checks"] if not c["found"]]
        if missing:
            reasons.append("expected_marker_missing")
        if status != 200:
            reasons.append(f"http_status_{status}")
        if not complete:
            reasons.append("incomplete_body")
        if missing or status != 200 or not complete:
            result["recommendation"] = "needs_human_review"
        else:
            result["recommendation"] = "safe_to_continue"
    return result


def validate_probe_artifact(data: Any) -> list[str]:
    """Return a list of violations for a SourceProbe JSON artifact."""
    if not isinstance(data, dict):
        return ["artifact must be a JSON object"]
    errors = [f"missing field: {f}" for f in REQUIRED_FIELDS if f not in data]
    if data.get("no_legal_conclusion") is not True:
        errors.append("no_legal_conclusion must be true")
    if data.get("recommendation") not in RECOMMENDATIONS:
        errors.append("recommendation must be one of " + "|".join(RECOMMENDATIONS))
    status_text = json.dumps(data)
    if "PASSED_UNDER_PROTOCOL" in status_text or '"PASS"' in status_text:
        errors.append("probe artifact must not carry a PASS status")
    if data.get("sha256") is not None and data.get("body_fully_read") is not True:
        errors.append("sha256 is only allowed when the body was fully read")
    if "body" in data or "raw_body" in data:
        errors.append("raw body must not be stored")
    if not isinstance(data.get("expected_marker_checks", []), list):
        errors.append("expected_marker_checks must be a list")
    return errors
