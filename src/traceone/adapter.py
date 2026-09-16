"""Current-wrapper enrollment adapter layered behind the open-set guard."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path

import numpy as np

from .fingerprint import (
    ENROLLED_OUTER_GUARD,
    GuardConfig,
    IdentityResult,
    TARGET_MODELS,
    classify_parsed,
    count_numbers,
    js_similarity,
    load_bank,
    score_numbers,
)
from .parsing import ParseResult, parse_grid_response, parse_identity_response


@dataclass(frozen=True)
class AdapterResult:
    status: str
    label: str | None
    adapter_margin: float | None
    adapter_scores: dict[str, float]
    outer_guard: IdentityResult

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "label": self.label,
            "adapter_margin": self.adapter_margin,
            "adapter_scores": self.adapter_scores,
            "outer_guard": self.outer_guard.to_dict(),
        }


def load_adapter(path: Path | None = None) -> dict:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    resource = files("traceone").joinpath("data/codex_low_v4_adapter_415.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def adapter_feature(numbers: list[int], bank: dict) -> np.ndarray:
    model_ids = list(bank["robust"]["model_order"])
    entries = {entry["id"]: entry for entry in bank["models"]}
    fused, marginal = score_numbers(numbers, bank)
    counts = count_numbers(numbers)
    similarities = np.asarray(
        [js_similarity(counts, entries[model_id]["counts"]) for model_id in model_ids],
        dtype=np.float64,
    )
    return np.concatenate((fused, marginal, similarities))


def fit_ridge_adapter(
    labeled_numbers: list[tuple[str, list[int]]],
    bank: dict,
    *,
    alpha: float = 10.0,
    minimum_margin: float = 0.05,
) -> dict:
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    labels = [label for label, _ in labeled_numbers]
    if set(labels) != set(TARGET_MODELS):
        raise ValueError("training data must contain every target model")
    matrix = np.stack([adapter_feature(numbers, bank) for _, numbers in labeled_numbers])
    mean = matrix.mean(axis=0)
    scale = matrix.std(axis=0)
    scale[scale < 1e-12] = 1.0
    standardized = (matrix - mean) / scale
    targets = np.asarray(
        [[float(label == model) for model in TARGET_MODELS] for label in labels],
        dtype=np.float64,
    )
    target_mean = targets.mean(axis=0)
    regularized = standardized.T @ standardized + alpha * np.eye(standardized.shape[1])
    weights = np.linalg.solve(regularized, standardized.T @ (targets - target_mean))
    return {
        "schema": "traceone-ridge-adapter-v1",
        "models": list(TARGET_MODELS),
        "bank_model_order": list(bank["robust"]["model_order"]),
        "feature": "fused scores + marginal scores + absolute JS similarities",
        "alpha": alpha,
        "minimum_margin": minimum_margin,
        "training_rows": len(labeled_numbers),
        "feature_mean": mean.tolist(),
        "feature_scale": scale.tolist(),
        "target_mean": target_mean.tolist(),
        "weights": weights.tolist(),
    }


def adapter_scores(numbers: list[int], bank: dict, adapter: dict) -> np.ndarray:
    if list(bank["robust"]["model_order"]) != list(adapter["bank_model_order"]):
        raise ValueError("adapter and bank model order do not match")
    feature = adapter_feature(numbers, bank)
    standardized = (
        feature - np.asarray(adapter["feature_mean"], dtype=np.float64)
    ) / np.asarray(adapter["feature_scale"], dtype=np.float64)
    return standardized @ np.asarray(adapter["weights"], dtype=np.float64) + np.asarray(
        adapter["target_mean"], dtype=np.float64
    )


def classify_adapted(
    parsed: ParseResult,
    *,
    bank: dict | None = None,
    adapter: dict | None = None,
    guard: GuardConfig = ENROLLED_OUTER_GUARD,
) -> AdapterResult:
    bank = bank or load_bank()
    outer = classify_parsed(parsed, bank=bank, guard=guard)
    if outer.status != "identified":
        return AdapterResult("unknown", None, None, {}, outer)
    adapter = adapter or load_adapter()
    scores = adapter_scores(list(parsed.numbers), bank, adapter)
    order = np.argsort(scores)
    margin = float(scores[order[-1]] - scores[order[-2]])
    model_ids = list(adapter["models"])
    label = model_ids[int(order[-1])]
    score_map = {model: float(scores[index]) for index, model in enumerate(model_ids)}
    if margin < float(adapter["minimum_margin"]):
        return AdapterResult("unknown", None, margin, score_map, outer)
    return AdapterResult("identified", label, margin, score_map, outer)


def identify_text_adapted(
    text: str,
    *,
    response_format: str = "grid",
    bank: dict | None = None,
    adapter: dict | None = None,
    guard: GuardConfig = ENROLLED_OUTER_GUARD,
) -> AdapterResult:
    if response_format == "grid":
        parsed = parse_grid_response(text)
    elif response_format == "flat":
        parsed = parse_identity_response(text)
    else:
        raise ValueError("response_format must be 'grid' or 'flat'")
    return classify_adapted(parsed, bank=bank, adapter=adapter, guard=guard)
