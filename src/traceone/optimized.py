"""Eight-route 315-choice experiment, building on ModelTrace bank features.

The new prompt permits repetition explicitly. Bank scores are features and
diagnostics, not a closed-set veto on the newly enrolled GPT-6.1 Sol route.
An independently calibrated target-support gate retains abstention.
"""
from __future__ import annotations

import json
from collections import Counter
from importlib.resources import files
from pathlib import Path

import numpy as np

from .adapter import AdapterResult, adapter_feature
from .fingerprint import ENROLLED_OUTER_GUARD, classify_parsed, load_bank
from .parsing import parse_grid_response
from .support import SupportResult

EIGHT_TARGET_MODELS = ("gpt-5.5", "gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol",
                       "gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-6.1-sol")
GROUP_ORDER = ("bank", "raw", "structure", "order")


def sequence_structure(numbers: list[int]) -> np.ndarray:
    if not 280 <= len(numbers) <= 350:
        raise ValueError("optimized features require 280–350 usable integers")
    x = np.asarray(numbers, dtype=float)
    out = []
    for b in [x] + list(np.array_split(x, 9)) + [x[:n] for n in (70, 140, 210, 280)]:
        counts = np.bincount(b.astype(int), minlength=356)[1:]
        delta = np.diff(b)
        out.extend([len(set(b))/len(b), counts.max(), (counts*counts).sum()/len(b),
                    b.mean()/355, b.std()/355, np.mean(abs(delta))/355,
                    np.mean(delta > 0), np.mean(abs(delta) <= 10),
                    np.mean(b % 2 == 0), np.mean(b % 5 == 0), np.mean(b % 10 == 7)])
    counts = Counter(numbers)
    out.extend([sum(c >= i for c in counts.values()) for i in range(2, 7)])
    out.extend([sum(c == i for c in counts.values()) for i in range(1, 6)])
    for lag in range(1, 9):
        out.extend([np.mean(x[:-lag] == x[lag:]), np.mean(abs(x[:-lag]-x[lag:]))/355,
                    np.mean((x[:-lag]-x.mean())*(x[lag:]-x.mean()))/355**2])
    return np.asarray(out)


def feature_groups(numbers: list[int], bank: dict) -> dict[str, np.ndarray]:
    x = np.asarray(numbers)
    sequence = sequence_structure(numbers)
    blocks = np.array_split(x, 9)
    digit = np.concatenate([np.bincount(b % 10, minlength=10)/len(b) for b in blocks])
    bins = np.minimum((x-1)*6//355, 5)
    transitions = np.bincount(bins[:-1]*6+bins[1:], minlength=36)/(len(x)-1)
    positions = np.concatenate([np.bincount(np.minimum((b-1)*8//355, 7), minlength=8)/len(b)
                                for b in blocks])
    full = adapter_feature(numbers, bank, include_raw=True)
    boundary = 3*len(bank["robust"]["model_order"])
    return {"bank": full[:boundary], "raw": full[boundary:], "structure": sequence,
            "order": np.concatenate((digit, transitions, positions))}


def feature_vector(numbers: list[int], bank: dict, weights: dict) -> np.ndarray:
    groups = feature_groups(numbers, bank)
    return np.concatenate([groups[name] for name in GROUP_ORDER if weights.get(name, 0) > 0])


def _support_feature(numbers: list[int], bank: dict) -> np.ndarray:
    # Compact 73-dimensional envelope: bank scores, global and row repetition,
    # and repeat-frequency tails. No high-margin bypass of this gate.
    groups = feature_groups(numbers, bank)
    s = groups["structure"]
    return np.concatenate((groups["bank"], s[:11], s[11:110:11], s[154:159]))


def fit_optimized(training: list[tuple[str, list[int]]], calibration: list[tuple[str, list[int]]],
                  bank: dict, *, group_weights: dict, alpha: float = 1,
                  minimum_margin: float = .01, covariance_shrinkage: float = .3,
                  classifier: str = "ridge", gamma: float = 1) -> dict:
    if alpha <= 0 or covariance_shrinkage <= 0 or minimum_margin < 0:
        raise ValueError("invalid fit parameters")
    if classifier not in {"ridge", "kernel"} or gamma <= 0:
        raise ValueError("invalid classifier parameters")
    if any(name not in GROUP_ORDER or not np.isfinite(value) or value < 0
           for name, value in group_weights.items()) or not any(group_weights.values()):
        raise ValueError("invalid feature-group weights")
    for rows in (training, calibration):
        if set(label for label, _ in rows) != set(EIGHT_TARGET_MODELS):
            raise ValueError("training and calibration must each cover all eight models")
    matrix = np.stack([feature_vector(n, bank, group_weights) for _, n in training])
    mean, scale = matrix.mean(0), matrix.std(0)
    scale[scale < 1e-12] = 1
    example = feature_groups(training[0][1], bank)
    multiplier = np.concatenate([np.full(len(example[name]), group_weights[name]/np.sqrt(len(example[name])))
                                 for name in GROUP_ORDER if group_weights.get(name, 0) > 0])
    x = (matrix-mean)/scale*multiplier
    y = np.asarray([EIGHT_TARGET_MODELS.index(label) for label, _ in training])
    targets = np.eye(8)[y]
    target_mean = targets.mean(0)
    kernel = x@x.T
    classifier_fields = {"classifier": classifier}
    if classifier == "kernel":
        distances = np.maximum((x*x).sum(1)[:, None]+(x*x).sum(1)[None, :]-2*kernel, 0)
        bandwidth = float(np.median(distances[np.triu_indices(len(x), 1)]))
        if bandwidth <= 0:
            raise ValueError("kernel fitting requires distinct training features")
        kernel = np.exp(-gamma*distances/bandwidth)
        coefficients = np.linalg.solve(kernel + alpha*np.eye(len(x)), targets-target_mean)
        classifier_fields.update(training_features=x.tolist(), coefficients=coefficients.tolist(),
                                 bandwidth=bandwidth, gamma=gamma)
    else:
        weights = x.T@np.linalg.solve(kernel + alpha*np.eye(len(x)), targets-target_mean)
        classifier_fields["weights"] = weights.tolist()
    support_matrix = np.stack([_support_feature(n, bank) for _, n in training])
    support_mean, support_scale = support_matrix.mean(0), support_matrix.std(0)
    support_scale[support_scale < 1e-12] = 1
    z = (support_matrix-support_mean)/support_scale
    centroids = np.stack([z[y == i].mean(0) for i in range(8)])
    residuals = z-centroids[y]
    precision = np.linalg.inv(residuals.T@residuals/len(z) + covariance_shrinkage*np.eye(z.shape[1]))
    distances = [[] for _ in range(8)]
    for label, n in calibration:
        i = EIGHT_TARGET_MODELS.index(label)
        delta = (_support_feature(n, bank)-support_mean)/support_scale-centroids[i]
        distances[i].append(float(delta@precision@delta))
    # Maximum of independently collected per-class calibration distances.
    # With 16 calibration rows the tail resolution is only 1/17, not 99%.
    return {"schema": "traceone-sequence-adapter-v1", "models": list(EIGHT_TARGET_MODELS),
            "bank_model_order": bank["robust"]["model_order"], "alpha": alpha,
            "minimum_margin": minimum_margin, "group_weights": group_weights,
            "training_rows": len(training), "training_label_counts": dict(Counter(l for l, _ in training)),
            "calibration_rows": len(calibration), "calibration_label_counts": dict(Counter(l for l, _ in calibration)),
            "feature_mean": mean.tolist(), "feature_scale": scale.tolist(), "feature_multiplier": multiplier.tolist(),
            "target_mean": target_mean.tolist(), **classifier_fields,
            "support": {"feature_mean": support_mean.tolist(), "feature_scale": support_scale.tolist(),
                        "centroids": centroids.tolist(), "precision": precision.tolist(),
                        "covariance_shrinkage": covariance_shrinkage,
                        "thresholds": [max(d) for d in distances],
                        "calibration_distances": [sorted(d) for d in distances],
                        "warning": "empirical class-conditional support; no guarantee under drift or unknown models"}}


def load_optimized(path: Path | None = None) -> dict:
    source = path if path is not None else files("traceone").joinpath("data/codex_low_v8_optimized.json")
    return json.loads(source.read_text(encoding="utf-8"))


def analyzable_response(text: str) -> bool:
    """Explicit, bounded tolerance; no invented, padded, or clamped integers."""
    parsed = parse_grid_response(text)
    if not 280 <= len(parsed.numbers) <= 350:
        return False
    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        return False
    if isinstance(payload, dict) and set(payload) == {"numbers"}:
        payload = payload["numbers"]
    return (isinstance(payload, list) and len(payload) == 9
            and all(isinstance(r, list) and 25 <= sum(isinstance(v, int) and not isinstance(v, bool)
                    and 1 <= v <= 355 for v in r) <= 45 for r in payload))


def identify_text_optimized(text: str, *, bank: dict | None = None, artifact: dict | None = None,
                            response_format: str = "grid", guard=ENROLLED_OUTER_GUARD) -> SupportResult:
    if response_format != "grid":
        raise ValueError("optimized method requires a 9x35 grid")
    bank, artifact = bank or load_bank(), artifact or load_optimized()
    if artifact["bank_model_order"] != bank["robust"]["model_order"]:
        raise ValueError("optimized artifact and bank order differ")
    parsed = parse_grid_response(text)
    outer = classify_parsed(parsed, bank=bank, guard=guard)
    if not analyzable_response(text):
        base = AdapterResult("unknown", None, None, {}, outer)
        return SupportResult("unknown", None, None, None, None, None, "invalid", base)
    numbers = list(parsed.numbers)
    x = (feature_vector(numbers, bank, artifact["group_weights"])-np.asarray(artifact["feature_mean"]))
    x = x/np.asarray(artifact["feature_scale"])*np.asarray(artifact["feature_multiplier"])
    if artifact["classifier"] == "kernel":
        training = np.asarray(artifact["training_features"])
        distances = np.sum((training-x)**2, axis=1)
        kernel = np.exp(-artifact["gamma"]*distances/artifact["bandwidth"])
        scores = kernel@np.asarray(artifact["coefficients"]) + np.asarray(artifact["target_mean"])
    else:
        scores = x@np.asarray(artifact["weights"]) + np.asarray(artifact["target_mean"])
    order = np.argsort(scores)
    winner = int(order[-1])
    margin = float(scores[winner]-scores[order[-2]])
    label = artifact["models"][winner]
    margin_passed = margin >= artifact["minimum_margin"]-1e-12
    base = AdapterResult("identified" if margin_passed else "unknown",
                         label if margin_passed else None, margin,
                         dict(zip(artifact["models"], map(float, scores))), outer)
    support = artifact["support"]
    residual = (_support_feature(numbers, bank)-np.asarray(support["feature_mean"]))/np.asarray(support["feature_scale"])
    residual -= np.asarray(support["centroids"][winner])
    distance = float(residual@np.asarray(support["precision"])@residual)
    threshold = support["thresholds"][winner]
    tolerance = 1e-10*max(1, abs(distance))
    calibration = support["calibration_distances"][winner]
    p = (1+sum(d >= distance-tolerance for d in calibration))/(len(calibration)+1)
    boundary_tolerance = 1e-10*max(1,abs(distance),abs(threshold))
    passed = margin_passed and distance <= threshold+boundary_tolerance
    path = "optimized_distance" if passed else "optimized_margin" if not margin_passed else "optimized_rejected"
    return SupportResult("identified" if passed else "unknown", label if passed else None,
                         passed, distance, threshold, p, path, base)
