#!/usr/bin/env python3
"""Compare small nonlinear target adapters with whole-collection holdouts."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

import numpy as np

from evaluate_adapter_cv import load_rows
from traceone.adapter import adapter_feature
from traceone.fingerprint import ENROLLED_OUTER_GUARD, TARGET_MODELS, classify_parsed, load_bank


def predict_knn(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray, k: int) -> int:
    distances = np.sum((train_x - test_x) ** 2, axis=1)
    nearest = np.argsort(distances)[:k]
    scores = np.zeros(len(TARGET_MODELS))
    for index in nearest:
        scores[train_y[index]] += 1.0 / (distances[index] + 1e-6)
    return int(np.argmax(scores))


def predict_centroid(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    shrinkage: float,
) -> int:
    centroids = np.stack(
        [train_x[train_y == index].mean(axis=0) for index in range(len(TARGET_MODELS))]
    )
    residuals = np.concatenate(
        [train_x[train_y == index] - centroids[index] for index in range(len(TARGET_MODELS))]
    )
    covariance = residuals.T @ residuals / len(residuals)
    diagonal = np.diag(np.diag(covariance))
    covariance = (1 - shrinkage) * covariance + shrinkage * diagonal
    precision = np.linalg.inv(covariance + 1e-6 * np.eye(covariance.shape[0]))
    delta = centroids - test_x
    distances = np.einsum("ij,jk,ik->i", delta, precision, delta)
    return int(np.argmin(distances))


def predict_rbf(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    gamma: float,
) -> int:
    distances = np.mean((train_x - test_x) ** 2, axis=1)
    weights = np.exp(-gamma * distances)
    scores = np.asarray(
        [weights[train_y == index].mean() for index in range(len(TARGET_MODELS))]
    )
    return int(np.argmax(scores))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    rows = load_rows()
    bank = load_bank()
    groups = list(dict.fromkeys(row["group"] for row in rows))
    methods = (
        [("knn", value) for value in (1, 3, 5, 9)]
        + [("lda", value) for value in (0.1, 0.3, 0.6, 1.0)]
        + [("rbf", value) for value in (0.3, 1.0, 3.0, 10.0)]
    )
    results: dict[str, list[dict]] = defaultdict(list)
    for held_group in groups:
        train = [row for row in rows if row["group"] != held_group]
        test = [row for row in rows if row["group"] == held_group]
        raw_train = np.stack([adapter_feature(row["numbers"], bank) for row in train])
        mean = raw_train.mean(axis=0)
        scale = raw_train.std(axis=0)
        scale[scale < 1e-12] = 1.0
        train_x = (raw_train - mean) / scale
        train_y = np.asarray([TARGET_MODELS.index(row["truth"]) for row in train])
        for row in test:
            outer = classify_parsed(row["parsed"], bank=bank, guard=ENROLLED_OUTER_GUARD)
            test_x = (adapter_feature(row["numbers"], bank) - mean) / scale
            for family, parameter in methods:
                if outer.status != "identified":
                    prediction = None
                elif family == "knn":
                    prediction = predict_knn(train_x, train_y, test_x, int(parameter))
                elif family == "lda":
                    prediction = predict_centroid(train_x, train_y, test_x, parameter)
                else:
                    prediction = predict_rbf(train_x, train_y, test_x, parameter)
                label = None if prediction is None else TARGET_MODELS[prediction]
                results[f"{family}:{parameter}"].append(
                    {
                        "held_group": held_group,
                        "sample_id": row["sample_id"],
                        "truth": row["truth"],
                        "label": label,
                        "correct": label == row["truth"],
                    }
                )

    summary = []
    for method, decisions in results.items():
        correct = sum(row["correct"] for row in decisions)
        errors = [row for row in decisions if not row["correct"]]
        summary.append(
            {
                "method": method,
                "correct": correct,
                "samples": len(decisions),
                "errors_per_group": dict(Counter(row["held_group"] for row in errors)),
                "errors": errors,
            }
        )
    summary.sort(key=lambda item: (-item["correct"], item["method"]))
    rendered = json.dumps(
        {"schema": "traceone-adapter-exploration-v1", "results": summary}, indent=2
    ) + "\n"
    if args.output:
        from pathlib import Path

        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
