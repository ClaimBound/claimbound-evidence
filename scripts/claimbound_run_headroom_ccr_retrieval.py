#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run Headroom CCR/MCP retrieval evidence gates and write ClaimBound cards."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform
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
PROTOCOL_ID = "HEADROOM_CCR_RETRIEVAL_D002"
PROTOCOL_VERSION = "frozen-2026-06-23"
SOURCE_NAME = "Headroom v0.27.0 public repository and package"
SOURCE_URL = "https://github.com/headroomlabs-ai/headroom/tree/v0.27.0"
OPERATOR = "maintainer"
BOOTSTRAP_ENV = "CLAIMBOUND_HEADROOM_CCR_DEPS_BOOTSTRAPPED"

CARD_ORDER = [
    "HEADROOM_CCR_SOURCE_BOUNDARY_D002",
    "HEADROOM_CCR_MCP_FULL_RETRIEVE_D002",
    "HEADROOM_CCR_MCP_QUERY_RETRIEVE_D002",
    "HEADROOM_DIRECT_COMPRESS_NOT_CCR_D002",
]

SOURCE_FILES = {
    "docs/content/docs/ccr.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/ccr.mdx",
    "docs/content/docs/mcp.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/mcp.mdx",
    "docs/content/docs/proxy.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/proxy.mdx",
    "headroom/ccr/mcp_server.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/ccr/mcp_server.py",
    "headroom/ccr/tool_injection.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/ccr/tool_injection.py",
    "headroom/compress.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/compress.py",
}


def main() -> int:
    args = _parse_args()
    _maybe_bootstrap_headroom(args)
    os.environ.setdefault("HEADROOM_TELEMETRY", "off")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    access_date = args.access_date
    headroom = _import_headroom()
    source_probe = _collect_source_probe()
    cli_probe = _collect_cli_probe()
    mcp_result = asyncio.run(_run_mcp_gate())
    direct_result = _run_direct_compress_gate(headroom)
    env = _collect_environment()

    run_summary = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "access_date": access_date,
        "created_at": access_date,
        "claim_boundary": (
            "Aggregate run summary for Headroom CCR/MCP retrieval checks. It is "
            "not a broad certification of Headroom, Codex, Ollama, or all agent "
            "traffic; card outcomes define the allowed claims."
        ),
        "headroom_package_version": getattr(headroom["module"], "__version__", None),
        "headroom_expected_version": HEADROOM_VERSION,
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "source_probe": source_probe,
        "cli_probe": cli_probe,
        "mcp_gate": mcp_result,
        "direct_compress_gate": direct_result,
        "environment": env,
        "raw_payload_policy": (
            "Synthetic payloads are generated in memory. Public artifacts include "
            "hashes, token counts and boolean gates, not full raw content."
        ),
    }

    cards = _build_cards(access_date, run_summary)
    _write_summaries_and_cards(cards, run_summary)
    _update_registry(cards)
    print(f"headroom_ccr_cards_written={len(cards)}")
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
        help="Do not re-exec through uv --with when Headroom/MCP dependencies are missing.",
    )
    return parser.parse_args()


def _maybe_bootstrap_headroom(args: argparse.Namespace) -> None:
    if args.no_bootstrap or os.environ.get(BOOTSTRAP_ENV) == "1":
        return
    try:
        import headroom  # noqa: F401
        import mcp  # noqa: F401
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
        "mcp",
        "python",
        str(Path(__file__).resolve()),
        *sys.argv[1:],
        "--no-bootstrap",
    ]
    os.execvpe(uv, cmd, env)


def _import_headroom() -> dict[str, Any]:
    try:
        import headroom
        from headroom import CompressConfig, compress
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "Headroom dependencies are unavailable. Run with "
            "`uv run python scripts/claimbound_run_headroom_ccr_retrieval.py`."
        ) from exc
    return {"module": headroom, "compress": compress, "CompressConfig": CompressConfig}


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
                "ccr": "Compress-Cache-Retrieve" in text or "CCR" in text,
                "headroom_retrieve": "headroom_retrieve" in text,
                "headroom_compress": "headroom_compress" in text,
                "proxy_retrieve_endpoint": "/v1/retrieve" in text,
                "local_store": "CompressionStore" in text or "local store" in text,
            },
        }
    lower = combined.lower()
    return {
        "files": files,
        "all_fetches_ok": all(item["status"] == "fetched" for item in files.values()),
        "mentions_ccr": "compress-cache-retrieve" in lower or "ccr" in lower,
        "mentions_retrieve_tool": "headroom_retrieve" in combined,
        "mentions_compress_tool": "headroom_compress" in combined,
        "mentions_proxy_retrieve_endpoint": "/v1/retrieve" in combined,
        "mentions_direct_compress_as_ccr": "compress() stores original" in lower,
        "source_sha256": _sha256_text(combined),
    }


def _collect_cli_probe() -> dict[str, Any]:
    return {
        "headroom_mcp_help": _help_probe(["headroom", "mcp", "--help"]),
        "headroom_proxy_help": _help_probe(["headroom", "proxy", "--help"]),
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
        "mentions_ccr": "CCR" in text or "Compress-Cache-Retrieve" in text,
        "mentions_headroom_retrieve": "headroom_retrieve" in text,
        "mentions_headroom_compress": "headroom_compress" in text,
        "mentions_no_ccr_marker": "--no-ccr-marker" in text,
    }


async def _run_mcp_gate() -> dict[str, Any]:
    from headroom.ccr.mcp_server import HeadroomMCPServer

    payload = _fixture_payload()
    server = HeadroomMCPServer(check_proxy=False)
    compress_items = await server._handle_compress({"content": payload})
    compression = json.loads(compress_items[0].text)
    hash_key = compression["hash"]
    full_items = await server._handle_retrieve({"hash": hash_key})
    full = json.loads(full_items[0].text)
    query_items = await server._handle_retrieve(
        {"hash": hash_key, "query": "TARGET-ALPHA CASE-0073"}
    )
    query = json.loads(query_items[0].text)
    full_content = full.get("original_content", "")
    query_serialized = json.dumps(query, sort_keys=True)
    return {
        "fixture_sha256": _sha256_text(payload),
        "fixture_bytes": len(payload.encode("utf-8")),
        "hash": hash_key,
        "hash_length": len(hash_key),
        "hash_prefix": hash_key[:12],
        "compression": {
            "original_tokens": compression.get("original_tokens"),
            "compressed_tokens": compression.get("compressed_tokens"),
            "tokens_saved": compression.get("tokens_saved"),
            "savings_percent": compression.get("savings_percent"),
            "transforms": compression.get("transforms", []),
            "compressed_sha256": _sha256_text(str(compression.get("compressed", ""))),
            "note_mentions_retrieve_tool": "headroom" in compression.get("note", ""),
        },
        "full_retrieve": {
            "source": full.get("source"),
            "content_sha256": _sha256_text(full_content),
            "matches_fixture_sha256": _sha256_text(full_content) == _sha256_text(payload),
            "matches_fixture_exact": full_content == payload,
            "returned_raw_content_committed": False,
        },
        "query_retrieve": {
            "source": query.get("source"),
            "count": query.get("count"),
            "has_target_answer": "TARGET-ALPHA" in query_serialized,
            "has_target_case": "CASE-0073" in query_serialized,
            "results_sha256": _sha256_text(query_serialized),
            "fallback_full_content": "original_content" in query,
        },
    }


def _run_direct_compress_gate(headroom: dict[str, Any]) -> dict[str, Any]:
    payload = _fixture_payload()
    compress = headroom["compress"]
    config_cls = headroom["CompressConfig"]
    result = compress(
        [{"role": "tool", "content": payload}],
        model="claude-sonnet-4-5-20250929",
        config=config_cls(compress_user_messages=True, min_tokens_to_compress=50, protect_recent=0),
    )
    compressed = str(result.messages[0].get("content", ""))
    has_ccr_marker = "hash=" in compressed or "<<ccr:" in compressed
    return {
        "fixture_sha256": _sha256_text(payload),
        "tokens_before": result.tokens_before,
        "tokens_after": result.tokens_after,
        "tokens_saved": result.tokens_saved,
        "compression_ratio": result.compression_ratio,
        "transforms": result.transforms_applied,
        "compressed_sha256": _sha256_text(compressed),
        "has_ccr_marker": has_ccr_marker,
        "stored_hash_observed": False,
    }


def _fixture_payload() -> str:
    rows = []
    for i in range(300):
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
    source_probe = run_summary["source_probe"]
    mcp_gate = run_summary["mcp_gate"]
    direct_gate = run_summary["direct_compress_gate"]

    source_pass = (
        source_probe["all_fetches_ok"]
        and source_probe["mentions_retrieve_tool"]
        and source_probe["mentions_compress_tool"]
        and source_probe["mentions_proxy_retrieve_endpoint"]
    )
    full_pass = (
        mcp_gate["compression"]["tokens_saved"] > 0
        and mcp_gate["full_retrieve"]["matches_fixture_exact"]
    )
    query_pass = (
        mcp_gate["query_retrieve"]["count"] == 1
        and mcp_gate["query_retrieve"]["has_target_answer"]
        and mcp_gate["query_retrieve"]["has_target_case"]
    )
    direct_boundary_pass = direct_gate["tokens_saved"] > 0 and not direct_gate["has_ccr_marker"]

    specs = {
        "HEADROOM_CCR_SOURCE_BOUNDARY_D002": {
            "status": "PASSED_UNDER_PROTOCOL" if source_pass else "NEGATIVE_RESULT_UNDER_PROTOCOL",
            "validity": "GREEN_VALIDATED" if source_pass else "AMBER_REVIEW",
            "claim_type": "source_boundary",
            "allowed": (
                "Headroom v0.27.0 public docs/source expose CCR/MCP compression, "
                "headroom_retrieve and proxy retrieve endpoints as the documented "
                "recoverability path."
            ),
            "boundary": (
                "This card verifies documented/source surface only. It does not prove "
                "agent answer quality, Codex traffic handling or all provider integrations."
            ),
            "summary": {"source_probe": source_probe, "cli_probe": run_summary["cli_probe"]},
            "candidate": "Headroom v0.27.0 CCR, MCP and proxy public sources",
            "target": "official CCR procedure boundary",
            "controls": "raw source fetch + CLI help probe",
            "limitations": [
                "Public source audit only.",
                "No maintainer endorsement implied.",
                "Does not cover future Headroom versions.",
            ],
        },
        "HEADROOM_CCR_MCP_FULL_RETRIEVE_D002": {
            "status": "PASSED_UNDER_PROTOCOL" if full_pass else "NEGATIVE_RESULT_UNDER_PROTOCOL",
            "validity": "GREEN_VALIDATED" if full_pass else "AMBER_REVIEW",
            "claim_type": "local_mcp_runtime_gate",
            "allowed": (
                "Under HEADROOM_CCR_RETRIEVAL_D002, Headroom MCP compression stored "
                "a synthetic JSON payload and full retrieve returned byte-identical "
                "content by hash."
            ),
            "boundary": (
                "This proves local MCP store/retrieve behavior for one synthetic "
                "payload on one MacBook Pro environment. It does not prove final LLM "
                "answers, proxy routing, Codex routing or cloud provider behavior."
            ),
            "summary": {"mcp_gate": mcp_gate},
            "candidate": "Headroom MCP headroom_compress then headroom_retrieve",
            "target": "local CCR full retrieval",
            "controls": "same-process MCP server, synthetic fixture hash equality",
            "limitations": [
                "Single local operator and single fixture family.",
                "Raw original content is intentionally not committed.",
                "MCP SDK is required for reproduction.",
            ],
        },
        "HEADROOM_CCR_MCP_QUERY_RETRIEVE_D002": {
            "status": "PASSED_UNDER_PROTOCOL" if query_pass else "NEGATIVE_RESULT_UNDER_PROTOCOL",
            "validity": "GREEN_VALIDATED" if query_pass else "AMBER_REVIEW",
            "claim_type": "local_mcp_runtime_gate",
            "allowed": (
                "Under HEADROOM_CCR_RETRIEVAL_D002, Headroom MCP query retrieve "
                "found the synthetic target row containing CASE-0073 and TARGET-ALPHA."
            ),
            "boundary": (
                "This verifies one deterministic query over one stored synthetic "
                "payload. It does not prove semantic ranking quality for arbitrary "
                "queries or that an LLM will choose to call retrieve at the right time."
            ),
            "summary": {"mcp_gate": mcp_gate},
            "candidate": "Headroom MCP headroom_retrieve(hash, query)",
            "target": "local CCR targeted retrieval",
            "controls": "known target row + structured query result checks",
            "limitations": [
                "Only one query and one fixture family.",
                "Does not evaluate natural-language ambiguity.",
                "Does not evaluate cloud or Codex tool-call execution.",
            ],
        },
        "HEADROOM_DIRECT_COMPRESS_NOT_CCR_D002": {
            "status": "PASSED_UNDER_PROTOCOL" if direct_boundary_pass else "NEGATIVE_RESULT_UNDER_PROTOCOL",
            "validity": "GREEN_VALIDATED" if direct_boundary_pass else "AMBER_REVIEW",
            "claim_type": "procedure_boundary",
            "allowed": (
                "Under HEADROOM_CCR_RETRIEVAL_D002, plain library compress() reduced "
                "tokens but did not expose a CCR retrieve hash for this fixture."
            ),
            "boundary": (
                "This boundary explains why direct-compress exact-answer checks must "
                "not be treated as a full test of Headroom's documented CCR path."
            ),
            "summary": {"direct_compress_gate": direct_gate},
            "candidate": "Headroom plain compress() library call",
            "target": "non-CCR direct compression boundary",
            "controls": "same synthetic fixture, marker/hash scan",
            "limitations": [
                "One fixture and local library invocation only.",
                "Does not claim direct compress() can never use CCR in future versions.",
                "Does not invalidate MCP/proxy CCR behavior.",
            ],
        },
    }

    return [
        _card(card_key, spec, access_date, sequences[card_key], run_summary)
        for card_key, spec in specs.items()
    ]


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
        "headroom_package_version": run_summary["headroom_package_version"],
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "environment": run_summary["environment"],
        **spec["summary"],
    }
    card = {
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
            "the local deterministic CCR/MCP gates on the recorded environment."
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
            "scripts/claimbound_run_headroom_ccr_retrieval.py"
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
    return card


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
        if card_key in existing:
            out[card_key] = existing[card_key]
        else:
            out[card_key] = next_seq
            next_seq += 1
    return out


def _write_summaries_and_cards(cards: list[dict[str, Any]], run_summary: dict[str, Any]) -> None:
    _write_json(REPO_ROOT / "artifacts" / "headroom_ccr_retrieval_d002_run_summary.json", run_summary)
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
