#!/usr/bin/env python3
"""Reproduce the GPT-6.1 expansion development checks, never a blind confirmation."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from traceone.adapter import adapter_feature, fit_ridge_adapter, load_adapter
from traceone.fingerprint import ENROLLED_OUTER_GUARD, classify_parsed, load_bank
from traceone.parsing import parse_grid_response
from traceone.support import classify_supported, fit_support, identify_text_supported, load_support

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("gpt-5.5", "gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol",
          "gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-6.1-sol")
FROZEN_ADAPTER = ROOT / "src/traceone/data/codex_low_v7_adapter_791.json"
FROZEN_SUPPORT = ROOT / "src/traceone/data/codex_low_v7_support_791.json"
BASE_FILES = ("enrollment-v3", "confirmation-v6", "gpt6-enrollment-v1", "confirmation-v8", "confirmation-v9")
EXPECTED_COUNTS = {"gpt61-enrollment-v2": 113, "eight-development-v1": 120,
                   "pair-replacement-v1": 24, "pair-contexts-v1": 24,
                   "eight-web-pilot-v2": 16, "eight-replacement-v1": 192}


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def prepare(rows: list[dict]) -> list[dict]:
    for row in rows:
        parsed = parse_grid_response(row["text"] if row["return_code"] == 0 else "")
        row["numbers"] = list(parsed.numbers)
        row["valid"] = row["return_code"] == 0 and parsed.valid
        row["repeat"] = int(row["sample_id"].rsplit("__", 1)[1])
    return rows


def validate_corpus(rows: list[dict]) -> dict:
    if len({r["sample_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate sample IDs")
    counts = Counter(r["run_id"] for r in rows)
    if dict(counts) != EXPECTED_COUNTS:
        raise ValueError(f"unexpected cohort sizes: {counts}")
    if {r["runtime"] for r in rows} != {"codex-cli 0.159.2"}:
        raise ValueError("runtime drift")
    if any(r["reasoning_effort"] != "low" or r["provider"] != "openai-codex-subscription"
           or r["wrapper"] != "codex-exec-ephemeral-ignore-user-config-read-only" for r in rows):
        raise ValueError("collection conditions differ")
    expected_prompts = {"gpt61-enrollment-v2": "identity-v3-schema", "eight-development-v1": "identity-v3-schema",
                        "pair-replacement-v1": "identity-replacement-v1", "pair-contexts-v1": "identity-contexts-v1",
                        "eight-web-pilot-v2": "identity-web-v1", "eight-replacement-v1": "identity-replacement-v1"}
    schema_hash = hashlib.sha256((ROOT / "schemas/identity-v3.json").read_bytes()).hexdigest()
    for run_id, prompt_id in expected_prompts.items():
        prompt_hash = hashlib.sha256((ROOT / f"prompts/{prompt_id}.txt").read_text().strip().encode()).hexdigest()
        cohort = [r for r in rows if r["run_id"] == run_id]
        if any(r["prompt_id"] != prompt_id or r["prompt_sha256"] != prompt_hash for r in cohort):
            raise ValueError(f"prompt drift: {run_id}")
        wanted_schema = None if run_id == "eight-web-pilot-v2" else schema_hash
        if any(r["output_schema_sha256"] != wanted_schema for r in cohort):
            raise ValueError(f"schema drift: {run_id}")
        if any("thread_id" in r or "stderr_tail" in r for r in cohort):
            raise ValueError("private log fields in public export")
        labels = {"gpt-6.1-sol"} if run_id == "gpt61-enrollment-v2" else set(MODELS)
        if run_id.startswith("pair-"):
            labels = {"gpt-6-astra", "gpt-6.1-sol"}
        by_model = Counter(r["requested_model"] for r in cohort)
        if set(by_model) != labels or len(set(by_model.values())) != 1:
            raise ValueError(f"unbalanced cohort: {run_id}")
    return {"rows": len(rows), "cohort_counts": dict(counts), "unique_sample_ids": len(rows),
            "runtime": "codex-cli 0.159.2", "strict_format_compliant": sum(r["valid"] for r in rows),
            "successful_calls": sum(r["return_code"] == 0 for r in rows),
            "time_bounds_utc": [min(r["collected_at"] for r in rows), max(r["collected_at"] for r in rows)]}


def summarize(rows: list[dict], predictions: list[str | None], models=MODELS) -> dict:
    per_model = {}
    for model in models:
        indices = [i for i, row in enumerate(rows) if row["requested_model"] == model]
        matches = sum(predictions[i] == model for i in indices)
        per_model[model] = {"samples": len(indices), "matches": matches, "match_rate": matches / len(indices),
                            "unknown": sum(predictions[i] is None for i in indices)}
    return {"samples": len(rows), "matches": sum(v["matches"] for v in per_model.values()),
            "per_model": per_model,
            "errors": [{"sample_id": row["sample_id"], "requested_model": row["requested_model"], "prediction": prediction}
                       for row, prediction in zip(rows, predictions) if row["requested_model"] != prediction]}


def original_checks(rows: list[dict], bank: dict) -> dict:
    current = [r for r in rows if r["run_id"] == "eight-development-v1"]
    base = prepare([r for name in BASE_FILES for r in read_rows(ROOT / f"data/public/{name}.jsonl")])
    base += [r for r in rows if r["run_id"] == "gpt61-enrollment-v2"]
    if Counter(r["requested_model"] for r in base) != Counter({m: 113 for m in MODELS}):
        raise ValueError("original-prompt enrollment must be 113 per model")
    if not all(r["valid"] for r in base + current):
        raise ValueError("invalid original-prompt enrollment")
    legacy_adapter, legacy_support = load_adapter(FROZEN_ADAPTER), load_support(FROZEN_SUPPORT)
    frozen_seven = summarize(current, [identify_text_supported(r["text"], bank=bank,
                                adapter=legacy_adapter, support=legacy_support).label for r in current])
    variants = []
    for alpha in (1.0, 10.0, 100.0):
        predictions = [None] * len(current)
        for fold in range(3):
            held = [i for i, r in enumerate(current) if r["repeat"] % 3 == fold]
            training = base + [r for i, r in enumerate(current) if i not in held]
            labeled = [(r["requested_model"], r["numbers"]) for r in training]
            adapter = fit_ridge_adapter(labeled, bank, models=MODELS, alpha=alpha, minimum_margin=.01, raw_weight=.25)
            support = fit_support(labeled, bank, adapter, rescue_margin_quantile=.9)
            for i in held:
                predictions[i] = classify_supported(parse_grid_response(current[i]["text"]), bank=bank,
                                                     adapter=adapter, support=support).label
        variants.append({"alpha": alpha, "raw_weight": .25, **summarize(current, predictions)})
    return {"status": "development only; current rows and all variants were inspected",
            "bank": "unchanged upstream 16-model feature bank; no appended gpt-6.1-sol centroid",
            "folds": "repeat modulo 3; 113 base rows per model always remain in training",
            "provenance_limit": "base rows for the old seven use older runtimes; not a concurrent eight-model reference bank",
            "decision_rule": "outer guard + eight-class ridge + support, with the v11 hyperparameters except the listed alpha",
            "frozen_seven_v11": frozen_seven, "eight_class_variants": variants}


def structure(numbers: list[int]) -> np.ndarray:
    values = np.asarray(numbers, dtype=float)
    pieces = []
    for block in [values] + list(np.array_split(values, 9)):
        differences = np.diff(block)
        pieces.extend([len(set(block)), block.mean(), block.std(), np.mean(abs(differences)),
                       np.mean(differences > 0), np.mean(block % 2 == 0), np.mean(block % 5 == 0), np.mean(block % 10 == 7)])
    counts = Counter(numbers)
    pieces.extend([sum(c >= i for c in counts.values()) for i in range(2, 7)])
    for lag in range(1, 9):
        pieces.extend([np.mean(values[:-lag] == values[lag:]),
                       np.mean((values[:-lag] - values.mean()) * (values[lag:] - values.mean()))])
    return np.asarray(pieces)


def cross_fit(rows: list[dict], features: np.ndarray, models: tuple[str, ...], spec: dict) -> list[str | None]:
    counts = Counter(r["requested_model"] for r in rows)
    count = next(iter(counts.values()))
    if len(set(counts.values())) != 1 or count % 3:
        raise ValueError("three balanced chronological folds are required")
    y = np.asarray([models.index(r["requested_model"]) for r in rows])
    predictions = [None] * len(rows)
    for fold in range(3):
        held = [i for i, r in enumerate(rows) if (r["repeat"] - 1) // (count // 3) == fold]
        train = [i for i, r in enumerate(rows) if i not in held and r["valid"]]
        xx, zz = features[train], features[held]
        if spec["kind"] == "prototype":
            centroids = np.stack([xx[y[train] == i].mean(0) for i in range(len(models))])
            scores = -((zz[:, None, :] - centroids[None, :, :]) ** 2).sum(2)
        else:
            if spec.get("standardize", True):
                center, scale = xx.mean(0), xx.std(0)
                scale[scale < 1e-12] = 1
                xx, zz = (xx - center) / scale, (zz - center) / scale
            targets = np.eye(len(models))[y[train]]
            target_mean = targets.mean(0)
            if spec["kind"] == "ridge":
                kernel, cross = xx @ xx.T, zz @ xx.T
            else:
                distances = np.maximum((xx * xx).sum(1)[:, None] + (xx * xx).sum(1)[None, :] - 2 * xx @ xx.T, 0)
                cross_distances = np.maximum((zz * zz).sum(1)[:, None] + (xx * xx).sum(1)[None, :] - 2 * zz @ xx.T, 0)
                median = np.median(distances[np.triu_indices(len(xx), 1)])
                kernel = np.exp(-spec.get("gamma", 1) * distances / median)
                cross = np.exp(-spec.get("gamma", 1) * cross_distances / median)
            scores = cross @ np.linalg.solve(kernel + spec["alpha"] * np.eye(len(xx)), targets - target_mean) + target_mean
        for i, guess in zip(held, np.argmax(scores, axis=1)):
            predictions[i] = models[int(guess)] if rows[i]["valid"] else None
    return predictions


def pair_checks(rows: list[dict]) -> list[dict]:
    models = ("gpt-6-astra", "gpt-6.1-sol")
    output = []
    for run_id in ("pair-replacement-v1", "pair-contexts-v1"):
        cohort = [r for r in rows if r["run_id"] == run_id]
        variants = []
        for per_row in (False, True):
            vectors = []
            for row in cohort:
                blocks = np.array_split(row["numbers"] if row["valid"] else [1] * 315, 9) if per_row else [row["numbers"]]
                vectors.append(np.concatenate([np.sqrt((np.bincount(b, minlength=356)[1:] + .1) / (len(b) + 35.5)) for b in blocks]))
            matrix = np.stack(vectors)
            specs = [{"kind": "prototype", "alpha": 0}, {"kind": "ridge", "alpha": 1}, {"kind": "ridge", "alpha": 10},
                     {"kind": "kernel", "alpha": .1, "standardize": False}, {"kind": "kernel", "alpha": 1, "standardize": False}]
            for spec in specs:
                variants.append({"per_row": per_row, "spec": spec,
                                 **summarize(cohort, cross_fit(cohort, matrix, models, spec), models)})
        variants.sort(key=lambda v: (-min(m["matches"] for m in v["per_model"].values()), -v["matches"]))
        for variant in variants[1:]:
            variant.pop("errors")
        output.append({"run_id": run_id, "status": "prompt/method selection only, 12 rows per route", "variants": variants})
    return output


def replacement_checks(rows: list[dict], bank: dict) -> dict:
    cohort = [r for r in rows if r["run_id"] == "eight-replacement-v1"]
    numbers = [r["numbers"] if r["valid"] else [1] * 315 for r in cohort]
    bank_size = 3 * len(bank["robust"]["model_order"])
    groups = {"bank": np.stack([adapter_feature(n, bank) for n in numbers]),
              "raw": np.stack([adapter_feature(n, bank, include_raw=True)[bank_size:] for n in numbers]),
              "structure": np.stack([structure(n) for n in numbers]),
              "hellinger": np.stack([np.sqrt((np.bincount(n, minlength=356)[1:] + .5) / (315 + 355 * .5)) for n in numbers])}
    outer = [classify_parsed(parse_grid_response(r["text"]), bank=bank, guard=ENROLLED_OUTER_GUARD).status == "identified" for r in cohort]
    variants = []
    for names in (("bank", "raw"), ("bank", "raw", "structure"), ("raw", "structure"), ("hellinger",), ("hellinger", "structure")):
        features = np.concatenate([groups[g] for g in names], axis=1)
        specs = [{"kind": "ridge", "alpha": a} for a in (1, 10, 100, 1000)]
        specs += [{"kind": "kernel", "alpha": a, "gamma": g} for a in (.1, 1) for g in (.25, 1, 4)]
        if names == ("hellinger",):
            specs.append({"kind": "prototype", "alpha": 0})
        for spec in specs:
            predictions = cross_fit(cohort, features, MODELS, spec)
            guarded = [p if passed else None for p, passed in zip(predictions, outer)]
            variants.append({"groups": names, "spec": spec, **summarize(cohort, predictions),
                             "with_existing_outer_guard": summarize(cohort, guarded)})
    variants.sort(key=lambda v: (-min(m["matches"] for m in v["per_model"].values()), -v["matches"]))
    for variant in variants[1:]:
        variant.pop("errors")
        variant["with_existing_outer_guard"].pop("errors")
    return {"status": "prompt/feature/hyperparameter selection; no independent confirmation or calibrated target-support for kernel variants",
            "folds": "three chronological folds of eight responses per route, 16 train and eight held per fold",
            "outer_guard_identified": sum(outer), "variants": variants}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data/public/gpt61-development-v1.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "data/gpt61-development-v1.json")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    rows = read_rows(args.input)
    quality = validate_corpus(prepare(rows))
    if args.verify_only:
        print(json.dumps(quality))
        return
    bank = load_bank(ROOT / "src/traceone/data/unified_bank_v2_16.json")
    pilot = [r for r in rows if r["run_id"] == "eight-web-pilot-v2"]
    payload = {"schema": "traceone-gpt61-development-v1", "status": "development only; eight-model release NOT qualified",
               "truth_limitation": "requested_model is a route/control-plane label, not independent attestation of served weights",
               "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(), "quality": quality,
               "implementation_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                     ("scripts/evaluate_gpt61_development.py", "src/traceone/adapter.py", "src/traceone/support.py",
                      "src/traceone/fingerprint.py", "src/traceone/parsing.py")},
               "original_prompt": original_checks(rows, bank), "pair_prompt_pilots": pair_checks(rows),
               "replacement_prompt": replacement_checks(rows, bank),
               "web_pilot": {"strict_format_compliant": sum(r["valid"] for r in pilot),
                             **summarize(pilot, [identify_text_supported(r["text"], bank=bank,
                                adapter=load_adapter(FROZEN_ADAPTER), support=load_support(FROZEN_SUPPORT)).label for r in pilot])},
               "publication_decision": "retain seven-model 315 default; do not enable an unqualified eighth prediction class"}
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "rows": len(rows), "eight_model_release_qualified": False}))


if __name__ == "__main__":
    main()
