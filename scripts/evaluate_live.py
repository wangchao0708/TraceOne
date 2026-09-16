#!/usr/bin/env python3
"""Evaluate saved Codex runs without treating the requested route as hidden truth."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from traceone.adapter import identify_text_adapted
from traceone.fingerprint import (
    ADAPTIVE_GUARD,
    BALANCED_GUARD,
    ENROLLED_OUTER_GUARD,
    STRICT_GUARD,
    identify_text,
)
from traceone.support import identify_text_supported


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if total == 0:
        return None
    estimate = successes / total
    denominator = 1 + z * z / total
    center = (estimate + z * z / (2 * total)) / denominator
    radius = (
        z
        * math.sqrt(estimate * (1 - estimate) / total + z * z / (4 * total * total))
        / denominator
    )
    return [max(0.0, center - radius), min(1.0, center + radius)]


def evaluate(paths: list[Path]) -> dict:
    rows = []
    for path in paths:
        rows.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    sample_ids = [str(row.get("sample_id")) for row in rows]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("duplicate sample_id detected; evaluation stopped")
    samples = []
    for row in rows:
        prompt_id = str(row.get("prompt_id"))
        grid_prompts = {"identity-v2-grid", "identity-v3-schema", "identity-web-v1"}
        response_format = (
            "grid"
            if row.get("output_schema") or prompt_id in grid_prompts or "grid" in prompt_id
            else "flat"
        )
        results = {}
        supported = identify_text_supported(
            row.get("text", ""),
            response_format=response_format,
            guard=ENROLLED_OUTER_GUARD,
        )
        supported_outer = supported.adapter.outer_guard
        results["supported"] = {
            "status": supported.status,
            "label": supported.label,
            "top_candidate": supported_outer.top_candidate,
            "marginal_candidate": supported_outer.marginal_candidate,
            "format_compliant": supported_outer.format_compliant,
            "usable_numbers": supported_outer.usable_numbers,
            "guard_reasons": supported_outer.guard_reasons,
            "similarity": supported_outer.similarity,
            "score_margin": supported_outer.score_margin,
            "marginal_score_margin": supported_outer.marginal_score_margin,
            "decision_path": supported.support_path,
            "adapter_margin": supported.adapter.adapter_margin,
            "support_distance": supported.support_distance,
            "support_threshold": supported.support_threshold,
            "support_p_value": supported.support_p_value,
        }
        enrolled = identify_text_adapted(
            row.get("text", ""),
            response_format=response_format,
            guard=ENROLLED_OUTER_GUARD,
        )
        results["enrolled"] = {
            "status": enrolled.status,
            "label": enrolled.label,
            "top_candidate": enrolled.outer_guard.top_candidate,
            "marginal_candidate": enrolled.outer_guard.marginal_candidate,
            "format_compliant": enrolled.outer_guard.format_compliant,
            "usable_numbers": enrolled.outer_guard.usable_numbers,
            "guard_reasons": enrolled.outer_guard.guard_reasons,
            "similarity": enrolled.outer_guard.similarity,
            "score_margin": enrolled.outer_guard.score_margin,
            "marginal_score_margin": enrolled.outer_guard.marginal_score_margin,
            "decision_path": "ridge_adapter" if enrolled.label else None,
            "adapter_margin": enrolled.adapter_margin,
        }
        for name, guard in (
            ("adaptive", ADAPTIVE_GUARD),
            ("balanced", BALANCED_GUARD),
            ("strict", STRICT_GUARD),
        ):
            result = identify_text(row.get("text", ""), response_format=response_format, guard=guard)
            results[name] = {
                "status": result.status,
                "label": result.label,
                "top_candidate": result.top_candidate,
                "marginal_candidate": result.marginal_candidate,
                "format_compliant": result.format_compliant,
                "usable_numbers": result.usable_numbers,
                "guard_reasons": result.guard_reasons,
                "similarity": result.similarity,
                "score_margin": result.score_margin,
                "marginal_score_margin": result.marginal_score_margin,
                "decision_path": result.decision_path,
            }
        samples.append(
            {
                "sample_id": row.get("sample_id"),
                "requested_model": row.get("requested_model"),
                "response_model": row.get("response_model"),
                "reasoning_effort": row.get("reasoning_effort"),
                "runtime": row.get("runtime"),
                "return_code": row.get("return_code"),
                **results,
            }
        )

    profiles = {}
    for profile in ("supported", "enrolled", "adaptive", "balanced", "strict"):
        per_model: dict[str, dict] = {}
        groups: dict[str, list[dict]] = defaultdict(list)
        for sample in samples:
            groups[str(sample["requested_model"])].append(sample)
        for model, group in sorted(groups.items()):
            matches = sum(sample[profile]["label"] == model for sample in group)
            identified = sum(sample[profile]["label"] is not None for sample in group)
            per_model[model] = {
                "samples": len(group),
                "requested_label_matches": matches,
                "requested_label_match_rate_including_abstention": matches / len(group),
                "wilson_95_interval": wilson_interval(matches, len(group)),
                "identified": identified,
                "coverage": identified / len(group),
                "format_compliant": sum(sample[profile]["format_compliant"] for sample in group),
            }
        matches = sum(
            sample[profile]["label"] == sample["requested_model"] for sample in samples
        )
        identified = sum(sample[profile]["label"] is not None for sample in samples)
        profiles[profile] = {
            "samples": len(samples),
            "requested_label_matches": matches,
            "requested_label_match_rate_including_abstention": matches / len(samples),
            "wilson_95_interval": wilson_interval(matches, len(samples)),
            "identified": identified,
            "coverage": identified / len(samples),
            "format_compliant": sum(sample[profile]["format_compliant"] for sample in samples),
            "per_model": per_model,
        }

    return {
        "schema": "traceone-live-evaluation-v1",
        "truth_limitation": (
            "requested_model is a control-plane label, not independent proof of served weights; "
            "metrics are route-label agreement, not audited ground-truth accuracy"
        ),
        "provenance": {
            "splits": sorted({str(row.get("split")) for row in rows}),
            "prompt_sha256": sorted({str(row.get("prompt_sha256")) for row in rows}),
            "output_schema_sha256": sorted(
                {str(row.get("output_schema_sha256")) for row in rows}
            ),
            "reasoning_efforts": sorted({str(row.get("reasoning_effort")) for row in rows}),
            "runtimes": sorted({str(row.get("runtime")) for row in rows}),
            "wrappers": sorted({str(row.get("wrapper")) for row in rows}),
        },
        "profiles": profiles,
        "samples": samples,
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
