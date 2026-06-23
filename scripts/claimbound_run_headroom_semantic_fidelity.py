#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run Headroom semantic-fidelity gates and write ClaimBound cards."""

from __future__ import annotations

import argparse
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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
HEADROOM_VERSION = "0.27.0"
HEADROOM_TAG = "v0.27.0"
HEADROOM_TAG_COMMIT = "95b2333ee5a3f1cbe512ca04a6563c3572835758"
PROTOCOL_ID = "HEADROOM_SEMANTIC_FIDELITY_D004"
PROTOCOL_VERSION = "frozen-2026-06-23"
SOURCE_NAME = "Headroom v0.27.0 public repository and package"
SOURCE_URL = "https://github.com/headroomlabs-ai/headroom/tree/v0.27.0"
OPERATOR = "maintainer"
BOOTSTRAP_ENV = "CLAIMBOUND_HEADROOM_SEMANTIC_DEPS_BOOTSTRAPPED"

CARD_ORDER = [
    "HEADROOM_OLLAMA_JSON_SEMANTIC_SAVINGS_D004",
    "HEADROOM_OLLAMA_LOG_SEMANTIC_SAVINGS_D004",
    "HEADROOM_OLLAMA_HISTORY_SEMANTIC_SAVINGS_D004",
]


@dataclass(frozen=True)
class SemanticFixture:
    card_key: str
    label: str
    messages: list[dict[str, Any]]
    fixture_text: str
    expected_fields: dict[str, Any]


@dataclass(frozen=True)
class SemanticGate:
    card_key: str
    label: str
    result_status: str
    decision_reason: str
    fixture_sha256: str
    fixture_bytes: int
    expected_fields_sha256: str
    original_tokens: int | None
    compressed_tokens: int | None
    tokens_saved: int | None
    reduction_pct: float | None
    transforms_applied: list[str]
    baseline_semantic_match: bool | None
    compressed_semantic_match: bool | None
    baseline_parse_ok: bool | None
    compressed_parse_ok: bool | None
    baseline_prompt_eval_count: int | None
    compressed_prompt_eval_count: int | None
    mismatched_fields: list[str]
    baseline_answer_sha256: str | None
    compressed_answer_sha256: str | None


def main() -> int:
    args = _parse_args()
    _maybe_bootstrap_headroom(args)
    os.environ.setdefault("HEADROOM_TELEMETRY", "off")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    access_date = args.access_date
    headroom = _import_headroom()
    env = _collect_environment(args.model)
    selected_model = args.model or _select_ollama_model(env["ollama_models"])
    gates = [
        _run_gate(headroom, selected_model, fixture, args.skip_ollama)
        for fixture in _fixtures()
    ]
    run_summary = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "access_date": access_date,
        "created_at": access_date,
        "claim_boundary": (
            "Semantic-fidelity follow-up to D001. The gate checks structured "
            "meaning equivalence, not literal answer equality, and combines it "
            "with the same >=60% token-reduction threshold for local Ollama."
        ),
        "headroom_package_version": getattr(headroom["module"], "__version__", None),
        "headroom_expected_version": HEADROOM_VERSION,
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "selected_ollama_model": selected_model,
        "environment": env,
        "raw_payload_policy": (
            "Synthetic fixtures and LLM answers are generated locally. Public "
            "artifacts include hashes, counts, semantic booleans and mismatched "
            "field names, not raw prompts or transcripts."
        ),
        "semantic_gates": {gate.card_key: _gate_summary(gate) for gate in gates},
    }
    cards = _build_cards(access_date, run_summary, gates)
    _write_summaries_and_cards(cards, run_summary)
    _update_registry(cards)
    print(f"headroom_semantic_cards_written={len(cards)}")
    print("headroom_selected_ollama_model=" + str(selected_model))
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
        "--model",
        default="",
        help="Ollama model to use. Defaults to qwen2.5-coder:7b when installed.",
    )
    parser.add_argument(
        "--skip-ollama",
        action="store_true",
        help="Skip local LLM checks and mark cards insufficient.",
    )
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Do not re-exec through uv --with when Headroom dependencies are missing.",
    )
    return parser.parse_args()


def _maybe_bootstrap_headroom(args: argparse.Namespace) -> None:
    if args.no_bootstrap or os.environ.get(BOOTSTRAP_ENV) == "1":
        return
    try:
        import headroom  # noqa: F401
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
            "`uv run python scripts/claimbound_run_headroom_semantic_fidelity.py`."
        ) from exc
    return {"module": headroom, "compress": compress, "CompressConfig": CompressConfig}


def _fixtures() -> list[SemanticFixture]:
    return [_json_fixture(), _log_fixture(), _history_fixture()]


def _json_fixture() -> SemanticFixture:
    records = []
    for index in range(40):
        records.append(
            {
                "very_long_repeated_field_name_description": (
                    "this synthetic record intentionally repeats long field names "
                    "and stable values"
                ),
                "very_long_repeated_field_name_id": index,
                "very_long_repeated_field_name_owner": "claimbound-headroom-evidence-team",
                "very_long_repeated_field_name_region": "us-east-production-cluster",
                "very_long_repeated_field_name_secret": (
                    "CB-HEADROOM-7429" if index == 2 else "not-target"
                ),
                "very_long_repeated_field_name_status": "successfully_completed_without_error",
            }
        )
    fixture_text = json.dumps(records, indent=2, sort_keys=True)
    messages = [
        {
            "role": "system",
            "content": (
                "Return only valid JSON. No markdown. The JSON schema is "
                '{"record_id":number,"secret":string,"status":string}.'
            ),
        },
        {
            "role": "user",
            "content": (
                "Find the record with very_long_repeated_field_name_id=2. "
                "Return record_id, secret, and status from the records below.\n"
                + fixture_text
            ),
        },
    ]
    return SemanticFixture(
        card_key="HEADROOM_OLLAMA_JSON_SEMANTIC_SAVINGS_D004",
        label="synthetic JSON tool output semantic gate",
        messages=messages,
        fixture_text=fixture_text,
        expected_fields={
            "record_id": 2,
            "secret": "CB-HEADROOM-7429",
            "status": "successfully_completed_without_error",
        },
    )


def _log_fixture() -> SemanticFixture:
    lines = []
    for index in range(80):
        marker = " TARGET_CODE=CB-LOG-31415" if index == 17 else ""
        lines.append(
            "2026-06-23T12:"
            f"{index % 60:02d}:00Z INFO worker={index % 8} "
            f"request_id=req-{index:04d} component=ingest status=ok "
            f"latency_ms={100 + index % 50} repeated_field=constant_value{marker}"
        )
    fixture_text = "\n".join(lines)
    messages = [
        {
            "role": "system",
            "content": (
                "Return only valid JSON. No markdown. The JSON schema is "
                '{"target_code":string,"request_id":string,"worker":number}.'
            ),
        },
        {
            "role": "user",
            "content": (
                "Find the log line containing TARGET_CODE. Return TARGET_CODE, "
                "request_id, and worker.\n"
                + fixture_text
            ),
        },
    ]
    return SemanticFixture(
        card_key="HEADROOM_OLLAMA_LOG_SEMANTIC_SAVINGS_D004",
        label="synthetic structured log semantic gate",
        messages=messages,
        fixture_text=fixture_text,
        expected_fields={
            "target_code": "CB-LOG-31415",
            "request_id": "req-0017",
            "worker": 1,
        },
    )


def _history_fixture() -> SemanticFixture:
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "Return only valid JSON. No markdown. The JSON schema is "
                '{"conversation_note":number,"checkpoint_code":string}.'
            ),
        }
    ]
    fixture_parts = []
    for index in range(18):
        value = "CB-HISTORY-27182" if index == 3 else f"decoy-{index:02d}"
        user_text = (
            f"Conversation note {index}. "
            "The user previously inspected a synthetic build artifact with "
            "repeated planning context and stable fields. "
            f"checkpoint_code={value}. "
            "This sentence is repeated to create compressible conversation history. "
            "This sentence is repeated to create compressible conversation history."
        )
        assistant_text = (
            f"Assistant acknowledged note {index} and kept the checkpoint in context. "
            "No private transcript or real user data is present."
        )
        messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": assistant_text})
        fixture_parts.extend([user_text, assistant_text])
    messages.append(
        {
            "role": "user",
            "content": "Return the checkpoint_code from Conversation note 3 and the note number.",
        }
    )
    return SemanticFixture(
        card_key="HEADROOM_OLLAMA_HISTORY_SEMANTIC_SAVINGS_D004",
        label="synthetic agent history semantic gate",
        messages=messages,
        fixture_text="\n".join(fixture_parts),
        expected_fields={"conversation_note": 3, "checkpoint_code": "CB-HISTORY-27182"},
    )


def _run_gate(
    headroom: dict[str, Any],
    model: str,
    fixture: SemanticFixture,
    skip_ollama: bool,
) -> SemanticGate:
    compress = headroom["compress"]
    config_cls = headroom["CompressConfig"]
    compressed = compress(
        fixture.messages,
        model=model,
        model_limit=8192,
        config=config_cls(compress_user_messages=True, protect_recent=0, min_tokens_to_compress=50),
    )
    reduction_pct = (
        round(compressed.tokens_saved / compressed.tokens_before * 100, 4)
        if compressed.tokens_before
        else 0.0
    )
    baseline_answer = ""
    compressed_answer = ""
    baseline_meta: dict[str, Any] = {}
    compressed_meta: dict[str, Any] = {}
    if model and not skip_ollama:
        baseline_answer, baseline_meta = _ollama_chat(model, fixture.messages)
        compressed_answer, compressed_meta = _ollama_chat(model, compressed.messages)

    baseline_parsed = _parse_json_object(baseline_answer) if baseline_answer else None
    compressed_parsed = _parse_json_object(compressed_answer) if compressed_answer else None
    baseline_match = (
        None if skip_ollama or not model else _fields_match(fixture.expected_fields, baseline_parsed)
    )
    compressed_match = (
        None if skip_ollama or not model else _fields_match(fixture.expected_fields, compressed_parsed)
    )
    mismatched = (
        []
        if compressed_parsed is None
        else _mismatched_fields(fixture.expected_fields, compressed_parsed)
    )

    if skip_ollama or not model:
        status = "INSUFFICIENT_COVERAGE"
        reason = "Ollama semantic checks were skipped or no local model was available."
    elif not baseline_match:
        status = "INSUFFICIENT_COVERAGE"
        reason = "Original baseline did not satisfy the deterministic semantic field gate."
    elif reduction_pct >= 60.0 and compressed_match:
        status = "PASSED_UNDER_PROTOCOL"
        reason = "Token-reduction and semantic-field gates passed."
    elif compressed_match and reduction_pct < 60.0:
        status = "NEGATIVE_RESULT_UNDER_PROTOCOL"
        reason = (
            "Semantic fields matched, but Headroom did not reduce tokens by the "
            "predeclared >=60% threshold for this fixture."
        )
    else:
        status = "NEGATIVE_RESULT_UNDER_PROTOCOL"
        reason = (
            "The original baseline matched the semantic fields, but the compressed "
            "path did not preserve the same structured meaning under the gate."
        )

    return SemanticGate(
        card_key=fixture.card_key,
        label=fixture.label,
        result_status=status,
        decision_reason=reason,
        fixture_sha256=_sha256_text(fixture.fixture_text),
        fixture_bytes=len(fixture.fixture_text.encode("utf-8")),
        expected_fields_sha256=_sha256_text(json.dumps(fixture.expected_fields, sort_keys=True)),
        original_tokens=compressed.tokens_before,
        compressed_tokens=compressed.tokens_after,
        tokens_saved=compressed.tokens_saved,
        reduction_pct=reduction_pct,
        transforms_applied=list(compressed.transforms_applied),
        baseline_semantic_match=baseline_match,
        compressed_semantic_match=compressed_match,
        baseline_parse_ok=baseline_parsed is not None if baseline_answer else None,
        compressed_parse_ok=compressed_parsed is not None if compressed_answer else None,
        baseline_prompt_eval_count=_maybe_int(baseline_meta.get("prompt_eval_count")),
        compressed_prompt_eval_count=_maybe_int(compressed_meta.get("prompt_eval_count")),
        mismatched_fields=mismatched,
        baseline_answer_sha256=_sha256_text(baseline_answer) if baseline_answer else None,
        compressed_answer_sha256=_sha256_text(compressed_answer) if compressed_answer else None,
    )


def _ollama_chat(model: str, messages: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 128, "num_ctx": 8192},
    }
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return "", {"error": f"{type(exc).__name__}: {exc}"}
    message = data.get("message") if isinstance(data, dict) else {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    return str(content).strip(), data if isinstance(data, dict) else {}


def _parse_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    stripped = text.strip().strip("` \n\t")
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _fields_match(expected: dict[str, Any], parsed: dict[str, Any] | None) -> bool:
    if parsed is None:
        return False
    return all(parsed.get(key) == value for key, value in expected.items())


def _mismatched_fields(expected: dict[str, Any], parsed: dict[str, Any]) -> list[str]:
    return [key for key, value in expected.items() if parsed.get(key) != value]


def _collect_environment(requested_model: str) -> dict[str, Any]:
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "requested_model": requested_model or None,
        "ollama_models": _ollama_models(),
        "user_declared_hardware": "MacBook Pro 16 inch, Apple M1 Pro, 16 GB",
        "raw_identifiers_committed": False,
    }


def _ollama_models() -> list[str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    models = data.get("models") if isinstance(data, dict) else []
    names = [item.get("name") for item in models if isinstance(item, dict)]
    return sorted(name for name in names if isinstance(name, str))


def _select_ollama_model(models: list[str]) -> str:
    for candidate in ("qwen2.5-coder:7b", "qwen3:8b", "gemma2", "gemma3"):
        if candidate in models:
            return candidate
    return models[0] if models else ""


def _gate_summary(item: SemanticGate) -> dict[str, Any]:
    return {
        "label": item.label,
        "fixture_sha256": item.fixture_sha256,
        "fixture_bytes": item.fixture_bytes,
        "expected_fields_sha256": item.expected_fields_sha256,
        "result_status": item.result_status,
        "decision_reason": item.decision_reason,
        "original_tokens": item.original_tokens,
        "compressed_tokens": item.compressed_tokens,
        "tokens_saved": item.tokens_saved,
        "reduction_pct": item.reduction_pct,
        "transforms_applied": item.transforms_applied,
        "baseline_semantic_match": item.baseline_semantic_match,
        "compressed_semantic_match": item.compressed_semantic_match,
        "baseline_parse_ok": item.baseline_parse_ok,
        "compressed_parse_ok": item.compressed_parse_ok,
        "baseline_prompt_eval_count": item.baseline_prompt_eval_count,
        "compressed_prompt_eval_count": item.compressed_prompt_eval_count,
        "mismatched_fields": item.mismatched_fields,
        "baseline_answer_sha256": item.baseline_answer_sha256,
        "compressed_answer_sha256": item.compressed_answer_sha256,
    }


def _build_cards(
    access_date: str,
    run_summary: dict[str, Any],
    gates: list[SemanticGate],
) -> list[dict[str, Any]]:
    sequences = _allocate_registry_sequences()
    cards = []
    for gate in gates:
        cards.append(_card(gate, access_date, sequences[gate.card_key], run_summary))
    return cards


def _card(
    gate: SemanticGate,
    access_date: str,
    registry_sequence: int,
    run_summary: dict[str, Any],
) -> dict[str, Any]:
    evidence_id = f"CLAIMBOUND-{gate.card_key}-{access_date}"
    summary_path = f"artifacts/{gate.card_key.lower()}_summary.json"
    summary = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "access_date": access_date,
        "card_key": gate.card_key,
        "claim_boundary": _claim_boundary(gate),
        "allowed_claim_sentence": _allowed_sentence(gate),
        "result_status": gate.result_status,
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "selected_ollama_model": run_summary["selected_ollama_model"],
        "environment": run_summary["environment"],
        "semantic_gate": _gate_summary(gate),
    }
    card = {
        "access_date": access_date,
        "ai_assistance": (
            "AI-assisted implementation was used to draft this runner and cards; "
            "result statuses come from deterministic runner gates."
        ),
        "allowed_claim_sentence": _allowed_sentence(gate),
        "baseline_control_summary": (
            "Original and Headroom-compressed contexts were sent to the same local "
            "Ollama model with temperature 0; a deterministic structured-field "
            "checker evaluated semantic equivalence."
        ),
        "card_svg_rendered": f"docs/evidence_cards/{evidence_id}.svg",
        "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
        "card_validity_level": (
            "GREEN_VALIDATED"
            if gate.result_status == "PASSED_UNDER_PROTOCOL"
            else "AMBER_REVIEW"
        ),
        "claim_boundary": _claim_boundary(gate),
        "claim_type": "local_ollama_semantic_gate",
        "created_at": access_date,
        "domain": "ai-tooling-evidence",
        "evidence_id": evidence_id,
        "execution_mode": "AUTOMATED_AI_ASSISTED",
        "git_commit": "pending-local-run",
        "known_limitations": [
            "Single local operator and single Ollama model.",
            "Semantic equivalence is restricted to predeclared structured fields.",
            "No LLM judge was used.",
            "Raw prompts and answers are intentionally not committed.",
        ],
        "last_verified_date": access_date,
        "manual_review": (
            "The operator reviewed the deterministic semantic-field gate and "
            "confirmed this card must not be read as an exact-string test."
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
            "only sanitized hash/count/boolean summaries are public."
        ),
        "record_type": "evidence_result",
        "registry_sequence": registry_sequence,
        "reproduction_level": "not independently reproduced",
        "result_status": gate.result_status,
        "runner_command": (
            "HEADROOM_TELEMETRY=off uv run python "
            "scripts/claimbound_run_headroom_semantic_fidelity.py"
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
            "allowed_claim_sentence": _allowed_sentence(gate),
            "artifact_ref": summary_path,
            "candidate_definition": gate.label,
            "controls_and_gate": "local Ollama semantic-field gate plus token-reduction threshold",
            "evidence_url": f"docs/evidence_cards/{evidence_id}.json",
            "period_scope": f"Headroom {HEADROOM_TAG} on access date {access_date}",
            "target_definition": "same meaning with >=60% fewer input tokens",
        },
        "_summary_payload": summary,
    }
    return card


def _allowed_sentence(gate: SemanticGate) -> str:
    if gate.result_status == "PASSED_UNDER_PROTOCOL":
        return (
            f"Under {PROTOCOL_ID}, {gate.label} preserved predeclared semantic "
            "fields while reducing local Ollama input tokens by at least 60%."
        )
    return (
        f"Under {PROTOCOL_ID}, {gate.label} did not satisfy the combined "
        "semantic-field and >=60% token-reduction gate."
    )


def _claim_boundary(gate: SemanticGate) -> str:
    return (
        "This card checks same-meaning preservation only through predeclared "
        "structured fields, not literal answer equality. It covers one local "
        "Ollama model and one synthetic fixture family; it does not generalize "
        "to all prompts, models, proxy deployments or CCR-enabled workflows."
    )


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
    _write_json(REPO_ROOT / "artifacts" / "headroom_semantic_fidelity_d004_run_summary.json", run_summary)
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


def _maybe_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


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
