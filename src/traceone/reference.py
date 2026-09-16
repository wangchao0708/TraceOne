"""Reference-data fitting helpers for reproducible grouped evaluation.

This module adapts ModelTrace's MIT-licensed ``bank_builder.py`` at commit
3f0dd2f.  It exists so evaluation can refit artifacts without the held-out
environment instead of scoring a row against a bank that already saw it.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from .fingerprint import (
    DIMENSION,
    count_numbers,
    hellinger_feature,
    ordered_block_feature,
)
from .parsing import VALUE_MAX, VALUE_MIN


ORDERED_BLOCK_WEIGHT = 0.25


def _extract_longest_numeric_run(text: str) -> list[int]:
    """Compatibility parser used only for the imported ModelTrace corpus."""
    import re

    runs: list[list[int]] = []
    current: list[int] = []
    previous_end = 0
    for match in re.finditer(r"\d+", text):
        separator = text[previous_end : match.start()]
        value = int(match.group())
        if current and any(character.isalpha() for character in separator):
            runs.append(current)
            current = []
        if VALUE_MIN <= value <= VALUE_MAX:
            current.append(value)
        previous_end = match.end()
    if current:
        runs.append(current)
    return max(runs, key=len) if runs else []


def read_reference_rows(path: Path, *, family: str) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not row.get("strict_valid"):
            continue
        numbers = _extract_longest_numeric_run(row["text"])
        rows.append(
            {
                **row,
                "family_id": family,
                "numbers": numbers,
                "counts": count_numbers(numbers),
            }
        )
    return rows


def fit_robust_artifacts(rows: list[dict], model_ids: list[str]) -> dict:
    environments = sorted({row["condition_id"] for row in rows})
    complete = [
        environment
        for environment in environments
        if {row["source"] for row in rows if row["condition_id"] == environment}
        == set(model_ids)
    ]
    robust_rows = [row for row in rows if row["condition_id"] in complete] if complete else rows

    features = np.stack([hellinger_feature(row["counts"]) for row in robust_rows])
    feature_mean = features.mean(axis=0)
    feature_scale = features.std(axis=0)
    feature_scale[feature_scale < 1e-12] = 1.0
    standardized = (features - feature_mean) / feature_scale

    nuisance_environments = sorted(
        {row.get("nuisance_condition_id", row["condition_id"]) for row in robust_rows}
    )
    environment_means = []
    for environment in nuisance_environments:
        indices = np.asarray(
            [
                row.get("nuisance_condition_id", row["condition_id"]) == environment
                for row in robust_rows
            ],
            dtype=bool,
        )
        environment_means.append(standardized[indices].mean(axis=0))
    offsets = np.stack(environment_means)
    offsets -= offsets.mean(axis=0, keepdims=True)
    basis = np.empty((0, DIMENSION), dtype=np.float64)
    if len(offsets) > 1:
        _, singular, right = np.linalg.svd(offsets, full_matrices=False)
        rank = min(2, int(np.sum(singular > singular[0] * 1e-8))) if singular[0] else 0
        basis = right[:rank]
        standardized -= (standardized @ basis.T) @ basis

    labels = np.asarray([row["source"] for row in robust_rows])
    centroids = np.stack(
        [standardized[labels == model_id].mean(axis=0) for model_id in model_ids]
    )
    centroids /= np.maximum(np.linalg.norm(centroids, axis=1, keepdims=True), 1e-12)

    ordered_features = np.stack(
        [ordered_block_feature(row["numbers"]) for row in robust_rows]
    )
    ordered_mean = ordered_features.mean(axis=0)
    ordered_scale = ordered_features.std(axis=0)
    ordered_scale[ordered_scale < 1e-12] = 1.0
    ordered_standardized = (ordered_features - ordered_mean) / ordered_scale
    ordered_environment_means = []
    for environment in nuisance_environments:
        indices = np.asarray(
            [
                row.get("nuisance_condition_id", row["condition_id"]) == environment
                for row in robust_rows
            ],
            dtype=bool,
        )
        ordered_environment_means.append(ordered_standardized[indices].mean(axis=0))
    ordered_offsets = np.stack(ordered_environment_means)
    ordered_offsets -= ordered_offsets.mean(axis=0, keepdims=True)
    ordered_basis = np.empty((0, ordered_standardized.shape[1]), dtype=np.float64)
    if len(ordered_offsets) > 1:
        _, singular, right = np.linalg.svd(ordered_offsets, full_matrices=False)
        rank = min(2, int(np.sum(singular > singular[0] * 1e-8))) if singular[0] else 0
        ordered_basis = right[:rank]
        ordered_standardized -= (ordered_standardized @ ordered_basis.T) @ ordered_basis
    ordered_centroids = np.stack(
        [ordered_standardized[labels == model_id].mean(axis=0) for model_id in model_ids]
    )
    ordered_centroids /= np.maximum(
        np.linalg.norm(ordered_centroids, axis=1, keepdims=True), 1e-12
    )

    unprojected_ordered = (ordered_features - ordered_mean) / ordered_scale
    ordered_environment_centroids = []
    for environment in complete or [None]:
        environment_centroids = []
        for model_id in model_ids:
            indices = np.asarray(
                [
                    (environment is None or row["condition_id"] == environment)
                    and row["source"] == model_id
                    for row in robust_rows
                ],
                dtype=bool,
            )
            centroid = unprojected_ordered[indices].mean(axis=0)
            centroid /= max(float(np.linalg.norm(centroid)), 1e-12)
            environment_centroids.append(centroid)
        ordered_environment_centroids.append(np.stack(environment_centroids))

    return {
        "model_order": model_ids,
        "robust_ready": bool(complete),
        "training_rows": len(robust_rows),
        "complete_environments": complete,
        "hellinger": {
            "feature_mean": feature_mean.tolist(),
            "feature_scale": feature_scale.tolist(),
            "nuisance_rank": len(basis),
            "nuisance_environments": nuisance_environments,
            "nuisance_basis": basis.tolist(),
            "centroids": centroids.tolist(),
        },
        "ordered_blocks": {
            "weight": ORDERED_BLOCK_WEIGHT,
            "feature_mean": ordered_mean.tolist(),
            "feature_scale": ordered_scale.tolist(),
            "nuisance_rank": len(ordered_basis),
            "nuisance_basis": ordered_basis.tolist(),
            "centroids": ordered_centroids.tolist(),
            "environment_centroids": [
                item.tolist() for item in ordered_environment_centroids
            ],
        },
    }


def build_scoring_bank(rows: list[dict], model_ids: list[str]) -> dict:
    models = []
    for model_id in model_ids:
        selected = [row for row in rows if row["source"] == model_id]
        pooled = [
            sum(row["counts"][index] for row in selected) for index in range(DIMENSION)
        ]
        models.append(
            {
                "id": model_id,
                "display_name": model_id,
                "family": selected[0].get("family_id"),
                "response_count": len(selected),
                "conditions": dict(Counter(row["condition_id"] for row in selected)),
                "counts": pooled,
            }
        )
    return {
        "schema": "traceone-evaluation-bank-v1",
        "models": models,
        "robust": fit_robust_artifacts(rows, model_ids),
        "calibration": {"1": {"beta": 1.0}},
    }
