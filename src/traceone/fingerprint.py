"""Single-response guarded fingerprinting.

The feature extractor is a compatible, attributed adaptation of ModelTrace's
MIT-licensed ``fingerprint.py`` at commit 3f0dd2f.  TraceOne adds an open-set
guard, channel agreement, absolute similarity thresholds, and abstention.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Iterable

import numpy as np

from .parsing import ParseResult, parse_grid_response, parse_identity_response


VALUE_MIN = 1
VALUE_MAX = 355
DIMENSION = VALUE_MAX - VALUE_MIN + 1
ALPHA = 0.5
TARGET_MODELS = (
    "gpt-5.5",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
    "gpt-6-astra",
)


@dataclass(frozen=True)
class GuardConfig:
    name: str
    minimum_numbers: int
    minimum_similarity: float
    minimum_margin: float
    require_channel_agreement: bool = True
    allow_marginal_fallback: bool = False
    fallback_minimum_similarity: float = 1.0
    fallback_minimum_margin: float = 1.0
    fallback_maximum_fused_gap: float = 0.0


BALANCED_GUARD = GuardConfig(
    name="balanced-development-v1",
    minimum_numbers=280,
    minimum_similarity=0.53,
    minimum_margin=0.025,
    require_channel_agreement=False,
)
STRICT_GUARD = GuardConfig(
    name="strict-development-v1",
    minimum_numbers=280,
    minimum_similarity=0.5525,
    minimum_margin=0.1428,
)
ADAPTIVE_GUARD = GuardConfig(
    name="adaptive-development-v1",
    minimum_numbers=280,
    minimum_similarity=0.52,
    minimum_margin=0.025,
    require_channel_agreement=False,
    allow_marginal_fallback=True,
    fallback_minimum_similarity=0.54,
    fallback_minimum_margin=0.10,
    fallback_maximum_fused_gap=0.075,
)
ENROLLED_OUTER_GUARD = GuardConfig(
    name="enrolled-outer-v2",
    minimum_numbers=280,
    minimum_similarity=0.52,
    minimum_margin=0.0,
    require_channel_agreement=False,
    allow_marginal_fallback=True,
    fallback_minimum_similarity=0.54,
    fallback_minimum_margin=0.10,
    fallback_maximum_fused_gap=0.075,
)


@dataclass(frozen=True)
class CandidateScore:
    model: str
    fused_score: float
    marginal_score: float
    profile_similarity: float
    closed_set_probability: float


@dataclass(frozen=True)
class IdentityResult:
    status: str
    label: str | None
    top_candidate: str | None
    marginal_candidate: str | None
    usable_numbers: int
    format_compliant: bool
    parse_errors: tuple[str, ...]
    guard_reasons: tuple[str, ...]
    similarity: float | None
    score_margin: float | None
    marginal_score_margin: float | None
    decision_path: str | None
    guard_profile: str
    candidates: tuple[CandidateScore, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def load_bank(path: Path | None = None) -> dict:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    resource = files("traceone").joinpath("data/unified_bank.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def count_numbers(numbers: Iterable[int]) -> list[int]:
    counts = [0] * DIMENSION
    for number in numbers:
        if not VALUE_MIN <= number <= VALUE_MAX:
            raise ValueError(f"number outside {VALUE_MIN}..{VALUE_MAX}: {number}")
        counts[number - VALUE_MIN] += 1
    return counts


def _standardize(values: Iterable[float]) -> np.ndarray:
    vector = np.asarray(list(values), dtype=np.float64)
    scale = max(float(vector.std()), 1e-12)
    return (vector - float(vector.mean())) / scale


def hellinger_feature(counts: list[int]) -> np.ndarray:
    values = np.asarray(counts, dtype=np.float64) + ALPHA
    return np.sqrt(values / values.sum())


def ordered_block_feature(numbers: list[int]) -> np.ndarray:
    values = np.asarray(numbers, dtype=np.float64)
    pieces: list[np.ndarray] = []
    for chunk in np.array_split(values, 4):
        counts, _ = np.histogram(chunk, bins=16, range=(1.0, 356.0))
        smoothed = counts.astype(np.float64) + 0.5
        pieces.append(np.sqrt(smoothed / smoothed.sum()))
    last_digits = np.bincount(values.astype(int) % 10, minlength=10).astype(np.float64) + 0.5
    pieces.append(np.sqrt(last_digits / last_digits.sum()))
    return np.concatenate(pieces)


def _marginal_scores(counts: list[int], bank: dict) -> np.ndarray:
    artifact = bank["robust"]["hellinger"]
    projected = (
        hellinger_feature(counts)
        - np.asarray(artifact["feature_mean"], dtype=np.float64)
    ) / np.asarray(artifact["feature_scale"], dtype=np.float64)
    basis = np.asarray(artifact["nuisance_basis"], dtype=np.float64)
    if basis.size:
        projected -= (projected @ basis.T) @ basis
    projected /= max(float(np.linalg.norm(projected)), 1e-12)
    centroids = np.asarray(artifact["centroids"], dtype=np.float64)
    return _standardize(projected @ centroids.T)


def _ordered_scores(numbers: list[int], bank: dict) -> np.ndarray:
    artifact = bank["robust"]["ordered_blocks"]
    feature = ordered_block_feature(numbers)
    standardized = (
        feature - np.asarray(artifact["feature_mean"], dtype=np.float64)
    ) / np.asarray(artifact["feature_scale"], dtype=np.float64)

    normalized = standardized / max(float(np.linalg.norm(standardized)), 1e-12)
    templates = np.asarray(artifact["environment_centroids"], dtype=np.float64)
    environment_scores = np.stack([normalized @ centroids.T for centroids in templates])
    template_scores = _standardize(np.max(environment_scores, axis=0))

    basis = np.asarray(artifact["nuisance_basis"], dtype=np.float64)
    projected = standardized.copy()
    if basis.size:
        projected -= (projected @ basis.T) @ basis
    projected /= max(float(np.linalg.norm(projected)), 1e-12)
    centroids = np.asarray(artifact["centroids"], dtype=np.float64)
    nuisance_scores = _standardize(projected @ centroids.T)
    return _standardize(0.5 * template_scores + 0.5 * nuisance_scores)


def score_numbers(numbers: list[int], bank: dict) -> tuple[np.ndarray, np.ndarray]:
    if not numbers:
        raise ValueError("at least one number is required")
    marginal = _marginal_scores(count_numbers(numbers), bank)
    ordered_artifact = bank["robust"].get("ordered_blocks")
    weight = float(ordered_artifact.get("weight", 0.0)) if ordered_artifact else 0.0
    if not ordered_artifact or weight == 0.0:
        return marginal, marginal
    ordered = _ordered_scores(numbers, bank)
    fused = (1.0 - weight) * marginal + weight * ordered
    return fused, marginal


def _softmax(values: np.ndarray) -> np.ndarray:
    shifted = values - float(values.max())
    weights = np.exp(shifted)
    return weights / weights.sum()


def js_similarity(left: list[int], right: list[int]) -> float:
    left_total = sum(left)
    if left_total == 0:
        return 0.0
    right_total = sum(right) + ALPHA * DIMENSION
    p = np.asarray(left, dtype=np.float64) / left_total
    q = (np.asarray(right, dtype=np.float64) + ALPHA) / right_total
    midpoint = (p + q) / 2.0
    left_mask = p > 0
    divergence_left = float(np.sum(p[left_mask] * np.log(p[left_mask] / midpoint[left_mask])))
    divergence_right = float(np.sum(q * np.log(q / midpoint)))
    divergence = (divergence_left + divergence_right) / 2.0
    return 1.0 - math.sqrt(divergence / math.log(2.0))


def classify_parsed(
    parsed: ParseResult,
    *,
    bank: dict | None = None,
    guard: GuardConfig = BALANCED_GUARD,
) -> IdentityResult:
    bank = bank or load_bank()
    reasons: list[str] = []
    if len(parsed.numbers) < guard.minimum_numbers:
        reasons.append("insufficient_usable_numbers")
        return IdentityResult(
            status="unknown",
            label=None,
            top_candidate=None,
            marginal_candidate=None,
            usable_numbers=len(parsed.numbers),
            format_compliant=parsed.valid,
            parse_errors=parsed.errors,
            guard_reasons=tuple(reasons),
            similarity=None,
            score_margin=None,
            marginal_score_margin=None,
            decision_path=None,
            guard_profile=guard.name,
            candidates=(),
        )

    model_ids = list(bank["robust"]["model_order"])
    models = {model["id"]: model for model in bank["models"]}
    fused, marginal = score_numbers(list(parsed.numbers), bank)
    beta = float(bank.get("calibration", {}).get("1", {}).get("beta", 1.0))
    probabilities = _softmax(beta * fused)
    counts = count_numbers(parsed.numbers)
    candidates = [
        CandidateScore(
            model=model_id,
            fused_score=float(fused[index]),
            marginal_score=float(marginal[index]),
            profile_similarity=js_similarity(counts, models[model_id]["counts"]),
            closed_set_probability=float(probabilities[index]),
        )
        for index, model_id in enumerate(model_ids)
    ]
    candidates.sort(key=lambda item: item.fused_score, reverse=True)
    top = candidates[0]
    margin = top.fused_score - candidates[1].fused_score
    marginal_order = sorted(range(len(model_ids)), key=lambda index: marginal[index], reverse=True)
    marginal_candidate = model_ids[marginal_order[0]]
    marginal_margin = float(marginal[marginal_order[0]] - marginal[marginal_order[1]])
    candidate_by_model = {candidate.model: candidate for candidate in candidates}

    fallback_label = None
    if (
        guard.allow_marginal_fallback
        and top.model not in TARGET_MODELS
        and marginal_candidate in TARGET_MODELS
        and candidate_by_model[marginal_candidate].profile_similarity
        >= guard.fallback_minimum_similarity
        and marginal_margin >= guard.fallback_minimum_margin
        and margin <= guard.fallback_maximum_fused_gap
    ):
        fallback_label = marginal_candidate

    if top.model not in TARGET_MODELS and fallback_label is None:
        reasons.append("guard_model_won")
    if guard.require_channel_agreement and top.model != marginal_candidate:
        reasons.append("feature_channel_disagreement")
    if fallback_label is None and top.profile_similarity < guard.minimum_similarity:
        reasons.append("low_absolute_similarity")
    if fallback_label is None and margin < guard.minimum_margin:
        reasons.append("low_score_margin")

    label = fallback_label or (top.model if not reasons else None)
    selected_similarity = (
        candidate_by_model[label].profile_similarity if label is not None else top.profile_similarity
    )
    return IdentityResult(
        status="identified" if label else "unknown",
        label=label,
        top_candidate=top.model,
        marginal_candidate=marginal_candidate,
        usable_numbers=len(parsed.numbers),
        format_compliant=parsed.valid,
        parse_errors=parsed.errors,
        guard_reasons=tuple(reasons),
        similarity=selected_similarity,
        score_margin=margin,
        marginal_score_margin=marginal_margin,
        decision_path=("marginal_fallback" if fallback_label else "fused") if label else None,
        guard_profile=guard.name,
        candidates=tuple(candidates),
    )


def identify_text(
    text: str,
    *,
    response_format: str = "grid",
    bank: dict | None = None,
    guard: GuardConfig = BALANCED_GUARD,
) -> IdentityResult:
    if response_format == "grid":
        parsed = parse_grid_response(text)
    elif response_format == "flat":
        parsed = parse_identity_response(text)
    else:
        raise ValueError("response_format must be 'grid' or 'flat'")
    return classify_parsed(parsed, bank=bank, guard=guard)
