#!/usr/bin/env python3
"""Fetch an already-frozen claim source manifest without source substitution."""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def html_text(payload: bytes) -> str:
    parser = TextExtractor()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return "\n".join(
        line for line in (re.sub(r"\s+", " ", html.unescape(x)).strip() for x in parser.parts) if line
    )


def extract_text(payload_path: Path, content_type: str) -> str:
    if "pdf" in content_type.casefold() or payload_path.read_bytes().startswith(b"%PDF"):
        if shutil.which("pdftotext") is not None:
            completed = subprocess.run(
                ["pdftotext", "-layout", str(payload_path), "-"],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode == 0:
                return completed.stdout
        try:
            from pypdf import PdfReader

            return "\n".join(page.extract_text() or "" for page in PdfReader(payload_path).pages)
        except (ImportError, OSError, ValueError):
            return ""
    return html_text(payload_path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    raw_root = args.output_root / "raw"
    meta_root = args.output_root / "meta"
    text_root = args.output_root / "text"
    for path in (raw_root, meta_root, text_root):
        path.mkdir(parents=True, exist_ok=True)

    context = ssl.create_default_context()
    for source in manifest["sources"]:
        key, url = source["key"], source["source_url"]
        raw_path = raw_root / f"{key}.bin"
        meta_path = meta_root / f"{key}.json"
        text_path = text_root / f"{key}.txt"
        if raw_path.exists() and meta_path.exists() and text_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            if not text_path.stat().st_size and raw_path.read_bytes().startswith(b"%PDF"):
                text_path.write_text(
                    extract_text(raw_path, metadata.get("content_type", "")),
                    encoding="utf-8",
                )
            print(
                f"{key}: cached HTTP {metadata['http_status']} "
                f"bytes={metadata['byte_count']} final={metadata['final_url']}"
            )
            continue
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ClaimBoundEvidence/1.0 (+https://github.com/ClaimBound/claimbound-evidence)"},
        )
        status = 0
        final_url = url
        content_type = ""
        error = None
        payload = b""
        try:
            with urllib.request.urlopen(request, timeout=45, context=context) as response:
                status = response.status
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
                payload = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            final_url = exc.geturl()
            content_type = exc.headers.get("Content-Type", "")
            payload = exc.read()
            error = f"HTTPError: {exc}"
        except Exception as exc:  # access failures are evidence outcomes, not fetcher failures
            error = f"{type(exc).__name__}: {exc}"

        raw_path.write_bytes(payload)
        text = extract_text(raw_path, content_type) if payload else ""
        text_path.write_text(text, encoding="utf-8")
        metadata = {
            "key": key,
            "source_url": url,
            "final_url": final_url,
            "http_status": status,
            "content_type": content_type,
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "error": error,
        }
        meta_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"{key}: HTTP {status} bytes={len(payload)} final={final_url}")


if __name__ == "__main__":
    main()
