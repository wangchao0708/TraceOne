#!/usr/bin/env python3
"""Check seven-route generalization before fitting the final release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from traceone.adapter import classify_adapted, fit_ridge_adapter
from traceone.fingerprint import ENROLLED_OUTER_GUARD, TARGET_MODELS, load_bank
from traceone.parsing import parse_grid_response
from traceone.support import classify_supported, fit_support


PROJECT = Path(__file__).resolve().parents[1]
OLD_TRAIN = PROJECT / "data/public/enrollment-v3.jsonl"
OLD_DEV = PROJECT / "data/public/confirmation-v6.jsonl"
NEW_ROWS = PROJECT / "data/public/gpt6-enrollment-v1.jsonl"
NEW_MODELS = ("gpt-6-sol", "gpt-6-luna")


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--minimum-margin", type=float, default=0.01)
    parser.add_argument("--distance-quantile", type=float, default=0.99)
    parser.add_argument("--rescue-margin-quantile", type=float, default=0.9)
    args = parser.parse_args()

    old_train = read_rows(OLD_TRAIN)
    old_dev = read_rows(OLD_DEV)
    new = read_rows(NEW_ROWS)
    train = old_train.copy()
    development = old_dev.copy()
    for model in NEW_MODELS:
        rows = sorted((row for row in new if row["requested_model"] == model), key=lambda row: row["sample_id"])
        if len(rows) != 83:
            raise ValueError(f"expected 83 enrollment rows for {model}; got {len(rows)}")
        train.extend(rows[:68])
        development.extend(rows[68:])

    train_counts = Counter(row["requested_model"] for row in train)
    dev_counts = Counter(row["requested_model"] for row in development)
    if set(train_counts) != set(TARGET_MODELS) or set(train_counts.values()) != {68}:
        raise ValueError(f"training split is not balanced: {train_counts}")
    if set(dev_counts) != set(TARGET_MODELS) or set(dev_counts.values()) != {15}:
        raise ValueError(f"development split is not balanced: {dev_counts}")

    bank = load_bank()
    labeled = []
    for row in train:
        parsed = parse_grid_response(row["text"])
        if not parsed.valid:
            raise ValueError(f"invalid training row: {row['sample_id']}")
        labeled.append((row["requested_model"], list(parsed.numbers)))
    adapter = fit_ridge_adapter(
        labeled, bank, alpha=args.alpha, minimum_margin=args.minimum_margin
    )
    support = fit_support(
        labeled, bank, adapter,
        distance_quantile=args.distance_quantile,
        rescue_margin_quantile=args.rescue_margin_quantile,
    )

    decisions = []
    for row in development:
        parsed = parse_grid_response(row.get("text", ""))
        enrolled = classify_adapted(parsed, bank=bank, adapter=adapter, guard=ENROLLED_OUTER_GUARD)
        supported = classify_supported(
            parsed, bank=bank, adapter=adapter, support=support, guard=ENROLLED_OUTER_GUARD
        )
        decisions.append({
            "sample_id": row["sample_id"],
            "requested_model": row["requested_model"],
            "format_compliant": parsed.valid,
            "outer_top": supported.adapter.outer_guard.top_candidate,
            "outer_reasons": supported.adapter.outer_guard.guard_reasons,
            "enrolled": enrolled.label,
            "supported": supported.label,
            "support_path": supported.support_path,
            "adapter_margin": supported.adapter.adapter_margin,
            "support_distance": supported.support_distance,
            "support_threshold": supported.support_threshold,
        })

    per_model = {
        model: {
            "samples": 15,
            "enrolled_matches": sum(row["enrolled"] == model for row in decisions if row["requested_model"] == model),
            "supported_matches": sum(row["supported"] == model for row in decisions if row["requested_model"] == model),
        }
        for model in TARGET_MODELS
    }
    result = {
        "schema": "traceone-seven-development-v1",
        "status": "development; used for release design, never a blind confirmation claim",
        "split": "old five: published enrollment-v3 / confirmation-v6; new two: first 68 / last 15 by sample_id",
        "sources": {
            str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (OLD_TRAIN, OLD_DEV, NEW_ROWS)
        },
        "train_counts": dict(train_counts),
        "development_counts": dict(dev_counts),
        "hyperparameters": {
            "alpha": args.alpha,
            "minimum_margin": args.minimum_margin,
            "distance_quantile": args.distance_quantile,
            "rescue_margin_quantile": args.rescue_margin_quantile,
        },
        "support_thresholds": {
            model: {"distance": support["distance_thresholds"][index], "rescue_margin": support["rescue_margin_thresholds"][index]}
            for index, model in enumerate(TARGET_MODELS)
        },
        "enrolled_matches": sum(row["enrolled"] == row["requested_model"] for row in decisions),
        "supported_matches": sum(row["supported"] == row["requested_model"] for row in decisions),
        "per_model": per_model,
        "decisions": decisions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"samples": len(decisions), "per_model": per_model}, ensure_ascii=False))


if __name__ == "__main__":
    main()
