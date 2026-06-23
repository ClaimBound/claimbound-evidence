#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run Headroom proxy/Codex boundary evidence gates and write ClaimBound cards."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
HEADROOM_VERSION = "0.27.0"
HEADROOM_TAG = "v0.27.0"
HEADROOM_TAG_COMMIT = "95b2333ee5a3f1cbe512ca04a6563c3572835758"
PROTOCOL_ID = "HEADROOM_PROXY_CODEX_D003"
PROTOCOL_VERSION = "frozen-2026-06-23"
SOURCE_NAME = "Headroom v0.27.0 public repository and package"
SOURCE_URL = "https://github.com/headroomlabs-ai/headroom/tree/v0.27.0"
OPERATOR = "maintainer"
BOOTSTRAP_ENV = "CLAIMBOUND_HEADROOM_PROXY_DEPS_BOOTSTRAPPED"

CARD_ORDER = [
    "HEADROOM_PROXY_COMPRESS_ENDPOINT_D003",
    "HEADROOM_PROXY_CCR_HASH_RETRIEVE_D003",
    "HEADROOM_CODEX_PROXY_BOUNDARY_D003",
]

SOURCE_FILES = {
    "docs/content/docs/proxy.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/proxy.mdx",
    "docs/content/docs/ccr.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/ccr.mdx",
    "headroom/proxy/server.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/proxy/server.py",
    "headroom/proxy/handlers/openai.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/proxy/handlers/openai.py",
    "headroom/cli/wrap.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/cli/wrap.py",
    "headroom/providers/codex/runtime.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/providers/codex/runtime.py",
}


def main() -> int:
    args = _parse_args()
    _maybe_bootstrap(args)
    os.environ.setdefault("HEADROOM_TELEMETRY", "off")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    access_date = args.access_date
    source_probe = _collect_source_probe()
    cli_probe = _collect_cli_probe()
    proxy_gate = asyncio.run(_run_proxy_gate())
    env = _collect_environment()
    run_summary = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "access_date": access_date,
        "created_at": access_date,
        "claim_boundary": (
            "Headroom proxy/Codex D003 checks only local proxy compression and "
            "public Codex route surface. It does not publish or inspect private "
            "Codex transcripts."
        ),
        "headroom_expected_version": HEADROOM_VERSION,
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "source_probe": source_probe,
        "cli_probe": cli_probe,
        "proxy_gate": proxy_gate,
        "environment": env,
        "raw_payload_policy": (
            "Synthetic payloads are generated in memory; public artifacts include "
            "hashes, counts and booleans, not full request/response bodies."
        ),
    }
    cards = _build_cards(access_date, run_summary)
    _write_summaries_and_cards(cards, run_summary)
    _update_registry(cards)
    print(f"headroom_proxy_codex_cards_written={len(cards)}")
    for card in cards:
        print(f"{card['evidence_id']} {card['result_status']}")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--access-date",
        default=datetime.now(UTC).date().isoformat(),
        help="Access/run date recorded in cards.",
    )
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Do not re-exec through uv --with when proxy dependencies are missing.",
    )
    return parser.parse_args()


def _maybe_bootstrap(args: argparse.Namespace) -> None:
    if args.no_bootstrap or os.environ.get(BOOTSTRAP_ENV) == "1":
        return
    try:
        import fastapi  # noqa: F401
        import headroom  # noqa: F401
        import httpx  # noqa: F401
        import transformers  # noqa: F401

        return
    except Exception:
        pass
    uv = shutil.which("uv")
    if uv is None:
        return
    env = os.environ.copy()
    env[BOOTSTRAP_ENV] = "1"
    cmd = [
        uv,
        "run",
        "--with",
        f"headroom-ai=={HEADROOM_VERSION}",
        "--with",
        "transformers",
        "--with",
        "fastapi",
        "--with",
        "httpx",
        "--with",
        "uvicorn",
        "python",
        str(Path(__file__).resolve()),
        *sys.argv[1:],
        "--no-bootstrap",
    ]
    os.execvpe(uv, cmd, env)


def _collect_source_probe() -> dict[str, Any]:
    files: dict[str, Any] = {}
    combined = ""
    for name, url in SOURCE_FILES.items():
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                text = response.read().decode("utf-8", errors="replace")
            status = "fetched"
        except (urllib.error.URLError, TimeoutError) as exc:
            text = ""
            status = f"fetch_failed:{type(exc).__name__}"
        combined += "\n" + text
        files[name] = {
            "url": url,
            "status": status,
            "sha256": _sha256_text(text) if text else None,
            "bytes": len(text.encode("utf-8")),
            "mentions": {
                "proxy_compress": "/v1/compress" in text,
                "proxy_retrieve": "/v1/retrieve" in text,
                "ccr_hashes": "ccr_hashes" in text,
                "codex": "codex" in text.lower(),
                "wrap_codex": "wrap codex" in text.lower() or "codex" in name.lower(),
            },
        }
    return {
        "files": files,
        "all_fetches_ok": all(item["status"] == "fetched" for item in files.values()),
        "mentions_proxy_compress": "/v1/compress" in combined,
        "mentions_proxy_retrieve": "/v1/retrieve" in combined,
        "mentions_ccr_hashes": "ccr_hashes" in combined,
        "mentions_codex_route": "codex" in combined.lower(),
        "source_sha256": _sha256_text(combined),
    }


def _collect_cli_probe() -> dict[str, Any]:
    return {
        "headroom_proxy_help": _help_probe(["headroom", "proxy", "--help"]),
        "headroom_wrap_codex_help": _help_probe(["headroom", "wrap", "codex", "--help"]),
    }


def _help_probe(cmd: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": type(exc).__name__}
    text = (completed.stdout or "") + (completed.stderr or "")
    return {
        "available": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_sha256": _sha256_text(text),
        "mentions_proxy": "proxy" in text.lower(),
        "mentions_codex": "codex" in text.lower(),
        "mentions_ccr": "CCR" in text or "headroom_retrieve" in text,
    }


async def _run_proxy_gate() -> dict[str, Any]:
    import httpx
    from headroom.proxy.models import ProxyConfig
    from headroom.proxy.server import create_app

    payload = _fixture_payload()
    app = create_app(
        ProxyConfig(
            stateless=True,
            ccr_inject_marker=True,
            ccr_inject_tool=True,
            ccr_context_tracking=True,
            ccr_proactive_expansion=True,
            compress_user_messages=True,
        )
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://claimbound.local") as client:
        response = await client.post(
            "/v1/compress",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": payload}],
                "config": {"compress_user_messages": True, "protect_recent": 0},
                "token_budget": 4096,
            },
        )
        data = response.json()
        compressed_content = ""
        if response.status_code == 200 and data.get("messages"):
            compressed_content = str(data["messages"][0].get("content", ""))
        marker_hashes = _extract_marker_hashes(compressed_content)
        ccr_hashes = data.get("ccr_hashes", []) if isinstance(data, dict) else []
        retrieve_attempt = None
        retrieve_hash = ccr_hashes[0] if ccr_hashes else (marker_hashes[0] if marker_hashes else None)
        if retrieve_hash:
            retrieve_response = await client.post("/v1/retrieve", json={"hash": retrieve_hash})
            retrieve_attempt = {
                "status_code": retrieve_response.status_code,
                "body_sha256": _sha256_text(retrieve_response.text),
                "matches_fixture": (
                    retrieve_response.status_code == 200
                    and retrieve_response.json().get("original_content") == payload
                ),
            }
        stats_response = await client.get("/v1/retrieve/stats")
        stats = stats_response.json() if stats_response.status_code == 200 else {}
    return {
        "fixture_sha256": _sha256_text(payload),
        "fixture_bytes": len(payload.encode("utf-8")),
        "compress_status_code": response.status_code,
        "tokens_before": data.get("tokens_before"),
        "tokens_after": data.get("tokens_after"),
        "tokens_saved": data.get("tokens_saved"),
        "compression_ratio": data.get("compression_ratio"),
        "transforms_applied": data.get("transforms_applied", []),
        "compressed_sha256": _sha256_text(compressed_content),
        "ccr_hashes_count": len(ccr_hashes),
        "marker_hashes_count": len(marker_hashes),
        "retrieve_attempt": retrieve_attempt,
        "stats_status_code": stats_response.status_code,
        "stats_sanitized": _sanitize_stats(stats),
        "raw_payload_committed": False,
        "private_transcripts_committed": False,
    }


def _extract_marker_hashes(text: str) -> list[str]:
    hashes = re.findall(r"hash=([a-f0-9]{12,24})", text)
    hashes.extend(re.findall(r"<<ccr:([a-f0-9]{12,24})", text))
    return hashes


def _sanitize_stats(stats: dict[str, Any]) -> dict[str, Any]:
    store = stats.get("store", {}) if isinstance(stats, dict) else {}
    backend = store.get("backend", {}) if isinstance(store, dict) else {}
    return {
        "store": {
            "entry_count": store.get("entry_count"),
            "total_original_tokens": store.get("total_original_tokens"),
            "total_compressed_tokens": store.get("total_compressed_tokens"),
            "total_retrievals": store.get("total_retrievals"),
            "backend_type": backend.get("backend_type"),
            "backend_db_path_committed": False,
        },
        "recent_retrievals_count": len(stats.get("recent_retrievals", []))
        if isinstance(stats, dict)
        else None,
    }


def _fixture_payload() -> str:
    rows = []
    for i in range(800):
        rows.append(
            {
                "id": f"CASE-{i:04d}",
                "answer": "TARGET-ALPHA" if i == 73 else "noise",
                "detail": "x" * 120,
            }
        )
    return json.dumps(rows, indent=2, sort_keys=True)


def _collect_environment() -> dict[str, Any]:
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "user_declared_hardware": "MacBook Pro 16 inch, Apple M1 Pro, 16 GB",
        "raw_identifiers_committed": False,
    }


def _build_cards(access_date: str, run_summary: dict[str, Any]) -> list[dict[str, Any]]:
    sequences = _allocate_registry_sequences()
    proxy_gate = run_summary["proxy_gate"]
    source_probe = run_summary["source_probe"]
    cli_probe = run_summary["cli_probe"]
    compress_pass = (
        proxy_gate["compress_status_code"] == 200
        and isinstance(proxy_gate["tokens_saved"], int)
        and proxy_gate["tokens_saved"] > 0
    )
    retrieve_pass = (
        proxy_gate["ccr_hashes_count"] > 0
        and proxy_gate["retrieve_attempt"] is not None
        and proxy_gate["retrieve_attempt"]["matches_fixture"]
    )
    codex_surface = (
        source_probe["mentions_codex_route"]
        and cli_probe["headroom_wrap_codex_help"]["available"]
        and cli_probe["headroom_wrap_codex_help"]["mentions_codex"]
    )
    specs = {
        "HEADROOM_PROXY_COMPRESS_ENDPOINT_D003": {
            "status": "PASSED_UNDER_PROTOCOL" if compress_pass else "NEGATIVE_RESULT_UNDER_PROTOCOL",
            "validity": "GREEN_VALIDATED" if compress_pass else "AMBER_REVIEW",
            "claim_type": "local_proxy_runtime_gate",
            "allowed": (
                "Under HEADROOM_PROXY_CODEX_D003, Headroom local proxy /v1/compress "
                "compressed a synthetic payload and reported positive token savings "
                "without contacting an upstream LLM."
            ),
            "boundary": (
                "This verifies only the local compression-only proxy endpoint. It "
                "does not prove CCR retrieval, Codex routing, cloud billing savings "
                "or final answer quality."
            ),
            "summary": {"proxy_gate": proxy_gate},
            "candidate": "Headroom local ASGI proxy /v1/compress",
            "target": "proxy compression endpoint",
            "controls": "in-process ASGI proxy, synthetic fixture, no upstream LLM",
            "limitations": [
                "Single local operator and fixture family.",
                "No real Codex transcript inspected.",
                "No cloud provider billing measured.",
            ],
        },
        "HEADROOM_PROXY_CCR_HASH_RETRIEVE_D003": {
            "status": "PASSED_UNDER_PROTOCOL" if retrieve_pass else "NEGATIVE_RESULT_UNDER_PROTOCOL",
            "validity": "GREEN_VALIDATED" if retrieve_pass else "AMBER_REVIEW",
            "claim_type": "local_proxy_runtime_gate",
            "allowed": (
                "Under HEADROOM_PROXY_CODEX_D003, the tested /v1/compress response "
                "did not provide a CCR hash that could be used to verify /v1/retrieve "
                "recovery for this synthetic fixture."
            )
            if not retrieve_pass
            else (
                "Under HEADROOM_PROXY_CODEX_D003, /v1/compress provided a CCR hash "
                "and /v1/retrieve returned byte-identical original content."
            ),
            "boundary": (
                "This is a narrow endpoint result for the compression-only proxy API. "
                "It must not be read as a failure of MCP CCR retrieval, which is "
                "covered separately by D002."
            ),
            "summary": {"proxy_gate": proxy_gate},
            "candidate": "Headroom local ASGI proxy /v1/compress plus /v1/retrieve",
            "target": "proxy CCR hash retrieval",
            "controls": "ccr_hashes/marker scan plus retrieve attempt only if hash exists",
            "limitations": [
                "No full agent request/response cycle was sent through proxy.",
                "No private Codex traffic was captured.",
                "MCP CCR retrieval remains a separate positive D002 result.",
            ],
        },
        "HEADROOM_CODEX_PROXY_BOUNDARY_D003": {
            "status": "INSUFFICIENT_COVERAGE",
            "validity": "AMBER_REVIEW" if codex_surface else "RED_BLOCKED",
            "claim_type": "codex_boundary",
            "allowed": (
                "Headroom v0.27.0 exposes public Codex proxy/wrap surface, but "
                "HEADROOM_PROXY_CODEX_D003 did not publish a real Codex transcript "
                "or prove Codex answer equivalence."
            ),
            "boundary": (
                "This card protects against overclaiming. It confirms route surface "
                "signals only; it is not a Codex compatibility pass or failure."
            ),
            "summary": {"source_probe": source_probe, "cli_probe": cli_probe},
            "candidate": "Headroom Codex wrapper/proxy public surface",
            "target": "Codex proxy coverage boundary",
            "controls": "public source probe + CLI help, no private transcript logging",
            "limitations": [
                "No private Codex session was routed or published.",
                "No Codex answer comparison was performed.",
                "No maintainer endorsement implied.",
            ],
        },
    }
    return [_card(key, spec, access_date, sequences[key], run_summary) for key, spec in specs.items()]


def _card(
    card_key: str,
    spec: dict[str, Any],
    access_date: str,
    registry_sequence: int,
    run_summary: dict[str, Any],
) -> dict[str, Any]:
    evidence_id = f"CLAIMBOUND-{card_key}-{access_date}"
    summary_path = f"artifacts/{card_key.lower()}_summary.json"
    summary = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "access_date": access_date,
        "card_key": card_key,
        "claim_boundary": spec["boundary"],
        "allowed_claim_sentence": spec["allowed"],
        "result_status": spec["status"],
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "environment": run_summary["environment"],
        **spec["summary"],
    }
    return {
        "access_date": access_date,
        "ai_assistance": (
            "AI-assisted implementation was used to draft this runner and cards; "
            "result statuses come from deterministic runner gates and source probes."
        ),
        "allowed_claim_sentence": spec["allowed"],
        "baseline_control_summary": spec["controls"],
        "card_svg_rendered": f"docs/evidence_cards/{evidence_id}.svg",
        "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
        "card_validity_level": spec["validity"],
        "claim_boundary": spec["boundary"],
        "claim_type": spec["claim_type"],
        "created_at": access_date,
        "domain": "ai-tooling-evidence",
        "evidence_id": evidence_id,
        "execution_mode": "AUTOMATED_AI_ASSISTED",
        "git_commit": "pending-local-run",
        "known_limitations": spec["limitations"],
        "last_verified_date": access_date,
        "manual_review": (
            "The operator reviewed Headroom v0.27.0 public docs/source and ran "
            "the local deterministic proxy/Codex boundary gates on the recorded environment."
        ),
        "official_source_name": SOURCE_NAME,
        "official_source_url": SOURCE_URL,
        "operator": OPERATOR,
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "raw_payload_committed": False,
        "raw_payload_manifest": (
            "No raw prompts, full synthetic fixture bodies, private transcripts, "
            "credentials, serial number, hardware UUID or provisioning UDID committed; "
            "only sanitized hash/count summaries are public."
        ),
        "record_type": "evidence_result",
        "registry_sequence": registry_sequence,
        "reproduction_level": "not independently reproduced",
        "result_status": spec["status"],
        "runner_command": (
            "HEADROOM_TELEMETRY=off uv run python "
            "scripts/claimbound_run_headroom_proxy_codex.py"
        ),
        "sanitized_report_path": summary_path,
        "sanitized_report_sha256": _sha256_bytes(_json_bytes(summary)),
        "source_rights_note": (
            "Headroom public repository is Apache-2.0; runtime fixtures are "
            "synthetic and generated locally; no private payloads committed."
        ),
        "verification_count": 1,
        "verification_level": "SINGLE_OPERATOR",
        "visual_summary": {
            "allowed_claim_sentence": spec["allowed"],
            "artifact_ref": summary_path,
            "candidate_definition": spec["candidate"],
            "controls_and_gate": spec["controls"],
            "evidence_url": f"docs/evidence_cards/{evidence_id}.json",
            "period_scope": f"Headroom {HEADROOM_TAG} on access date {access_date}",
            "target_definition": spec["target"],
        },
        "_summary_payload": summary,
    }


def _allocate_registry_sequences() -> dict[str, int]:
    registry = _read_json(REPO_ROOT / "docs" / "registry" / "evidence_index.json")
    existing: dict[str, int] = {}
    for entry in registry.get("cards", []):
        evidence_id = str(entry.get("evidence_id", ""))
        for card_key in CARD_ORDER:
            if evidence_id.startswith(f"CLAIMBOUND-{card_key}-"):
                existing[card_key] = int(entry["registry_sequence"])
    used = {
        int(entry["registry_sequence"])
        for entry in registry.get("cards", [])
        if "registry_sequence" in entry
    }
    next_seq = max(used, default=0) + 1
    out: dict[str, int] = {}
    for card_key in CARD_ORDER:
        out[card_key] = existing.get(card_key, next_seq)
        if card_key not in existing:
            next_seq += 1
    return out


def _write_summaries_and_cards(cards: list[dict[str, Any]], run_summary: dict[str, Any]) -> None:
    _write_json(REPO_ROOT / "artifacts" / "headroom_proxy_codex_d003_run_summary.json", run_summary)
    for card in cards:
        summary = card.pop("_summary_payload")
        _write_json(REPO_ROOT / card["sanitized_report_path"], summary)
        _write_json(REPO_ROOT / "docs" / "evidence_cards" / f"{card['evidence_id']}.json", card)


def _update_registry(cards: list[dict[str, Any]]) -> None:
    path = REPO_ROOT / "docs" / "registry" / "evidence_index.json"
    registry = _read_json(path)
    new_ids = {card["evidence_id"] for card in cards}
    new_prefixes = tuple(f"CLAIMBOUND-{key}-" for key in CARD_ORDER)
    retained = [
        entry
        for entry in registry.get("cards", [])
        if entry.get("evidence_id") not in new_ids
        and not str(entry.get("evidence_id", "")).startswith(new_prefixes)
    ]
    retained.extend(_registry_entry(card) for card in cards)
    retained.sort(key=lambda item: int(item["registry_sequence"]))
    registry["cards"] = retained
    registry["card_count"] = len(retained)
    registry["statistics"] = _statistics(retained)
    _write_json(path, registry)


def _registry_entry(card: dict[str, Any]) -> dict[str, Any]:
    evidence_id = card["evidence_id"]
    return {
        "domain": card["domain"],
        "evidence_id": evidence_id,
        "last_verified_date": card["last_verified_date"],
        "official_source_name": card["official_source_name"],
        "operator": card["operator"],
        "path": f"docs/evidence_cards/{evidence_id}.json",
        "record_type": card["record_type"],
        "registry_sequence": card["registry_sequence"],
        "reproduction_level": card["reproduction_level"],
        "result_status": card["result_status"],
        "sanitized_report_path": card["sanitized_report_path"],
        "share_url": (
            "https://github.com/ClaimBound/claimbound-evidence/blob/main/"
            f"docs/evidence_cards/{evidence_id}.json"
        ),
        "verification_count": card["verification_count"],
        "verification_level": card["verification_level"],
        "svg_url": (
            "https://github.com/ClaimBound/claimbound-evidence/blob/main/"
            f"docs/evidence_cards/{evidence_id}.svg"
        ),
    }


def _statistics(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "by_domain": _count(entries, "domain"),
        "by_record_type": _count(entries, "record_type"),
        "by_result_status": _count(entries, "result_status"),
        "by_source": _count(entries, "official_source_name"),
    }


def _count(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(str(entry.get(field, "")) for entry in entries)
    counter.pop("", None)
    return dict(sorted(counter.items()))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_bytes(data).decode("utf-8"), encoding="utf-8")


def _json_bytes(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
