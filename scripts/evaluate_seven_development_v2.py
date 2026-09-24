#!/usr/bin/env python3
"""Three-fold development check after the frozen v9 confirmation failed."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

from traceone.adapter import fit_ridge_adapter
from traceone.fingerprint import ENROLLED_OUTER_GUARD, TARGET_MODELS, load_bank
from traceone.parsing import parse_grid_response
from traceone.support import classify_supported, fit_support, support_score


PROJECT = Path(__file__).resolve().parents[1]
BASE_FILES = (
    PROJECT / "data/public/enrollment-v3.jsonl",
    PROJECT / "data/public/confirmation-v6.jsonl",
    PROJECT / "data/public/gpt6-enrollment-v1.jsonl",
)
FAILED_CONFIRMATION = PROJECT / "data/public/confirmation-v8.jsonl"


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def numbers(row: dict) -> list[int]:
    parsed = parse_grid_response(row["text"] if row.get("return_code", 0) == 0 else "")
    if not parsed.valid:
        raise ValueError(f"development enrollment is invalid: {row['sample_id']}")
    return list(parsed.numbers)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    bank = load_bank()
    base = [row for path in BASE_FILES for row in read_rows(path)]
    failed = read_rows(FAILED_CONFIRMATION)
    counts = Counter(row["requested_model"] for row in failed)
    if set(counts) != set(TARGET_MODELS) or set(counts.values()) != {15}:
        raise ValueError(f"expected 15 failed-confirmation rows per target: {counts}")
    base_labeled = [(row["requested_model"], numbers(row)) for row in base]
    outputs = []
    for maximum_gap, bank_rescue in ((0.075, False), (0.2, False), (0.2, True)):
        guard = replace(ENROLLED_OUTER_GUARD, fallback_maximum_fused_gap=maximum_gap)
        decisions = []
        for fold in range(3):
            training = [
                row for row in failed
                if (int(row["sample_id"].rsplit("__", 1)[-1]) - 1) // 5 != fold
            ]
            held = [
                row for row in failed
                if (int(row["sample_id"].rsplit("__", 1)[-1]) - 1) // 5 == fold
            ]
            labeled = base_labeled + [(row["requested_model"], numbers(row)) for row in training]
            adapter = fit_ridge_adapter(labeled, bank, alpha=1.0, minimum_margin=0.01)
            support = fit_support(labeled, bank, adapter, rescue_margin_quantile=0.9)
            for row in held:
                parsed = parse_grid_response(row["text"])
                result = classify_supported(
                    parsed, bank=bank, adapter=adapter, support=support,
                    guard=guard, allow_bank_rescue=False,
                )
                label = result.label
                path = result.support_path
                outer = result.adapter.outer_guard
                if (bank_rescue and label is None and result.adapter.adapter_margin is not None
                        and result.adapter.adapter_margin < 0.01
                        and outer.status == "identified" and outer.label in TARGET_MODELS
                        and outer.score_margin is not None and outer.score_margin >= 0.25
                        and outer.similarity is not None and outer.similarity >= 0.60):
                    score = support_score(list(parsed.numbers), outer.label, bank, support)
                    if score["distance"] <= score["threshold"]:
                        label = outer.label
                        path = "bank_rescue"
                decisions.append({
                    "sample_id": row["sample_id"],
                    "fold": fold,
                    "requested_model": row["requested_model"],
                    "prediction": label,
                    "outer_top": outer.top_candidate,
                    "outer_marginal": outer.marginal_candidate,
                    "support_path": path,
                })
        outputs.append({
            "fallback_maximum_fused_gap": maximum_gap,
            "bank_rescue": bank_rescue,
            "samples": len(decisions),
            "matches": sum(row["prediction"] == row["requested_model"] for row in decisions),
            "per_model": {
                model: sum(row["prediction"] == model for row in decisions if row["requested_model"] == model)
                for model in TARGET_MODELS
            },
            "errors": [row for row in decisions if row["prediction"] != row["requested_model"]],
        })

    result = {
        "schema": "traceone-seven-development-v2",
        "status": "development after confirmation-v8 failed; not an independent holdout",
        "design": "three chronological 5-per-model folds from failed confirmation-v8; each fit uses 581 prior enrollment rows plus the other 10 per model",
        "hyperparameters": {"alpha": 1.0, "minimum_margin": 0.01, "distance_quantile": 0.99, "rescue_margin_quantile": 0.9},
        "variants": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{key: value for key, value in item.items() if key != "errors"} for item in outputs]))


if __name__ == "__main__":
    main()
