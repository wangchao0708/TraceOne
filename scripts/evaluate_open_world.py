#!/usr/bin/env python3
"""Evaluate rejection when an entire non-target label is absent from the gallery."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import replace
from pathlib import Path

from traceone.adapter import classify_adapted, fit_ridge_adapter
from traceone.fingerprint import ENROLLED_OUTER_GUARD, TARGET_MODELS
from traceone.parsing import ParseResult, parse_grid_response
from traceone.reference import build_scoring_bank, read_reference_rows
from traceone.support import classify_supported, fit_support


PROJECT = Path(__file__).resolve().parents[1]


def wilson(successes: int, total: int) -> list[float]:
    z = 1.959963984540054
    estimate = successes / total
    denominator = 1 + z * z / total
    center = (estimate + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(
        estimate * (1 - estimate) / total + z * z / (4 * total * total)
    ) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def load_live(paths: list[Path], *, require_valid: bool = True) -> list[dict]:
    rows = []
    seen = set()
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            sample_id = str(raw["sample_id"])
            source_key = (str(path.resolve()), sample_id)
            if source_key in seen:
                raise ValueError(f"duplicate row within {path}: {sample_id}")
            seen.add(source_key)
            parsed = parse_grid_response(raw.get("text", ""))
            if require_valid and not parsed.valid:
                raise ValueError(f"invalid live response: {sample_id}")
            rows.append(
                {"sample_id": sample_id, "truth": raw["requested_model"],
                 "numbers": list(parsed.numbers), "parsed": parsed}
            )
    return rows


def summarize(successes: int, total: int) -> dict:
    return {
        "samples": total,
        "count": successes,
        "rate": successes / total,
        "wilson_95_interval": wilson(successes, total),
    }


def evaluate(
    reference_dir: Path,
    enrollment_paths: list[Path],
    target_holdout_paths: list[Path],
    *,
    covariance_shrinkage: float = 0.3,
    distance_quantile: float = 0.99,
    rescue_margin_quantile: float = 0.95,
    adapter_alpha: float = 30.0,
    adapter_margin: float = 0.01,
) -> dict:
    reference = read_reference_rows(reference_dir / "gpt_reference.jsonl", family="gpt")
    reference += read_reference_rows(reference_dir / "claude_reference.jsonl", family="claude")
    enrollment = load_live(enrollment_paths)
    # Invalid/timeout holdout rows remain in the denominator and are scored wrong.
    # Enrollment rows, by contrast, must be valid because they define the fit.
    holdout = load_live(target_holdout_paths, require_valid=False)
    counts = Counter(row["truth"] for row in enrollment)
    if set(counts) != set(TARGET_MODELS) or len(set(counts.values())) != 1:
        raise ValueError(f"balanced five-model enrollment is required: {counts}")

    model_order = list(dict.fromkeys(row["source"] for row in reference))
    excluded = [model for model in model_order if model not in TARGET_MODELS]
    ood_profile = replace(ENROLLED_OUTER_GUARD, minimum_numbers=80)
    folds = []
    all_ood_decisions = []
    supported_holdout_rates = []
    enrolled_holdout_rates = []
    for held_label in excluded:
        fold_rows = [row for row in reference if row["source"] != held_label]
        fold_models = [model for model in model_order if model != held_label]
        bank = build_scoring_bank(fold_rows, fold_models)
        labeled = [(row["truth"], row["numbers"]) for row in enrollment]
        adapter = fit_ridge_adapter(
            labeled, bank, alpha=adapter_alpha, minimum_margin=adapter_margin
        )
        support = fit_support(
            labeled,
            bank,
            adapter,
            covariance_shrinkage=covariance_shrinkage,
            distance_quantile=distance_quantile,
            rescue_margin_quantile=rescue_margin_quantile,
        )
        decisions = []
        for row in [item for item in reference if item["source"] == held_label]:
            parsed = ParseResult(
                tuple(row["numbers"]), True, (), len(row["numbers"]), len(row["numbers"])
            )
            result = classify_supported(
                parsed, bank=bank, adapter=adapter, support=support, guard=ood_profile
            )
            enrolled = classify_adapted(
                parsed, bank=bank, adapter=adapter, guard=ood_profile
            )
            decision = {
                "row_id": row["row_id"],
                "held_label": held_label,
                "prediction": result.label,
                "accepted": result.label is not None,
                "supported_prediction": result.label,
                "supported_accepted": result.label is not None,
                "enrolled_prediction": enrolled.label,
                "enrolled_accepted": enrolled.label is not None,
                "support_path": result.support_path,
            }
            decisions.append(decision)
            all_ood_decisions.append(decision)

        supported_holdout_correct = 0
        enrolled_holdout_correct = 0
        for row in holdout:
            result = classify_supported(
                row["parsed"], bank=bank, adapter=adapter, support=support
            )
            enrolled = classify_adapted(
                row["parsed"], bank=bank, adapter=adapter
            )
            supported_holdout_correct += result.label == row["truth"]
            enrolled_holdout_correct += enrolled.label == row["truth"]
        supported_holdout_rate = supported_holdout_correct / len(holdout)
        enrolled_holdout_rate = enrolled_holdout_correct / len(holdout)
        supported_holdout_rates.append(supported_holdout_rate)
        enrolled_holdout_rates.append(enrolled_holdout_rate)
        false_accepts = sum(item["supported_accepted"] for item in decisions)
        enrolled_false_accepts = sum(item["enrolled_accepted"] for item in decisions)
        folds.append(
            {
                "held_label": held_label,
                "false_accepts": false_accepts,
                "supported_false_accepts": false_accepts,
                "enrolled_false_accepts": enrolled_false_accepts,
                "samples": len(decisions),
                "false_acceptance_rate": false_accepts / len(decisions),
                "target_holdout_correct": supported_holdout_correct,
                "target_holdout_samples": len(holdout),
                "target_holdout_accuracy": supported_holdout_rate,
                "supported_target_holdout_correct": supported_holdout_correct,
                "supported_target_holdout_accuracy": supported_holdout_rate,
                "enrolled_target_holdout_correct": enrolled_holdout_correct,
                "enrolled_target_holdout_accuracy": enrolled_holdout_rate,
            }
        )

    false_accepts = sum(item["supported_accepted"] for item in all_ood_decisions)
    enrolled_false_accepts = sum(
        item["enrolled_accepted"] for item in all_ood_decisions
    )
    return {
        "schema": "traceone-open-world-evaluation-v1",
        "design": (
            "leave one complete excluded label out of the reference bank, adapter feature space, "
            "and support fit; evaluate that omitted label as unseen"
        ),
        "status": "development evidence; hyperparameters were inspected on these data",
        "support_hyperparameters": {
            "covariance_shrinkage": covariance_shrinkage,
            "distance_quantile": distance_quantile,
            "rescue_margin_quantile": rescue_margin_quantile,
        },
        "adapter_hyperparameters": {
            "alpha": adapter_alpha,
            "minimum_margin": adapter_margin,
        },
        "enrollment_rows": len(enrollment),
        "enrollment_per_model": dict(counts),
        "unseen_label_ood": {
            "traceone_supported_false_acceptance": summarize(
                false_accepts, len(all_ood_decisions)
            ),
            "traceone_enrolled_false_acceptance": summarize(
                enrolled_false_accepts, len(all_ood_decisions)
            ),
            "modeltrace_closed_set_false_identification": summarize(
                len(all_ood_decisions), len(all_ood_decisions)
            ),
            "folds": folds,
        },
        "target_holdout_sensitivity": {
            "unique_samples_per_fold": len(holdout),
            "folds": len(folds),
            "mean_accuracy_across_gallery_folds": sum(supported_holdout_rates)
            / len(supported_holdout_rates),
            "minimum_accuracy_across_gallery_folds": min(supported_holdout_rates),
            "supported_mean_accuracy_across_gallery_folds": sum(
                supported_holdout_rates
            )
            / len(supported_holdout_rates),
            "supported_minimum_accuracy_across_gallery_folds": min(
                supported_holdout_rates
            ),
            "enrolled_mean_accuracy_across_gallery_folds": sum(
                enrolled_holdout_rates
            )
            / len(enrolled_holdout_rates),
            "enrolled_minimum_accuracy_across_gallery_folds": min(
                enrolled_holdout_rates
            ),
            "warning": "the same target holdout rows are reused across folds and are not 8x independent",
        },
        "limitations": [
            "held labels come from the upstream corpus rather than a new independent provider",
            "target truth is requested route, not independently attested served weights",
            "the empirical support envelope has no distribution-free OOD guarantee",
        ],
        "decisions": all_ood_decisions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-dir", type=Path, default=PROJECT / "data/reference")
    parser.add_argument("--enrollment", type=Path, nargs="+", required=True)
    parser.add_argument("--target-holdout", type=Path, nargs="+", required=True)
    parser.add_argument("--covariance-shrinkage", type=float, default=0.3)
    parser.add_argument("--distance-quantile", type=float, default=0.99)
    parser.add_argument("--rescue-margin-quantile", type=float, default=0.95)
    parser.add_argument("--adapter-alpha", type=float, default=30.0)
    parser.add_argument("--adapter-margin", type=float, default=0.01)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(
        args.reference_dir,
        args.enrollment,
        args.target_holdout,
        covariance_shrinkage=args.covariance_shrinkage,
        distance_quantile=args.distance_quantile,
        rescue_margin_quantile=args.rescue_margin_quantile,
        adapter_alpha=args.adapter_alpha,
        adapter_margin=args.adapter_margin,
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
