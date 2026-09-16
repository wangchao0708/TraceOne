#!/usr/bin/env python3
"""Compare TraceOne one-call decisions with ModelTrace's closed-set scorer.

The comparison reuses the exact upstream unified bank and score fusion already
packaged by TraceOne.  Three-call results use non-overlapping chronological
triplets, so no response contributes to more than one three-call decision.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from traceone.fingerprint import ENROLLED_OUTER_GUARD, load_bank, score_numbers
from traceone.parsing import parse_grid_response
from traceone.support import identify_text_supported


UPSTREAM_COMMIT = "3f0dd2f4b451ad424f3b165a108a468efe4d4d81"


def wilson_interval(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    estimate = successes / total
    denominator = 1 + z * z / total
    center = (estimate + z * z / (2 * total)) / denominator
    radius = (
        z
        * math.sqrt(estimate * (1 - estimate) / total + z * z / (4 * total * total))
        / denominator
    )
    return [max(0.0, center - radius), min(1.0, center + radius)]


def _upstream_prediction(texts: list[str], bank: dict) -> str | None:
    """Reproduce ModelTrace's average-fused-score, closed-set prediction."""
    score_rows = []
    for text in texts:
        parsed = parse_grid_response(text)
        if not parsed.valid:
            continue
        fused, _ = score_numbers(list(parsed.numbers), bank)
        score_rows.append(fused)
    if not score_rows:
        return None
    mean_scores = np.mean(np.stack(score_rows), axis=0)
    return bank["robust"]["model_order"][int(np.argmax(mean_scores))]


def _summary(decisions: list[dict]) -> dict:
    by_model: dict[str, list[dict]] = defaultdict(list)
    for decision in decisions:
        by_model[decision["requested_model"]].append(decision)
    per_model = {}
    for model, rows in sorted(by_model.items()):
        matches = sum(row["prediction"] == model for row in rows)
        per_model[model] = {
            "decisions": len(rows),
            "requested_label_matches": matches,
            "requested_label_match_rate": matches / len(rows),
            "wilson_95_interval": wilson_interval(matches, len(rows)),
        }
    matches = sum(
        row["prediction"] == row["requested_model"] for row in decisions
    )
    return {
        "decisions": len(decisions),
        "requested_label_matches": matches,
        "requested_label_match_rate": matches / len(decisions),
        "wilson_95_interval": wilson_interval(matches, len(decisions)),
        "per_model": per_model,
    }


def evaluate(paths: list[Path]) -> dict:
    rows = []
    for path in paths:
        rows.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    sample_ids = [row["sample_id"] for row in rows]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("duplicate sample_id detected")
    bank = load_bank()

    traceone = []
    upstream_one = []
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        model = row["requested_model"]
        grouped[model].append(row)
        result = identify_text_supported(
            row.get("text", ""),
            response_format="grid",
            guard=ENROLLED_OUTER_GUARD,
        )
        traceone.append(
            {
                "sample_id": row["sample_id"],
                "requested_model": model,
                "prediction": result.label,
                "support_path": result.support_path,
            }
        )
        upstream_one.append(
            {
                "sample_id": row["sample_id"],
                "requested_model": model,
                "prediction": _upstream_prediction([row.get("text", "")], bank),
            }
        )

    upstream_three = []
    for model, model_rows in sorted(grouped.items()):
        ordered = sorted(model_rows, key=lambda row: row["sample_id"])
        if len(ordered) % 3:
            raise ValueError(f"{model} row count is not divisible by three")
        for offset in range(0, len(ordered), 3):
            triplet = ordered[offset : offset + 3]
            upstream_three.append(
                {
                    "sample_ids": [row["sample_id"] for row in triplet],
                    "requested_model": model,
                    "prediction": _upstream_prediction(
                        [row.get("text", "") for row in triplet], bank
                    ),
                }
            )

    return {
        "schema": "traceone-head-to-head-v1",
        "upstream": {
            "repository": "https://github.com/xqy2006/ModelTrace",
            "commit": UPSTREAM_COMMIT,
            "bank_sha256": "6a3f7e4d703990a2322cf535020309380ca858654345d8fe5db278578568bad3",
            "method": "upstream average fused score followed by closed-set argmax",
        },
        "design": (
            "same blind responses and bank; TraceOne and upstream-one each make one "
            "decision per response; upstream-three uses disjoint chronological triplets"
        ),
        "traceone_method": "outer guard + ridge target adapter + empirical target support",
        "comparison_limits": [
            "requested route is not independent served-weight ground truth",
            "the prompt and structured wrapper are TraceOne's, not ModelTrace's randomized challenge wording",
            "the three-call arm has one third as many independent decisions",
            "ModelTrace is closed set and therefore has no unknown decision",
        ],
        "traceone_one_call": _summary(traceone),
        "modeltrace_one_call": _summary(upstream_one),
        "modeltrace_three_call": _summary(upstream_three),
        "decisions": {
            "traceone_one_call": traceone,
            "modeltrace_one_call": upstream_one,
            "modeltrace_three_call": upstream_three,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.inputs)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
