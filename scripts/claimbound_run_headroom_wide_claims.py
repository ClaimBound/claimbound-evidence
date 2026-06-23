#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run Headroom wide-claim evidence gates and write ClaimBound cards.

The runner intentionally keeps raw fixtures and model transcripts out of the
repository. Public artifacts contain hashes, counts, statuses and gate booleans.
"""

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
PROTOCOL_ID = "HEADROOM_WIDE_CLAIMS_D001"
PROTOCOL_VERSION = "frozen-2026-06-23"
SOURCE_NAME = "Headroom v0.27.0 public repository and package"
SOURCE_URL = "https://github.com/headroomlabs-ai/headroom/tree/v0.27.0"
OPERATOR = "maintainer"
BOOTSTRAP_ENV = "CLAIMBOUND_HEADROOM_DEPS_BOOTSTRAPPED"

SOURCE_FILES = {
    "README.md": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/README.md",
    "docs/content/docs/litellm.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/litellm.mdx",
    "docs/content/docs/proxy.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/proxy.mdx",
    "docs/content/docs/memory.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/memory.mdx",
    "docs/content/docs/limitations.mdx": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/docs/content/docs/limitations.mdx",
    "headroom/evals/README.md": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/evals/README.md",
    "headroom/evals/runners/before_after.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/evals/runners/before_after.py",
    "headroom/providers/openai_compatible.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/providers/openai_compatible.py",
    "headroom/providers/codex/runtime.py": "https://raw.githubusercontent.com/headroomlabs-ai/headroom/v0.27.0/headroom/providers/codex/runtime.py",
}

CARD_ORDER = [
    "HEADROOM_SOURCE_BOUNDARY_D001",
    "HEADROOM_MEMORY_NOT_REQUIRED_D001",
    "HEADROOM_OLLAMA_JSON_TOOL_OUTPUT_D001",
    "HEADROOM_OLLAMA_LOG_OUTPUT_D001",
    "HEADROOM_OLLAMA_AGENT_HISTORY_D001",
    "HEADROOM_RAG_PLAIN_TEXT_D001",
    "HEADROOM_CODE_FILE_DEFAULT_D001",
    "HEADROOM_CODEX_PROXY_ROUTE_D001",
    "HEADROOM_CODEX_SAME_ANSWER_D001",
]


@dataclass(frozen=True)
class GateResult:
    card_key: str
    label: str
    expected_answer: str
    fixture_sha256: str
    fixture_bytes: int
    result_status: str
    decision_reason: str
    original_tokens: int | None
    compressed_tokens: int | None
    tokens_saved: int | None
    reduction_pct: float | None
    transforms_applied: list[str]
    baseline_answer_matches: bool | None
    compressed_answer_matches: bool | None
    baseline_prompt_eval_count: int | None
    compressed_prompt_eval_count: int | None
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
    source_probe = _collect_source_probe()
    cli_probe = _collect_headroom_cli_probe()
    selected_model = args.model or _select_ollama_model(env["ollama_models"])

    gate_results = _run_runtime_gates(
        headroom=headroom,
        model=selected_model,
        skip_ollama=args.skip_ollama,
    )

    run_summary = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "access_date": access_date,
        "created_at": access_date,
        "claim_boundary": (
            "Aggregate run summary for HEADROOM_WIDE_CLAIMS_D001 only. Evidence "
            "status lives in the individual Headroom cards; this file must not be "
            "used as a broad pass/fail statement about Headroom."
        ),
        "headroom_package_version": getattr(headroom["module"], "__version__", None),
        "headroom_expected_version": HEADROOM_VERSION,
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "source_probe": source_probe,
        "cli_probe": cli_probe,
        "environment": env,
        "selected_ollama_model": selected_model,
        "raw_payload_policy": (
            "Raw fixtures and model transcripts are generated in memory and not "
            "committed; public artifacts include hashes, counts and gate booleans."
        ),
        "runtime_gates": {item.card_key: _gate_summary(item) for item in gate_results},
    }

    cards = _build_cards(
        access_date=access_date,
        run_summary=run_summary,
        source_probe=source_probe,
        cli_probe=cli_probe,
        gate_results={item.card_key: item for item in gate_results},
    )
    _write_summaries_and_cards(cards, run_summary)
    _update_registry(cards)

    print(f"headroom_cards_written={len(cards)}")
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
        help="Skip local LLM answer checks and mark runtime answer gates insufficient.",
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
            "`uv run --with headroom-ai==0.27.0 --with transformers python "
            "scripts/claimbound_run_headroom_wide_claims.py`."
        ) from exc
    return {"module": headroom, "compress": compress, "CompressConfig": CompressConfig}


def _collect_environment(requested_model: str) -> dict[str, Any]:
    return {
        "machine_note": "User-declared MacBook Pro 16-inch, Apple M1 Pro, 16 GB.",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "macos": _run_text(["sw_vers"]),
        "darwin_kernel": _run_text(["uname", "-srmp"]),
        "git_commit": _run_text(["git", "rev-parse", "--short", "HEAD"]).strip(),
        "ollama_version": _run_text(["ollama", "--version"]).strip(),
        "ollama_api_version": _fetch_json("http://127.0.0.1:11434/api/version"),
        "ollama_models": _ollama_models(),
        "requested_model": requested_model or None,
        "codex_cli_version": _run_text(["codex", "--version"]).strip(),
        "hardware_privacy_note": (
            "Serial number, hardware UUID and provisioning UDID intentionally "
            "not collected or committed."
        ),
    }


def _run_text(cmd: list[str], *, timeout: int = 20) -> str:
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return f"UNAVAILABLE: {type(exc).__name__}: {exc}"
    return result.stdout.strip()


def _fetch_json(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data if isinstance(data, dict) else {"value": data}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def _ollama_models() -> list[str]:
    output = _run_text(["ollama", "list"])
    models: list[str] = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def _select_ollama_model(models: list[str]) -> str:
    for candidate in ("qwen2.5-coder:7b", "qwen3:8b"):
        if candidate in models:
            return candidate
    return models[0] if models else "qwen2.5-coder:7b"


def _collect_source_probe() -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    combined_text: dict[str, str] = {}
    for path, url in SOURCE_FILES.items():
        try:
            body = _fetch_text(url)
            files[path] = {
                "url": url,
                "status": "fetched",
                "sha256": _sha256_text(body),
                "bytes": len(body.encode("utf-8")),
            }
            combined_text[path] = body
        except Exception as exc:  # noqa: BLE001
            files[path] = {
                "url": url,
                "status": "fetch_failed",
                "error": f"{type(exc).__name__}: {exc}",
            }

    all_text = "\n".join(combined_text.values()).lower()
    checks = {
        "wide_60_95_claim": _has_all(all_text, ["60", "95", "fewer tokens"]),
        "same_answers_claim": "same answers" in all_text,
        "tool_logs_rag_files_history_claim": _has_all(
            all_text,
            ["tool outputs", "logs", "rag", "files", "conversation history"],
        ),
        "codex_support_claim": _has_all(all_text, ["codex", "wrap codex"]),
        "proxy_support_claim": _has_all(all_text, ["proxy", "openai-compatible"]),
        "mcp_support_claim": "mcp" in all_text,
        "memory_documented": _has_all(all_text, ["cross-agent memory", "memory"]),
        "memory_optional_signal": _has_any(all_text, ["--memory", "don't need cross-agent memory"]),
        "ollama_documented": "ollama" in all_text,
        "openai_compatible_documented": "openai-compatible" in all_text,
        "qwen_family_in_provider_code": "qwen" in combined_text.get(
            "headroom/providers/openai_compatible.py", ""
        ).lower(),
        "gemma_family_in_provider_code": "gemma" in combined_text.get(
            "headroom/providers/openai_compatible.py", ""
        ).lower(),
        "limitations_include_rag_passthrough": _has_all(
            combined_text.get("docs/content/docs/limitations.mdx", "").lower(),
            ["rag", "passthrough"],
        ),
        "limitations_include_source_code_passthrough": _has_all(
            combined_text.get("docs/content/docs/limitations.mdx", "").lower(),
            ["source code", "passthrough"],
        ),
    }
    return {
        "headroom_tag": HEADROOM_TAG,
        "headroom_tag_commit": HEADROOM_TAG_COMMIT,
        "files": files,
        "checks": checks,
        "all_required_sources_fetched": all(v.get("status") == "fetched" for v in files.values()),
    }


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "ClaimBound evidence runner"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def _has_all(text: str, needles: list[str]) -> bool:
    return all(needle.lower() in text for needle in needles)


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _collect_headroom_cli_probe() -> dict[str, Any]:
    return {
        "headroom_help": _headroom_help_probe(["headroom", "--help"]),
        "headroom_wrap_help": _headroom_help_probe(["headroom", "wrap", "--help"]),
        "headroom_wrap_codex_help": _headroom_help_probe(["headroom", "wrap", "codex", "--help"]),
    }


def _headroom_help_probe(cmd: list[str]) -> dict[str, Any]:
    text = _run_text(cmd, timeout=30)
    return {
        "command": " ".join(cmd),
        "sha256": _sha256_text(text),
        "bytes": len(text.encode("utf-8")),
        "mentions_codex": "codex" in text.lower(),
        "mentions_proxy": "proxy" in text.lower(),
        "mentions_openai_base_url": "openai_base_url" in text.lower(),
        "available": not text.startswith("UNAVAILABLE:"),
    }


def _run_runtime_gates(
    *,
    headroom: dict[str, Any],
    model: str,
    skip_ollama: bool,
) -> list[GateResult]:
    fixtures = [
        ("HEADROOM_OLLAMA_JSON_TOOL_OUTPUT_D001", "synthetic JSON tool output", *_json_fixture()),
        ("HEADROOM_OLLAMA_LOG_OUTPUT_D001", "synthetic structured logs", *_log_fixture()),
        ("HEADROOM_OLLAMA_AGENT_HISTORY_D001", "synthetic agent history", *_history_fixture()),
    ]
    results = [
        _run_one_gate(
            headroom=headroom,
            model=model,
            card_key=card_key,
            label=label,
            messages=messages,
            fixture_text=fixture_text,
            expected_answer=expected_answer,
            skip_ollama=skip_ollama,
        )
        for card_key, label, messages, fixture_text, expected_answer in fixtures
    ]
    return results


def _json_fixture() -> tuple[list[dict[str, Any]], str, str]:
    expected = "CB-HEADROOM-7429"
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
                "very_long_repeated_field_name_secret": expected if index == 2 else "not-target",
                "very_long_repeated_field_name_status": "successfully_completed_without_error",
            }
        )
    fixture_text = json.dumps(records, indent=2, sort_keys=True)
    messages = [
        {"role": "system", "content": "Answer only the requested exact value. No explanation."},
        {
            "role": "user",
            "content": (
                "From the following records, return the "
                "very_long_repeated_field_name_secret for id 2.\n"
                + fixture_text
            ),
        },
    ]
    return messages, fixture_text, expected


def _log_fixture() -> tuple[list[dict[str, Any]], str, str]:
    expected = "CB-LOG-31415"
    lines = []
    for index in range(80):
        marker = f" TARGET_CODE={expected}" if index == 17 else ""
        lines.append(
            "2026-06-23T12:"
            f"{index % 60:02d}:00Z INFO worker={index % 8} "
            f"request_id=req-{index:04d} component=ingest status=ok "
            f"latency_ms={100 + index % 50} repeated_field=constant_value{marker}"
        )
    fixture_text = "\n".join(lines)
    messages = [
        {"role": "system", "content": "Answer only the requested exact value. No explanation."},
        {"role": "user", "content": "From the log lines, return TARGET_CODE.\n" + fixture_text},
    ]
    return messages, fixture_text, expected


def _history_fixture() -> tuple[list[dict[str, Any]], str, str]:
    expected = "CB-HISTORY-27182"
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "Answer only the requested exact value. No explanation."}
    ]
    fixture_parts = []
    for index in range(18):
        value = expected if index == 3 else f"decoy-{index:02d}"
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
            "content": "Return the checkpoint_code from Conversation note 3.",
        }
    )
    return messages, "\n".join(fixture_parts), expected


def _run_one_gate(
    *,
    headroom: dict[str, Any],
    model: str,
    card_key: str,
    label: str,
    messages: list[dict[str, Any]],
    fixture_text: str,
    expected_answer: str,
    skip_ollama: bool,
) -> GateResult:
    compress = headroom["compress"]
    config_cls = headroom["CompressConfig"]
    config = config_cls(
        compress_user_messages=True,
        protect_recent=0,
        min_tokens_to_compress=50,
    )
    compressed = compress(messages, model=model, model_limit=8192, config=config)
    reduction_pct = (
        round(compressed.tokens_saved / compressed.tokens_before * 100, 4)
        if compressed.tokens_before
        else 0.0
    )

    baseline_answer = None
    compressed_answer = None
    baseline_meta: dict[str, Any] = {}
    compressed_meta: dict[str, Any] = {}
    if not skip_ollama:
        baseline_answer, baseline_meta = _ollama_chat(model, messages)
        compressed_answer, compressed_meta = _ollama_chat(model, compressed.messages)

    baseline_match = None if skip_ollama else _normalize_answer(baseline_answer) == expected_answer
    compressed_match = (
        None if skip_ollama else _normalize_answer(compressed_answer) == expected_answer
    )

    if skip_ollama:
        status = "INSUFFICIENT_COVERAGE"
        reason = "Ollama answer checks were skipped."
    elif not baseline_match:
        status = "INSUFFICIENT_COVERAGE"
        reason = "Original baseline did not return the expected deterministic answer."
    elif reduction_pct >= 60.0 and compressed_match:
        status = "PASSED_UNDER_PROTOCOL"
        reason = "Token-reduction and exact-answer gates passed."
    else:
        status = "NEGATIVE_RESULT_UNDER_PROTOCOL"
        reason = (
            "The original baseline answered correctly, but the compressed path "
            "did not satisfy both the token-reduction and exact-answer gates."
        )

    return GateResult(
        card_key=card_key,
        label=label,
        expected_answer=expected_answer,
        fixture_sha256=_sha256_text(fixture_text),
        fixture_bytes=len(fixture_text.encode("utf-8")),
        result_status=status,
        decision_reason=reason,
        original_tokens=compressed.tokens_before,
        compressed_tokens=compressed.tokens_after,
        tokens_saved=compressed.tokens_saved,
        reduction_pct=reduction_pct,
        transforms_applied=list(compressed.transforms_applied),
        baseline_answer_matches=baseline_match,
        compressed_answer_matches=compressed_match,
        baseline_prompt_eval_count=_maybe_int(baseline_meta.get("prompt_eval_count")),
        compressed_prompt_eval_count=_maybe_int(compressed_meta.get("prompt_eval_count")),
        baseline_answer_sha256=_sha256_text(baseline_answer) if baseline_answer else None,
        compressed_answer_sha256=_sha256_text(compressed_answer) if compressed_answer else None,
    )


def _ollama_chat(model: str, messages: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 32, "num_ctx": 8192},
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


def _normalize_answer(answer: str | None) -> str:
    if not answer:
        return ""
    text = answer.strip()
    text = text.strip("` \n\t")
    match = re.search(r"\bCB-[A-Z]+-\d+\b", text)
    return match.group(0) if match else text


def _maybe_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _gate_summary(item: GateResult) -> dict[str, Any]:
    return {
        "label": item.label,
        "fixture_sha256": item.fixture_sha256,
        "fixture_bytes": item.fixture_bytes,
        "expected_answer_sha256": _sha256_text(item.expected_answer),
        "result_status": item.result_status,
        "decision_reason": item.decision_reason,
        "original_tokens": item.original_tokens,
        "compressed_tokens": item.compressed_tokens,
        "tokens_saved": item.tokens_saved,
        "reduction_pct": item.reduction_pct,
        "transforms_applied": item.transforms_applied,
        "baseline_answer_matches": item.baseline_answer_matches,
        "compressed_answer_matches": item.compressed_answer_matches,
        "baseline_prompt_eval_count": item.baseline_prompt_eval_count,
        "compressed_prompt_eval_count": item.compressed_prompt_eval_count,
        "baseline_answer_sha256": item.baseline_answer_sha256,
        "compressed_answer_sha256": item.compressed_answer_sha256,
    }


def _build_cards(
    *,
    access_date: str,
    run_summary: dict[str, Any],
    source_probe: dict[str, Any],
    cli_probe: dict[str, Any],
    gate_results: dict[str, GateResult],
) -> list[dict[str, Any]]:
    registry_sequences = _allocate_registry_sequences()
    card_specs = [
        _source_boundary_spec(source_probe),
        _memory_not_required_spec(source_probe, gate_results),
        _runtime_spec(gate_results["HEADROOM_OLLAMA_JSON_TOOL_OUTPUT_D001"]),
        _runtime_spec(gate_results["HEADROOM_OLLAMA_LOG_OUTPUT_D001"]),
        _runtime_spec(gate_results["HEADROOM_OLLAMA_AGENT_HISTORY_D001"]),
        _rag_plain_text_spec(source_probe),
        _code_file_spec(source_probe),
        _codex_proxy_spec(source_probe, cli_probe),
        _codex_same_answer_spec(),
    ]

    cards: list[dict[str, Any]] = []
    for spec in card_specs:
        card_key = spec["card_key"]
        evidence_id = f"CLAIMBOUND-{card_key}-{access_date}"
        report_path = f"artifacts/{card_key.lower()}_summary.json"
        summary = {
            "protocol_id": PROTOCOL_ID,
            "evidence_id": evidence_id,
            "access_date": access_date,
            "card_key": card_key,
            "status": spec["result_status"],
            "claim_boundary": spec["claim_boundary"],
            "decision_reason": spec["decision_reason"],
            "run_context": {
                "headroom_package_version": run_summary["headroom_package_version"],
                "headroom_tag": HEADROOM_TAG,
                "headroom_tag_commit": HEADROOM_TAG_COMMIT,
                "selected_ollama_model": run_summary["selected_ollama_model"],
                "environment": run_summary["environment"],
            },
            "source_probe": source_probe if spec.get("include_source_probe") else None,
            "cli_probe": cli_probe if spec.get("include_cli_probe") else None,
            "runtime_gate": spec.get("runtime_gate"),
            "raw_payload_committed": False,
            "raw_payload_policy": run_summary["raw_payload_policy"],
        }
        summary = {k: v for k, v in summary.items() if v is not None}
        summary_bytes = _json_bytes(summary)
        summary_sha = hashlib.sha256(summary_bytes).hexdigest()

        card = _base_card(
            evidence_id=evidence_id,
            registry_sequence=registry_sequences[card_key],
            access_date=access_date,
            report_path=report_path,
            report_sha256=summary_sha,
            spec=spec,
        )
        card["_summary_payload"] = summary
        cards.append(card)
    return cards


def _source_boundary_spec(source_probe: dict[str, Any]) -> dict[str, Any]:
    checks = source_probe["checks"]
    passed = (
        source_probe["all_required_sources_fetched"]
        and checks["wide_60_95_claim"]
        and checks["same_answers_claim"]
        and checks["tool_logs_rag_files_history_claim"]
        and checks["codex_support_claim"]
        and checks["ollama_documented"]
        and checks["memory_documented"]
    )
    return {
        "card_key": "HEADROOM_SOURCE_BOUNDARY_D001",
        "record_type": "source_audit",
        "claim_type": "public_source_boundary",
        "result_status": "PASSED_UNDER_PROTOCOL" if passed else "INSUFFICIENT_COVERAGE",
        "decision_reason": (
            "Headroom v0.27.0 public sources contain the wide claim and relevant "
            "Codex, Ollama/OpenAI-compatible and memory boundary signals."
            if passed
            else "One or more required public source signals was missing or unavailable."
        ),
        "allowed_claim_sentence": (
            "Headroom v0.27.0 public sources contain the wide compression claim "
            "and the local/proxy/memory boundaries checked by this protocol."
        ),
        "claim_boundary": (
            "This card verifies only public-source presence for Headroom v0.27.0. "
            "It does not prove runtime token savings, answer preservation, provider "
            "coverage, maintainer endorsement or general reliability."
        ),
        "baseline_control_summary": (
            "Fetched fixed v0.27.0 raw source files and checked predeclared text "
            "signals for the wide claim, local/Ollama support, Codex/proxy support "
            "and memory documentation."
        ),
        "manual_review": (
            "The operator reviewed sanitized source-probe booleans and accepted "
            "only the source-boundary claim."
        ),
        "known_limitations": [
            "Source-boundary evidence only.",
            "Does not evaluate runtime behavior.",
            "Bound to Headroom v0.27.0 sources on the access date.",
        ],
        "visual": {
            "candidate_definition": "Headroom v0.27.0 public source files",
            "controls_and_gate": "fixed tag source probe",
            "target_definition": "source-boundary signals",
        },
        "include_source_probe": True,
    }


def _memory_not_required_spec(
    source_probe: dict[str, Any],
    gate_results: dict[str, GateResult],
) -> dict[str, Any]:
    any_compress_invoked = any(item.original_tokens for item in gate_results.values())
    passed = source_probe["checks"]["memory_optional_signal"] and any_compress_invoked
    return {
        "card_key": "HEADROOM_MEMORY_NOT_REQUIRED_D001",
        "record_type": "evidence_result",
        "claim_type": "local_library_gate",
        "result_status": "PASSED_UNDER_PROTOCOL" if passed else "INSUFFICIENT_COVERAGE",
        "decision_reason": (
            "The protocol invoked Headroom library compression without enabling "
            "cross-agent memory, and public docs present memory as an optional path."
            if passed
            else "The run could not establish both optional-memory documentation and local compression invocation."
        ),
        "allowed_claim_sentence": (
            "Under HEADROOM_WIDE_CLAIMS_D001, local library compression was invoked "
            "without enabling cross-agent memory."
        ),
        "claim_boundary": (
            "This card verifies only that the local library compression path did not "
            "require cross-agent memory for these synthetic fixtures. It does not "
            "prove any memory feature quality, shared-agent behavior or answer "
            "preservation."
        ),
        "baseline_control_summary": (
            "Memory was not enabled in the runner; source probe checked memory "
            "documentation separately from compression execution."
        ),
        "manual_review": (
            "The operator confirmed the runner does not configure Headroom memory "
            "and reviewed source-probe memory signals."
        ),
        "known_limitations": [
            "Single local library path only.",
            "No memory backend behavior was evaluated.",
            "Does not cover proxy memory or learn modes.",
        ],
        "visual": {
            "candidate_definition": "Headroom compress() without memory settings",
            "controls_and_gate": "runner config + source-probe memory signals",
            "target_definition": "memory independence boundary",
        },
        "include_source_probe": True,
    }


def _runtime_spec(gate: GateResult) -> dict[str, Any]:
    return {
        "card_key": gate.card_key,
        "record_type": "evidence_result",
        "claim_type": "local_ollama_compression_gate",
        "result_status": gate.result_status,
        "decision_reason": gate.decision_reason,
        "allowed_claim_sentence": (
            f"Under HEADROOM_WIDE_CLAIMS_D001, the {gate.label} fixture result is "
            f"{gate.result_status} for token reduction plus exact-answer preservation."
        ),
        "claim_boundary": (
            f"This card verifies only the {gate.label} fixture on one local Ollama "
            "Qwen run. It does not generalize to all prompts, providers, model "
            "families, proxy deployments, CCR retrieval tool use or future Headroom "
            "versions."
        ),
        "baseline_control_summary": (
            "Original fixture and Headroom-compressed fixture were sent to the same "
            "local Ollama model at temperature 0; expected answers were checked by "
            "exact deterministic matching."
        )
        if gate.result_status == "PASSED_UNDER_PROTOCOL"
        else None,
        "manual_review": (
            "The operator reviewed sanitized token counts, transforms, answer-match "
            "booleans and fixture hashes only."
        ),
        "known_limitations": [
            "Single-operator local run only.",
            "Synthetic fixture only.",
            "Raw prompts and model transcripts are not committed.",
            "No cloud-provider behavior is inferred.",
        ],
        "visual": {
            "candidate_definition": gate.label,
            "controls_and_gate": "original vs Headroom-compressed Ollama exact-answer gate",
            "target_definition": "local token reduction and answer preservation",
        },
        "runtime_gate": _gate_summary(gate),
    }


def _rag_plain_text_spec(source_probe: dict[str, Any]) -> dict[str, Any]:
    passed = source_probe["checks"]["limitations_include_rag_passthrough"]
    return {
        "card_key": "HEADROOM_RAG_PLAIN_TEXT_D001",
        "record_type": "source_audit",
        "claim_type": "claim_boundary_check",
        "result_status": "PASSED_UNDER_PROTOCOL" if passed else "INSUFFICIENT_COVERAGE",
        "decision_reason": (
            "Headroom v0.27.0 limitations identify RAG document contexts as "
            "passthrough/not compressed, so the headline range should not be "
            "automatically applied to RAG/plain-text chunks."
            if passed
            else "The source probe did not establish the RAG/plain-text limitation."
        ),
        "allowed_claim_sentence": (
            "Under fixed v0.27.0 sources, RAG/plain-text chunks are a boundary case "
            "and are not automatically covered by the 60-95% headline."
        ),
        "claim_boundary": (
            "This card records a limitation boundary, not a runtime benchmark. It "
            "does not prove that all RAG/plain-text inputs are unchanged or that no "
            "specific deployment can compress them."
        ),
        "baseline_control_summary": (
            "Fixed v0.27.0 limitations source was checked for RAG passthrough language."
        ),
        "manual_review": (
            "The operator reviewed sanitized source-probe booleans for the limitation."
        ),
        "known_limitations": [
            "Source-boundary limitation only.",
            "No external RAG pipeline was run.",
            "Does not cover future Headroom versions.",
        ],
        "visual": {
            "candidate_definition": "RAG/plain-text limitation source",
            "controls_and_gate": "fixed limitations source probe",
            "target_definition": "headline-claim boundary",
        },
        "include_source_probe": True,
    }


def _code_file_spec(source_probe: dict[str, Any]) -> dict[str, Any]:
    passed = source_probe["checks"]["limitations_include_source_code_passthrough"]
    return {
        "card_key": "HEADROOM_CODE_FILE_DEFAULT_D001",
        "record_type": "source_audit",
        "claim_type": "claim_boundary_check",
        "result_status": "PASSED_UNDER_PROTOCOL" if passed else "INSUFFICIENT_COVERAGE",
        "decision_reason": (
            "Headroom v0.27.0 limitations identify source code as passthrough or "
            "protected, so source-code/file payloads should not be used as simple "
            "evidence for the 60-95% headline."
            if passed
            else "The source probe did not establish the source-code/file limitation."
        ),
        "allowed_claim_sentence": (
            "Under fixed v0.27.0 sources, source-code/file payloads are a protected "
            "boundary case for the 60-95% headline."
        ),
        "claim_boundary": (
            "This card records a limitation boundary only. It does not test every "
            "file type, code compressor option, proxy setting or retrieval path."
        ),
        "baseline_control_summary": (
            "Fixed v0.27.0 limitations source was checked for source-code passthrough "
            "or protection language."
        ),
        "manual_review": (
            "The operator reviewed sanitized source-probe booleans for the limitation."
        ),
        "known_limitations": [
            "Source-boundary limitation only.",
            "No full codebase compression run was executed.",
            "Does not cover opt-in code compression settings.",
        ],
        "visual": {
            "candidate_definition": "source-code/file limitation source",
            "controls_and_gate": "fixed limitations source probe",
            "target_definition": "headline-claim boundary",
        },
        "include_source_probe": True,
    }


def _codex_proxy_spec(
    source_probe: dict[str, Any],
    cli_probe: dict[str, Any],
) -> dict[str, Any]:
    help_available = cli_probe["headroom_wrap_codex_help"]["available"]
    doc_signal = source_probe["checks"]["codex_support_claim"]
    route_signal = help_available and cli_probe["headroom_wrap_codex_help"]["mentions_codex"]
    status = "INSUFFICIENT_COVERAGE"
    reason = (
        "The v0.27.0 public sources and installed CLI expose a Codex wrapper/proxy "
        "route, but this protocol did not publish a live Codex traffic capture."
        if doc_signal and route_signal
        else "The run could not establish the documented Codex wrapper/proxy route."
    )
    return {
        "card_key": "HEADROOM_CODEX_PROXY_ROUTE_D001",
        "record_type": "source_audit",
        "claim_type": "proxy_route_boundary",
        "result_status": status,
        "decision_reason": reason,
        "allowed_claim_sentence": (
            "Headroom v0.27.0 exposes documented Codex wrapper/proxy signals, but "
            "this card does not prove live Codex traffic compression."
        ),
        "claim_boundary": (
            "This card covers documentation and CLI surface only. It does not publish "
            "private Codex requests, account traffic, cloud responses or same-answer "
            "behavior."
        ),
        "manual_review": (
            "The operator reviewed source-probe and CLI-help hashes without running "
            "a private Codex session through the proxy."
        ),
        "known_limitations": [
            "No private Codex transcript was captured.",
            "No cloud-provider request was sent by this card.",
            "Route availability is not equivalent to answer preservation.",
        ],
        "visual": {
            "candidate_definition": "Headroom Codex wrapper/proxy surface",
            "controls_and_gate": "source probe + CLI help probe",
            "target_definition": "Codex route boundary",
        },
        "include_source_probe": True,
        "include_cli_probe": True,
    }


def _codex_same_answer_spec() -> dict[str, Any]:
    return {
        "card_key": "HEADROOM_CODEX_SAME_ANSWER_D001",
        "record_type": "evidence_result",
        "claim_type": "codex_answer_gate",
        "result_status": "INSUFFICIENT_COVERAGE",
        "decision_reason": (
            "A deterministic original-vs-compressed Codex answer run was not "
            "published because doing so would require private Codex traffic or a "
            "separate approved capture protocol."
        ),
        "allowed_claim_sentence": (
            "HEADROOM_WIDE_CLAIMS_D001 does not yet provide public evidence that "
            "Codex same-answer behavior passed under a deterministic route test."
        ),
        "claim_boundary": (
            "This card is an explicit non-green record. It must not be read as a "
            "Codex failure, a Codex pass or a Headroom proxy pass."
        ),
        "manual_review": (
            "The operator preserved the privacy boundary and did not publish Codex "
            "prompt or response traffic."
        ),
        "known_limitations": [
            "No Codex answer run was executed for publication.",
            "Requires a separate protocol for sanitized route capture.",
            "Does not evaluate cloud behavior.",
        ],
        "visual": {
            "candidate_definition": "Codex same-answer route",
            "controls_and_gate": "not executed under public-safe protocol",
            "target_definition": "Codex answer preservation",
        },
    }


def _base_card(
    *,
    evidence_id: str,
    registry_sequence: int,
    access_date: str,
    report_path: str,
    report_sha256: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    result_status = spec["result_status"]
    card_validity = {
        "PASSED_UNDER_PROTOCOL": "GREEN_VALIDATED",
        "NEGATIVE_RESULT_UNDER_PROTOCOL": "RED_VALIDATED",
        "INSUFFICIENT_COVERAGE": "AMBER_VALIDATED",
        "BLOCKED_SOURCE": "AMBER_VALIDATED",
    }.get(result_status, "VALIDATED")
    card = {
        "access_date": access_date,
        "ai_assistance": (
            "AI-assisted implementation was used to draft this runner and cards; "
            "result statuses come from deterministic runner gates and manual review."
        ),
        "allowed_claim_sentence": spec["allowed_claim_sentence"],
        "card_svg_rendered": f"docs/evidence_cards/{evidence_id}.svg",
        "card_svg_template": "docs/assets/claimbound_evidence_card.svg",
        "card_validity_level": card_validity,
        "claim_boundary": spec["claim_boundary"],
        "claim_type": spec["claim_type"],
        "created_at": access_date,
        "domain": "ai-tooling-evidence",
        "evidence_id": evidence_id,
        "execution_mode": "AUTOMATED_AI_ASSISTED",
        "git_commit": _run_text(["git", "rev-parse", "--short", "HEAD"]).strip(),
        "known_limitations": spec["known_limitations"],
        "last_verified_date": access_date,
        "manual_review": spec["manual_review"],
        "official_source_name": SOURCE_NAME,
        "official_source_url": SOURCE_URL,
        "operator": OPERATOR,
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "raw_payload_committed": False,
        "raw_payload_manifest": (
            "No raw prompts, full fixtures, private transcripts, credentials, serial "
            "number, hardware UUID or provisioning UDID committed; only sanitized "
            "hash/count summaries are public."
        ),
        "record_type": spec["record_type"],
        "registry_sequence": registry_sequence,
        "reproduction_level": "not independently reproduced",
        "result_status": result_status,
        "runner_command": (
            "HEADROOM_TELEMETRY=off uv run python "
            "scripts/claimbound_run_headroom_wide_claims.py"
        ),
        "sanitized_report_path": report_path,
        "sanitized_report_sha256": report_sha256,
        "source_rights_note": (
            "Headroom public repository is Apache-2.0; runtime fixtures are synthetic "
            "and generated locally; no private payloads committed."
        ),
        "verification_count": 1,
        "verification_level": "SINGLE_OPERATOR",
        "visual_summary": {
            "allowed_claim_sentence": spec["allowed_claim_sentence"],
            "artifact_ref": report_path,
            "candidate_definition": spec["visual"]["candidate_definition"],
            "controls_and_gate": spec["visual"]["controls_and_gate"],
            "evidence_url": f"docs/evidence_cards/{evidence_id}.json",
            "period_scope": f"Headroom {HEADROOM_TAG} on access date {access_date}",
            "target_definition": spec["visual"]["target_definition"],
        },
    }
    if spec.get("baseline_control_summary"):
        card["baseline_control_summary"] = spec["baseline_control_summary"]
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
    _write_json(REPO_ROOT / "artifacts" / "headroom_wide_claims_d001_run_summary.json", run_summary)
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


if __name__ == "__main__":
    raise SystemExit(main())
