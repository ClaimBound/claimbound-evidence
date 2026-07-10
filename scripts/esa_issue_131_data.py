# SPDX-License-Identifier: Apache-2.0
"""Frozen claim matrix for ClaimBound issue #131."""

from __future__ import annotations

import base64
import json
import re
import zlib
from collections import Counter
from typing import Any


FROZEN_MATRIX_ZLIB_B64 = """
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
""".strip()


def expected_protocol_ids() -> set[str]:
    expected: set[str] = set()
    for prefix, start in [
        ("S1", 201),
        ("S2", 221),
        ("S3", 241),
        ("S4", 261),
        ("S5P", 281),
    ]:
        for slot in range(1, 21):
            expected.add(f"ESA-{prefix}-{slot:02d}-D{start + slot - 1}")
    return expected


def validate_matrix(matrix: dict[str, Any]) -> None:
    cards = matrix.get("cards")
    if not isinstance(cards, list) or len(cards) != 100:
        raise ValueError("matrix must contain exactly 100 cards")

    ids: list[str] = []
    claims: list[str] = []
    per_mission: Counter[str] = Counter()

    for index, card in enumerate(cards, start=1):
        if not isinstance(card, dict):
            raise ValueError(f"matrix card #{index} must be an object")
        required = {
            "protocol_id",
            "mission",
            "source_url",
            "official_source_name",
            "topic",
            "section",
            "claim",
            "required_patterns",
        }
        missing = sorted(required - set(card))
        if missing:
            raise ValueError(
                f"matrix card #{index} missing: {', '.join(missing)}"
            )

        protocol_id = str(card["protocol_id"])
        source_url = str(card["source_url"])
        claim = str(card["claim"])
        patterns = card["required_patterns"]

        if not source_url.startswith("https://www.esa.int/"):
            raise ValueError(f"{protocol_id}: source must be official esa.int")
        if not isinstance(patterns, list) or not patterns:
            raise ValueError(
                f"{protocol_id}: required_patterns must be non-empty"
            )
        for pattern in patterns:
            re.compile(str(pattern), flags=re.I)

        ids.append(protocol_id)
        claims.append(claim)
        per_mission[str(card["mission"])] += 1

    if len(ids) != len(set(ids)):
        raise ValueError("matrix contains duplicate protocol IDs")
    if set(ids) != expected_protocol_ids():
        missing = sorted(expected_protocol_ids() - set(ids))
        extra = sorted(set(ids) - expected_protocol_ids())
        raise ValueError(
            f"matrix protocol range mismatch; missing={missing}, extra={extra}"
        )
    if len(claims) != len(set(claims)):
        raise ValueError("matrix contains duplicate narrow claims")
    if sorted(per_mission.values()) != [20, 20, 20, 20, 20]:
        raise ValueError(
            f"matrix must contain 20 cards per mission: {dict(per_mission)}"
        )


def load_matrix() -> tuple[dict[str, Any], bytes]:
    compressed = base64.b64decode(FROZEN_MATRIX_ZLIB_B64)
    payload = zlib.decompress(compressed)
    matrix = json.loads(payload.decode("utf-8"))
    if not isinstance(matrix, dict):
        raise ValueError("matrix must be a JSON object")
    validate_matrix(matrix)
    return matrix, payload
