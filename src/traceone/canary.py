"""Versioned exact-answer canaries for paired capability measurements."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from typing import Iterable


def generate_canary(seed: int, items_per_family: int = 12) -> dict:
    """Generate deterministic tasks; use the same artifact for both paired runs."""
    if items_per_family < 1:
        raise ValueError("items_per_family must be positive")
    rng = random.Random(seed)
    items = []
    suffix = " Do not use tools, code execution, search, or a calculator."

    for index in range(items_per_family):
        a, b, c = rng.randint(101, 999), rng.randint(101, 999), rng.randint(1000, 9999)
        modulus = rng.choice((97, 101, 103, 107, 109, 113))
        items.append(
            {
                "id": f"modular-{index:03d}",
                "family": "modular_arithmetic",
                "prompt": f"Compute (({a} * {b}) + {c}) mod {modulus}. Return only the decimal integer.{suffix}",
                "expected": str((a * b + c) % modulus),
            }
        )

    for index in range(items_per_family):
        left, right = rng.randint(120, 999), rng.randint(120, 999)
        divisor = math.gcd(left, right)
        items.append(
            {
                "id": f"gcd-lcm-{index:03d}",
                "family": "gcd_lcm",
                "prompt": (
                    f"For the integers {left} and {right}, compute gcd followed by lcm. "
                    f"Return only `gcd,lcm` with no spaces.{suffix}"
                ),
                "expected": f"{divisor},{left * right // divisor}",
            }
        )

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for index in range(items_per_family):
        source = "".join(rng.choice(alphabet) for _ in range(17))
        shift = rng.randint(2, 14)
        rotated = source[shift:] + source[:shift]
        expected = rotated[::-1]
        items.append(
            {
                "id": f"string-{index:03d}",
                "family": "string_transform",
                "prompt": (
                    f"Take `{source}`. Rotate left by {shift} characters, then reverse the whole "
                    f"result. Return only the final string.{suffix}"
                ),
                "expected": expected,
            }
        )

    for index in range(items_per_family):
        start = rng.randint(5, 40)
        linear = rng.randint(2, 9)
        quadratic = rng.randint(1, 5)
        n = rng.randint(11, 19)
        expected = start + linear * (n - 1) + quadratic * (n - 1) * (n - 2) // 2
        items.append(
            {
                "id": f"sequence-{index:03d}",
                "family": "second_difference_sequence",
                "prompt": (
                    f"A sequence has a_1={start}. Its first difference at step k (from a_k to "
                    f"a_(k+1)) is {linear}+{quadratic}*(k-1). Compute a_{n}. Return only the integer.{suffix}"
                ),
                "expected": str(expected),
            }
        )

    rng.shuffle(items)
    return {
        "schema": "traceone-canary-v1",
        "seed": seed,
        "items_per_family": items_per_family,
        "items": items,
    }


def _extract_answer(text: str) -> str | None:
    stripped = text.strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped or None
    if isinstance(payload, dict) and set(payload) == {"answer"}:
        answer = payload["answer"]
        return str(answer).strip() if answer is not None else None
    if isinstance(payload, (str, int, float)) and not isinstance(payload, bool):
        return str(payload).strip()
    return None


def score_canary(benchmark: dict, responses: Iterable[dict]) -> dict:
    by_id: dict[str, dict] = {}
    for response in responses:
        item_id = str(response["item_id"])
        if item_id in by_id:
            raise ValueError(f"duplicate response for {item_id}")
        by_id[item_id] = response

    outcomes = []
    for item in benchmark["items"]:
        response = by_id.get(item["id"])
        actual = _extract_answer(str(response.get("text", ""))) if response else None
        expected = str(item["expected"]).strip()
        outcomes.append(
            {
                "id": item["id"],
                "family": item["family"],
                "correct": None if actual is None else actual == expected,
                "actual": actual,
            }
        )
    return {
        "schema": "traceone-canary-outcomes-v1",
        "benchmark_schema": benchmark.get("schema"),
        "seed": benchmark.get("seed"),
        "items": outcomes,
    }
