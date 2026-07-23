#!/usr/bin/env python3
"""Retry transport-blocked frozen URLs with curl without substituting sources."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from fetch_frozen_claim_sources import BLOCKED_RETRY_STATUSES, extract_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())

    for source in manifest["sources"]:
        key, url = source["key"], source["source_url"]
        raw_path = args.output_root / "raw" / f"{key}.bin"
        meta_path = args.output_root / "meta" / f"{key}.json"
        text_path = args.output_root / "text" / f"{key}.txt"
        metadata = json.loads(meta_path.read_text())
        if metadata["http_status"] not in BLOCKED_RETRY_STATUSES:
            continue
        attempts = list(metadata.get("attempts", []))
        if not attempts:
            attempts.append(
                {
                    "profile": "original-cached",
                    "http_status": metadata["http_status"],
                    "final_url": metadata["final_url"],
                    "byte_count": metadata["byte_count"],
                    "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                    "error": metadata.get("error"),
                }
            )
        with tempfile.NamedTemporaryFile(prefix="claimbound-retry-", suffix=".bin") as target:
            completed = subprocess.run(
                [
                    "curl", "-L", "--compressed", "--max-time", "45", "-sS",
                    "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
                    "-H", "Accept: text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
                    "-H", "Accept-Language: en-US,en;q=0.9",
                    "-o", target.name,
                    "-w", "%{http_code}\n%{url_effective}\n%{content_type}",
                    url,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            parts = completed.stdout.splitlines()
            status = int(parts[0]) if parts and parts[0].isdigit() else 0
            final_url = parts[1] if len(parts) > 1 else url
            content_type = parts[2] if len(parts) > 2 else ""
            payload = Path(target.name).read_bytes()
        attempt = {
            "profile": "curl-browser-compatible",
            "http_status": status,
            "final_url": final_url,
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "error": completed.stderr.strip() or None,
        }
        attempts.append(attempt)
        if status == 200:
            raw_path.write_bytes(payload)
            text_path.write_text(extract_text(raw_path, content_type))
            metadata.update(
                {
                    "final_url": final_url,
                    "http_status": status,
                    "content_type": content_type,
                    "byte_count": len(payload),
                    "sha256": attempt["sha256"],
                    "error": None,
                    "selected_transport_profile": attempt["profile"],
                }
            )
        metadata["attempts"] = attempts
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
        print(f"{key}: curl HTTP {status} bytes={len(payload)} final={final_url}")


if __name__ == "__main__":
    main()
