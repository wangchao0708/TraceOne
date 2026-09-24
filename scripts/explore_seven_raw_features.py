#!/usr/bin/env python3
"""Development-only two-batch check for higher-dimensional number features."""

from __future__ import annotations

import json
import argparse
from collections import Counter
from pathlib import Path

import numpy as np

from traceone.adapter import adapter_feature, fit_ridge_adapter
from traceone.fingerprint import TARGET_MODELS, load_bank
from traceone.parsing import parse_grid_response
from traceone.support import classify_supported, fit_support


ROOT = Path(__file__).resolve().parents[1]
BASE = (
    "data/public/enrollment-v3.jsonl",
    "data/public/confirmation-v6.jsonl",
    "data/public/gpt6-enrollment-v1.jsonl",
)
BATCHES = ("data/public/confirmation-v8.jsonl", "data/public/confirmation-v9.jsonl")


def load(path: str) -> list[dict]:
    rows = []
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        parsed = parse_grid_response(row["text"])
        if not parsed.valid:
            raise ValueError(row["sample_id"])
        row["numbers"] = list(parsed.numbers)
        rows.append(row)
    return rows


def features(rows: list[dict], bank: dict) -> tuple[np.ndarray, np.ndarray]:
    bank_matrix = np.stack([adapter_feature(row["numbers"], bank) for row in rows])
    counts = np.stack([
        np.bincount(row["numbers"], minlength=356)[1:356] / 315
        for row in rows
    ])
    return bank_matrix, counts


def fit_predict(training: tuple[np.ndarray, np.ndarray], test: tuple[np.ndarray, np.ndarray],
                labels: np.ndarray, alpha: float, raw_weight: float) -> np.ndarray:
    train_bank, train_raw = training
    test_bank, test_raw = test
    train = np.concatenate((train_bank, train_raw), axis=1)
    held = np.concatenate((test_bank, test_raw), axis=1)
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale < 1e-12] = 1.0
    train = (train - mean) / scale
    held = (held - mean) / scale
    train[:, 48:] *= raw_weight
    held[:, 48:] *= raw_weight
    target = np.eye(len(TARGET_MODELS))[labels]
    target_mean = target.mean(axis=0)
    weight = np.linalg.solve(train.T @ train + alpha * np.eye(train.shape[1]),
                             train.T @ (target - target_mean))
    return held @ weight + target_mean


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    bank = load_bank()
    base = [row for path in BASE for row in load(path)]
    batches = {path: load(path) for path in BATCHES}
    variants = []
    for alpha in (1.0, 10.0, 100.0):
        for raw_weight in (0.0, 0.25, 0.5, 1.0):
            per_batch = {}
            errors = []
            for hold_path in BATCHES:
                training = base + [row for path, rows in batches.items() if path != hold_path for row in rows]
                held = batches[hold_path]
                label_index = np.array([TARGET_MODELS.index(row["requested_model"]) for row in training])
                scores = fit_predict(features(training, bank), features(held, bank),
                                     label_index, alpha, raw_weight)
                predictions = [TARGET_MODELS[index] for index in np.argmax(scores, axis=1)]
                per_batch[hold_path] = dict(Counter(
                    row["requested_model"] for row, guess in zip(held, predictions)
                    if row["requested_model"] == guess
                ))
                for row, guess in zip(held, predictions):
                    if guess != row["requested_model"]:
                        errors.append((row["sample_id"], row["requested_model"], guess))
            variants.append({"alpha": alpha, "raw_weight": raw_weight,
                             "matches": 210 - len(errors), "per_batch": per_batch,
                             "errors": errors})
    variants.sort(key=lambda value: (-value["matches"], value["raw_weight"], value["alpha"]))
    for row in variants:
        print(json.dumps({key: value for key, value in row.items() if key != "errors"}))
    print("best_errors", json.dumps(variants[0]["errors"]))
    supported_results = []
    for hold_path in BATCHES:
        training = base + [row for path, rows in batches.items() if path != hold_path for row in rows]
        held = batches[hold_path]
        labeled = [(row["requested_model"], row["numbers"]) for row in training]
        adapter = fit_ridge_adapter(labeled, bank, alpha=1.0,
                                    minimum_margin=0.01, raw_weight=0.25)
        support = fit_support(labeled, bank, adapter, rescue_margin_quantile=0.9)
        decisions = []
        for row in held:
            parsed = parse_grid_response(row["text"])
            result = classify_supported(parsed, bank=bank, adapter=adapter, support=support)
            decisions.append((row["sample_id"], row["requested_model"], result.label,
                              result.support_path, result.adapter.outer_guard.top_candidate))
        summary = {
            "holdout": hold_path,
            "matches": sum(truth == guess for _, truth, guess, _, _ in decisions),
            "per_model": {model: sum(truth == guess for _, truth, guess, _, _ in decisions
                                      if truth == model) for model in TARGET_MODELS},
            "errors": [row for row in decisions if row[1] != row[2]],
        }
        supported_results.append(summary)
        print("supported", json.dumps(summary))
    if args.output:
        payload = {
            "schema": "traceone-raw-feature-development-v1",
            "status": "development after confirmation-v9 failed; neither holdout is independent of hyperparameter selection",
            "design": "hold out confirmation-v8 or confirmation-v9 as a whole; fit on 581 earlier enrollment rows plus the other 105-row batch",
            "variants": variants,
            "supported_two_batch": supported_results,
        }
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
