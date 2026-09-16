#!/usr/bin/env python3
"""Leave one collection group out for the fixed ridge enrollment adapter."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from traceone.adapter import adapter_scores, fit_ridge_adapter
from traceone.fingerprint import (
    ENROLLED_OUTER_GUARD,
    TARGET_MODELS,
    classify_parsed,
    load_bank,
)
from traceone.parsing import ParseResult, parse_grid_response


PROJECT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    PROJECT / "data/public/enrollment-v3.jsonl",
    PROJECT / "data/public/confirmation-v6.jsonl",
)
GROUP_PREFIXES = {
    "development-schema": "development_v3",
    "holdout-schema": "validation_v3",
    "confirmation-schema": "confirmation_v1",
    "confirmation-v2-schema": "confirmation_v2",
    "confirmation-v3-schema": "confirmation_v3",
    "confirmation-v4-schema": "confirmation_v4",
    "confirmation-v6-schema": "confirmation_v6",
}


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    estimate = successes / total
    denominator = 1 + z * z / total
    center = (estimate + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(
        estimate * (1 - estimate) / total + z * z / (4 * total * total)
    ) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def load_rows() -> list[dict]:
    rows = []
    for path in PUBLIC_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            prefix = str(raw["source_file"]).split("/", 1)[0].removesuffix(".jsonl")
            if prefix not in GROUP_PREFIXES:
                raise ValueError(f"unmapped public source: {raw['source_file']}")
            group = GROUP_PREFIXES[prefix]
            parsed = parse_grid_response(raw["text"])
            if not parsed.valid:
                raise ValueError(f"invalid row: {raw['sample_id']}")
            rows.append(
                {
                    "group": group,
                    "sample_id": raw["sample_id"],
                    "truth": raw["requested_model"],
                    "numbers": list(parsed.numbers),
                    "parsed": parsed,
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--minimum-margin", type=float, default=0.01)
    parser.add_argument(
        "--output", type=Path, default=PROJECT / "data/adapter-group-cv-v2.json"
    )
    args = parser.parse_args()
    rows = load_rows()
    bank = load_bank()
    predictions = []
    groups_order = list(dict.fromkeys(row["group"] for row in rows))
    for held_group in groups_order:
        training = [row for row in rows if row["group"] != held_group]
        adapter = fit_ridge_adapter(
            [(row["truth"], row["numbers"]) for row in training],
            bank,
            alpha=args.alpha,
            minimum_margin=args.minimum_margin,
        )
        for row in [item for item in rows if item["group"] == held_group]:
            outer = classify_parsed(
                row["parsed"], bank=bank, guard=ENROLLED_OUTER_GUARD
            )
            label = None
            margin = None
            if outer.status == "identified":
                scores = adapter_scores(row["numbers"], bank, adapter)
                order = np.argsort(scores)
                margin = float(scores[order[-1]] - scores[order[-2]])
                if margin >= args.minimum_margin:
                    label = list(TARGET_MODELS)[int(order[-1])]
            predictions.append(
                {
                    "held_group": held_group,
                    "sample_id": row["sample_id"],
                    "truth": row["truth"],
                    "label": label,
                    "correct": label == row["truth"],
                    "adapter_margin": margin,
                    "outer_status": outer.status,
                }
            )

    groups = {}
    for group in groups_order:
        selected = [row for row in predictions if row["held_group"] == group]
        per_model = {}
        for model in TARGET_MODELS:
            model_rows = [row for row in selected if row["truth"] == model]
            correct = sum(row["correct"] for row in model_rows)
            per_model[model] = {
                "samples": len(model_rows),
                "correct": correct,
                "accuracy_including_abstention": correct / len(model_rows),
            }
        correct = sum(row["correct"] for row in selected)
        groups[group] = {
            "samples": len(selected),
            "correct": correct,
            "accuracy_including_abstention": correct / len(selected),
            "wilson_95_interval": wilson(correct, len(selected)),
            "per_model": per_model,
        }
    correct = sum(row["correct"] for row in predictions)
    result = {
        "schema": "traceone-adapter-group-cv-v1",
        "design": "each prediction is made by an adapter trained without its entire collection group",
        "alpha": args.alpha,
        "minimum_adapter_margin": args.minimum_margin,
        "samples": len(predictions),
        "correct": correct,
        "accuracy_including_abstention": correct / len(predictions),
        "wilson_95_interval": wilson(correct, len(predictions)),
        "groups": groups,
        "errors": [row for row in predictions if not row["correct"]],
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
