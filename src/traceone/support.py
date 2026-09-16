"""Target-support rejection layered after the registered-model outer guard."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path

import numpy as np

from .adapter import (
    AdapterResult,
    adapter_feature,
    adapter_scores,
    classify_adapted,
    load_adapter,
)
from .fingerprint import ENROLLED_OUTER_GUARD, GuardConfig, TARGET_MODELS, load_bank
from .parsing import ParseResult, parse_grid_response, parse_identity_response


@dataclass(frozen=True)
class SupportResult:
    status: str
    label: str | None
    support_passed: bool | None
    support_distance: float | None
    support_threshold: float | None
    support_p_value: float | None
    support_path: str | None
    adapter: AdapterResult

    def to_dict(self) -> dict:
        return asdict(self)


def load_support(path: Path | None = None) -> dict:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    resource = files("traceone").joinpath("data/codex_low_v4_support_415.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def _quantile(values: np.ndarray, quantile: float) -> float:
    return float(np.quantile(values, quantile, method="higher"))


def fit_support(
    labeled_numbers: list[tuple[str, list[int]]],
    bank: dict,
    adapter: dict,
    *,
    covariance_shrinkage: float = 0.3,
    distance_quantile: float = 0.99,
    rescue_margin_quantile: float = 0.95,
) -> dict:
    if covariance_shrinkage <= 0:
        raise ValueError("covariance_shrinkage must be positive")
    if not 0 < distance_quantile <= 1 or not 0 < rescue_margin_quantile <= 1:
        raise ValueError("quantiles must be in (0, 1]")
    labels = [label for label, _ in labeled_numbers]
    if set(labels) != set(TARGET_MODELS):
        raise ValueError("training data must contain every target model")

    matrix = np.stack([adapter_feature(numbers, bank) for _, numbers in labeled_numbers])
    feature_mean = matrix.mean(axis=0)
    feature_scale = matrix.std(axis=0)
    feature_scale[feature_scale < 1e-12] = 1.0
    standardized = (matrix - feature_mean) / feature_scale
    target_indices = np.asarray([TARGET_MODELS.index(label) for label in labels])
    centroids = np.stack(
        [standardized[target_indices == index].mean(axis=0)
         for index in range(len(TARGET_MODELS))]
    )
    residuals = np.concatenate(
        [standardized[target_indices == index] - centroids[index]
         for index in range(len(TARGET_MODELS))]
    )
    covariance = residuals.T @ residuals / len(residuals)
    precision = np.linalg.inv(
        covariance + covariance_shrinkage * np.eye(covariance.shape[0])
    )
    own_residuals = standardized - centroids[target_indices]
    distances = np.einsum("ij,jk,ik->i", own_residuals, precision, own_residuals)

    all_scores = np.stack(
        [adapter_scores(numbers, bank, adapter) for _, numbers in labeled_numbers]
    )
    predictions = np.argmax(all_scores, axis=1)
    ordered = np.sort(all_scores, axis=1)
    margins = ordered[:, -1] - ordered[:, -2]
    distance_thresholds = []
    rescue_thresholds = []
    calibration_distances = []
    for index in range(len(TARGET_MODELS)):
        class_distances = distances[target_indices == index]
        correct_margins = margins[(target_indices == index) & (predictions == index)]
        if not len(correct_margins):
            raise ValueError(f"adapter has no correct row for {TARGET_MODELS[index]}")
        distance_thresholds.append(_quantile(class_distances, distance_quantile))
        rescue_thresholds.append(_quantile(correct_margins, rescue_margin_quantile))
        calibration_distances.append(sorted(float(value) for value in class_distances))

    return {
        "schema": "traceone-target-support-v1",
        "models": list(TARGET_MODELS),
        "bank_model_order": list(bank["robust"]["model_order"]),
        "feature": "registered-bank fused scores + marginal scores + absolute JS similarities",
        "training_rows": len(labeled_numbers),
        "covariance_shrinkage": covariance_shrinkage,
        "distance_quantile": distance_quantile,
        "rescue_margin_quantile": rescue_margin_quantile,
        "feature_mean": feature_mean.tolist(),
        "feature_scale": feature_scale.tolist(),
        "centroids": centroids.tolist(),
        "precision": precision.tolist(),
        "distance_thresholds": distance_thresholds,
        "rescue_margin_thresholds": rescue_thresholds,
        "calibration_distances": calibration_distances,
        "warning": "empirical support envelope; no distribution-free OOD guarantee",
    }


def support_score(numbers: list[int], label: str, bank: dict, artifact: dict) -> dict:
    if list(bank["robust"]["model_order"]) != list(artifact["bank_model_order"]):
        raise ValueError("support artifact and bank model order do not match")
    index = list(artifact["models"]).index(label)
    feature = adapter_feature(numbers, bank)
    standardized = (
        feature - np.asarray(artifact["feature_mean"], dtype=np.float64)
    ) / np.asarray(artifact["feature_scale"], dtype=np.float64)
    residual = standardized - np.asarray(artifact["centroids"][index], dtype=np.float64)
    precision = np.asarray(artifact["precision"], dtype=np.float64)
    distance = float(residual @ precision @ residual)
    threshold = float(artifact["distance_thresholds"][index])
    calibration = artifact["calibration_distances"][index]
    p_value = (1 + sum(value >= distance for value in calibration)) / (len(calibration) + 1)
    return {"distance": distance, "threshold": threshold, "p_value": p_value}


def classify_supported(
    parsed: ParseResult,
    *,
    bank: dict | None = None,
    adapter: dict | None = None,
    support: dict | None = None,
    guard: GuardConfig = ENROLLED_OUTER_GUARD,
) -> SupportResult:
    bank = bank or load_bank()
    adapter = adapter or load_adapter()
    base = classify_adapted(parsed, bank=bank, adapter=adapter, guard=guard)
    if base.status != "identified" or base.label is None:
        return SupportResult("unknown", None, None, None, None, None, None, base)
    support = support or load_support()
    score = support_score(list(parsed.numbers), base.label, bank, support)
    index = list(support["models"]).index(base.label)
    rescue_threshold = float(support["rescue_margin_thresholds"][index])
    distance_passed = score["distance"] <= score["threshold"]
    margin_rescue = bool(
        base.adapter_margin is not None and base.adapter_margin >= rescue_threshold
    )
    passed = distance_passed or margin_rescue
    path = "distance" if distance_passed else "high_margin_rescue" if margin_rescue else "rejected"
    return SupportResult(
        "identified" if passed else "unknown",
        base.label if passed else None,
        passed,
        score["distance"],
        score["threshold"],
        score["p_value"],
        path,
        base,
    )


def identify_text_supported(
    text: str,
    *,
    response_format: str = "grid",
    bank: dict | None = None,
    adapter: dict | None = None,
    support: dict | None = None,
    guard: GuardConfig = ENROLLED_OUTER_GUARD,
) -> SupportResult:
    if response_format == "grid":
        parsed = parse_grid_response(text)
    elif response_format == "flat":
        parsed = parse_identity_response(text)
    else:
        raise ValueError("response_format must be 'grid' or 'flat'")
    return classify_supported(parsed, bank=bank, adapter=adapter, support=support, guard=guard)
