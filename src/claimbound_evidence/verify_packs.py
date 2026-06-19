# SPDX-License-Identifier: Apache-2.0
"""VERIFY pack shortcuts for cross-platform external operators."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from claimbound_evidence.inspect import load_json, pick_fields


FORBIDDEN_AI_PHRASES = (
    "deployment readiness",
    "model safety",
    "benchmark superiority",
    "runtime behavior",
    "generally safe",
)


@dataclass(frozen=True)
class VerifyCheck:
    name: str
    ok: bool
    detail: str


def _ai_boundary_ok(card_path: Path) -> tuple[bool, str]:
    data = load_json(card_path)
    allowed = str(data.get("allowed_claim_sentence", "")).lower()
    boundary = str(data.get("claim_boundary", "")).lower()
    forbidden_in_allowed = [phrase for phrase in FORBIDDEN_AI_PHRASES if phrase in allowed]
    if forbidden_in_allowed:
        return False, f"forbidden phrases in allowed_claim_sentence: {', '.join(forbidden_in_allowed)}"
    if "source" not in allowed and "audit" not in allowed:
        return False, "allowed_claim_sentence should stay source-audit narrow"
    if "does not" not in boundary and "not verify" not in boundary:
        return False, "claim_boundary should state explicit non-claims"
    return True, "ok"


def verify_source_probe_spec(repo_root: Path) -> list[VerifyCheck]:
    doc = repo_root / "docs" / "SOURCE_PROBE_V1_ACCEPTANCE_CRITERIA.md"
    script = repo_root / "scripts" / "claimbound_source_probe.py"
    text = doc.read_text(encoding="utf-8") if doc.is_file() else ""
    return [
        VerifyCheck("doc_exists", doc.is_file(), str(doc)),
        VerifyCheck(
            "doc_marked_design_only",
            "design document only" in text.lower(),
            "expects 'design document only' in status line",
        ),
        VerifyCheck(
            "probe_script_absent",
            not script.exists(),
            "scripts/claimbound_source_probe.py must not exist yet",
        ),
        VerifyCheck(
            "no_passed_by_itself",
            "must not emit passed_under_protocol by itself" in text.lower(),
            "spec must forbid PASSED_UNDER_PROTOCOL from probe alone",
        ),
    ]


def verify_static_registry_spec(repo_root: Path) -> list[VerifyCheck]:
    doc = repo_root / "docs" / "STATIC_REGISTRY_MVP_ACCEPTANCE_CRITERIA.md"
    script = repo_root / "scripts" / "claimbound_build_registry_view.py"
    views = repo_root / "docs" / "registry" / "views"
    text = doc.read_text(encoding="utf-8") if doc.is_file() else ""
    return [
        VerifyCheck("doc_exists", doc.is_file(), str(doc)),
        VerifyCheck(
            "doc_marked_design_only",
            "design document only" in text.lower(),
            "expects 'design document only' in status line",
        ),
        VerifyCheck(
            "registry_view_script_absent",
            not script.exists(),
            "scripts/claimbound_build_registry_view.py must not exist yet",
        ),
        VerifyCheck(
            "registry_views_absent",
            not views.exists(),
            "docs/registry/views must not exist yet",
        ),
    ]


def _cli_main(argv: list[str]) -> int:
    from claimbound_evidence.cli import main as cli_main

    return int(cli_main(argv))


def verify_api_parity(repo_root: Path) -> list[VerifyCheck]:
    exit_code = _cli_main(["validate-all"])
    checks = [VerifyCheck("validate_all", exit_code == 0, f"exit={exit_code}")]
    registry = load_json(repo_root / "docs" / "registry" / "evidence_index.json")
    card_count = registry.get("card_count")
    checks.append(
        VerifyCheck("card_count_24", card_count == 24, f"card_count={card_count}")
    )
    api_card = repo_root / "docs" / "evidence_cards" / "CLAIMBOUND-API_PARITY_D001-2026-06-15.json"
    if api_card.is_file():
        fields = pick_fields(
            load_json(api_card),
            ("evidence_id", "result_status", "claim_boundary", "runner_command"),
        )
        checks.append(
            VerifyCheck(
                "api_card_present",
                True,
                f"evidence_id={fields['evidence_id']}",
            )
        )
    else:
        checks.append(VerifyCheck("api_card_present", False, "API parity card missing"))
    return checks


def verify_ai_boundary(repo_root: Path) -> list[VerifyCheck]:
    cards = (
        "CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08",
        "CLAIMBOUND-OPENAI_GPT5_SYSTEM_CARD_SOURCE_AUDIT_D001-2026-05-08",
        "CLAIMBOUND-GOOGLE_DEEPMIND_MODEL_CARDS_SOURCE_AUDIT_D001-2026-05-08",
        "CLAIMBOUND-GROK_PROMPTS_SOURCE_AUDIT_D001-2026-05-07",
    )
    checks: list[VerifyCheck] = []
    for card_id in cards:
        path = repo_root / "docs" / "evidence_cards" / f"{card_id}.json"
        if not path.is_file():
            checks.append(VerifyCheck(card_id, False, "missing card"))
            continue
        ok, detail = _ai_boundary_ok(path)
        checks.append(VerifyCheck(card_id, ok, detail))
    return checks


def verify_eea_drift(repo_root: Path) -> list[VerifyCheck]:
    from claimbound_evidence.workflows import drift_eea_source_audit

    baseline = repo_root / "artifacts" / "source_audit_d001_summary.json"
    checks = [
        VerifyCheck("baseline_artifact", baseline.is_file(), str(baseline)),
    ]
    exit_code = drift_eea_source_audit(repo_root)
    checks.append(VerifyCheck("eea_drift_probe", exit_code == 0, f"exit={exit_code}"))
    return checks


def verify_nasa_rerun(repo_root: Path, *, operator: str = "verify-operator") -> list[VerifyCheck]:
    from claimbound_evidence.workflows import rerun_nasa_d103

    baseline = repo_root / "artifacts" / "nasa_power_d103_real_run_summary.json"
    checks = [
        VerifyCheck("baseline_artifact", baseline.is_file(), str(baseline)),
    ]
    exit_code = rerun_nasa_d103(repo_root, operator=operator)
    checks.append(VerifyCheck("nasa_rerun_gate", exit_code == 0, f"exit={exit_code}"))
    return checks


def verify_noaa_rerun(repo_root: Path, *, operator: str = "verify-operator") -> list[VerifyCheck]:
    from claimbound_evidence.workflows import rerun_noaa_d131

    baseline = repo_root / "artifacts" / "noaa_coops_d131_negative_result_summary.json"
    checks = [
        VerifyCheck("baseline_artifact", baseline.is_file(), str(baseline)),
    ]
    exit_code = rerun_noaa_d131(repo_root, operator=operator)
    checks.append(VerifyCheck("noaa_rerun_gate", exit_code == 0, f"exit={exit_code}"))
    return checks


def verify_starter_pack(repo_root: Path) -> list[VerifyCheck]:
    checks: list[VerifyCheck] = []
    for demo_name in ("eea-source-audit", "grok-source-audit"):
        exit_code = _cli_main(["demo", demo_name])
        checks.append(
            VerifyCheck(f"demo_{demo_name}", exit_code == 0, f"exit={exit_code}")
        )

    flagship_cards = (
        "CLAIMBOUND-ANTHROPIC_SYSTEM_CARDS_SOURCE_AUDIT_D001-2026-05-08",
        "CLAIMBOUND-NASA-POWER-D103-2026-04-29",
        "CLAIMBOUND-NOAA-COOPS-D131-2026-04-30",
    )
    for card_id in flagship_cards:
        path = repo_root / "docs" / "evidence_cards" / f"{card_id}.json"
        fields = pick_fields(
            load_json(path),
            ("evidence_id", "result_status", "reproduction_level", "claim_boundary"),
        )
        if card_id.startswith("CLAIMBOUND-NASA-POWER-D103"):
            checks.append(
                VerifyCheck(
                    "nasa_drift_in_reproduction_level",
                    fields["result_status"] == "PASSED_UNDER_PROTOCOL"
                    and "DRIFT" in str(fields["reproduction_level"]),
                    f"result_status={fields['result_status']} "
                    f"reproduction_level={fields['reproduction_level']}",
                )
            )
        else:
            checks.append(
                VerifyCheck(
                    card_id,
                    path.is_file(),
                    f"result_status={fields['result_status']}",
                )
            )
    return checks


VERIFY_PACKS: dict[str, Callable[..., list[VerifyCheck]]] = {
    "starter-pack": verify_starter_pack,
    "ai-boundary": verify_ai_boundary,
    "api-parity": verify_api_parity,
    "source-probe-spec": verify_source_probe_spec,
    "static-registry-spec": verify_static_registry_spec,
    "eea-drift": verify_eea_drift,
    "nasa-rerun": verify_nasa_rerun,
    "noaa-rerun": verify_noaa_rerun,
}

_NETWORK_PACKS = frozenset({"eea-drift", "nasa-rerun", "noaa-rerun"})


def run_verify_pack(repo_root: Path, pack_name: str, *, operator: str = "verify-operator") -> int:
    handler = VERIFY_PACKS.get(pack_name)
    if handler is None:
        raise ValueError(f"unknown verify pack: {pack_name}")
    if pack_name in ("nasa-rerun", "noaa-rerun"):
        checks = handler(repo_root, operator=operator)
    else:
        checks = handler(repo_root)
    ok = True
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")
        ok = ok and check.ok
    print(f"verify_{pack_name}={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1