"""Paired capability-degradation tests, kept separate from fingerprint drift."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class DegradationResult:
    status: str
    paired_items: int
    baseline_accuracy: float
    current_accuracy: float
    accuracy_loss: float
    regressions: int
    improvements: int
    unchanged_correct: int
    unchanged_wrong: int
    baseline_only_items: int
    current_only_items: int
    invalid_baseline_items: int
    invalid_current_items: int
    one_sided_p_value: float
    alpha: float
    minimum_effect: float
    invalid_policy: str
    complete_pairing: bool

    def to_dict(self) -> dict:
        return asdict(self)


def one_sided_mcnemar(regressions: int, improvements: int) -> float:
    """Exact P[X >= regressions], X ~ Binomial(discordant, 0.5)."""
    if regressions < 0 or improvements < 0:
        raise ValueError("discordant counts must be non-negative")
    discordant = regressions + improvements
    if discordant == 0:
        return 1.0
    numerator = sum(math.comb(discordant, value) for value in range(regressions, discordant + 1))
    return numerator / (2**discordant)


def compare_paired_outcomes(
    baseline: Mapping[str, bool | None],
    current: Mapping[str, bool | None],
    *,
    alpha: float = 0.05,
    minimum_effect: float = 0.02,
    invalid_policy: str = "fail",
    require_complete_pairing: bool = True,
) -> DegradationResult:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 <= minimum_effect <= 1:
        raise ValueError("minimum_effect must be between 0 and 1")
    if invalid_policy not in {"fail", "exclude"}:
        raise ValueError("invalid_policy must be 'fail' or 'exclude'")

    shared = sorted(set(baseline) & set(current))
    invalid_baseline = sum(baseline[item] is None for item in shared)
    invalid_current = sum(current[item] is None for item in shared)
    if invalid_policy == "exclude":
        eligible = [
            item
            for item in shared
            if baseline[item] is not None and current[item] is not None
        ]
    else:
        eligible = shared

    def outcome(values: Mapping[str, bool | None], item: str) -> bool:
        value = values[item]
        return False if value is None else value

    regressions = sum(outcome(baseline, item) and not outcome(current, item) for item in eligible)
    improvements = sum(not outcome(baseline, item) and outcome(current, item) for item in eligible)
    unchanged_correct = sum(outcome(baseline, item) and outcome(current, item) for item in eligible)
    unchanged_wrong = sum(not outcome(baseline, item) and not outcome(current, item) for item in eligible)
    paired = len(eligible)
    baseline_accuracy = (regressions + unchanged_correct) / paired if paired else 0.0
    current_accuracy = (improvements + unchanged_correct) / paired if paired else 0.0
    loss = baseline_accuracy - current_accuracy
    p_value = one_sided_mcnemar(regressions, improvements)
    degraded = paired > 0 and loss >= minimum_effect and p_value <= alpha

    complete_pairing = set(baseline) == set(current)
    if require_complete_pairing and not complete_pairing:
        status = "invalid_comparison"
    elif paired == 0:
        status = "insufficient_data"
    elif degraded:
        status = "degraded"
    elif loss >= minimum_effect:
        status = "inconclusive"
    else:
        status = "no_detected_degradation"

    return DegradationResult(
        status=status,
        paired_items=paired,
        baseline_accuracy=baseline_accuracy,
        current_accuracy=current_accuracy,
        accuracy_loss=loss,
        regressions=regressions,
        improvements=improvements,
        unchanged_correct=unchanged_correct,
        unchanged_wrong=unchanged_wrong,
        baseline_only_items=len(set(baseline) - set(current)),
        current_only_items=len(set(current) - set(baseline)),
        invalid_baseline_items=invalid_baseline,
        invalid_current_items=invalid_current,
        one_sided_p_value=p_value,
        alpha=alpha,
        minimum_effect=minimum_effect,
        invalid_policy=invalid_policy,
        complete_pairing=complete_pairing,
    )


def holm_bonferroni(p_values: Iterable[float], alpha: float = 0.05) -> list[dict]:
    """Return decisions in original order for a family of predeclared tests."""
    values = list(p_values)
    if any(not 0 <= value <= 1 for value in values):
        raise ValueError("p-values must be between 0 and 1")
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    rejected: set[int] = set()
    stopped = False
    for rank, (index, value) in enumerate(ordered):
        threshold = alpha / (len(values) - rank)
        if not stopped and value <= threshold:
            rejected.add(index)
        else:
            stopped = True

    adjusted = [0.0] * len(values)
    running = 0.0
    for rank, (index, value) in enumerate(ordered):
        running = max(running, (len(values) - rank) * value)
        adjusted[index] = min(1.0, running)
    return [
        {"p_value": value, "adjusted_p_value": adjusted[index], "reject": index in rejected}
        for index, value in enumerate(values)
    ]


def compare_stratified_outcomes(
    baseline: Mapping[str, bool | None],
    current: Mapping[str, bool | None],
    families: Mapping[str, str],
    *,
    alpha: float = 0.05,
    minimum_effect: float = 0.02,
    invalid_policy: str = "fail",
    require_complete_pairing: bool = True,
) -> dict:
    """Run one preregistered primary test plus Holm-corrected family tests."""
    overall = compare_paired_outcomes(
        baseline,
        current,
        alpha=alpha,
        minimum_effect=minimum_effect,
        invalid_policy=invalid_policy,
        require_complete_pairing=require_complete_pairing,
    )
    shared = set(baseline) & set(current)
    missing_families = sorted(item for item in shared if item not in families)
    if missing_families:
        raise ValueError(f"missing family for item: {missing_families[0]}")
    family_names = sorted({families[item] for item in shared})
    raw = []
    for family in family_names:
        item_ids = {item for item in shared if families[item] == family}
        raw.append(
            compare_paired_outcomes(
                {item: baseline[item] for item in item_ids},
                {item: current[item] for item in item_ids},
                alpha=alpha,
                minimum_effect=minimum_effect,
                invalid_policy=invalid_policy,
                require_complete_pairing=require_complete_pairing,
            )
        )
    corrections = holm_bonferroni(
        [result.one_sided_p_value for result in raw], alpha=alpha
    )
    family_results = []
    for name, result, correction in zip(family_names, raw, corrections):
        payload = result.to_dict()
        eligible = result.status not in {"invalid_comparison", "insufficient_data"}
        detected = (
            eligible
            and result.accuracy_loss >= minimum_effect
            and correction["reject"]
        )
        payload.update(
            {
                "family": name,
                "holm_adjusted_p_value": correction["adjusted_p_value"],
                "holm_reject": correction["reject"],
                "multiplicity_adjusted_status": (
                    "degraded" if detected else result.status
                ),
            }
        )
        if result.status == "degraded" and not detected:
            payload["multiplicity_adjusted_status"] = "inconclusive"
        family_results.append(payload)
    return {
        "schema": "traceone-degradation-suite-v1",
        "primary_test": "overall paired exact one-sided McNemar",
        "overall": overall.to_dict(),
        "secondary_tests": "per-family paired tests with Holm-Bonferroni correction",
        "families": family_results,
    }


def _log_binomial_probability(n: int, k: int, probability: float) -> float:
    if k < 0 or k > n:
        return -math.inf
    if probability == 0:
        return 0.0 if k == 0 else -math.inf
    if probability == 1:
        return 0.0 if k == n else -math.inf
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(probability)
        + (n - k) * math.log1p(-probability)
    )


def _binomial_tail(n: int, start: int, probability: float) -> float:
    if start <= 0:
        return 1.0
    if start > n:
        return 0.0
    logs = [_log_binomial_probability(n, k, probability) for k in range(start, n + 1)]
    peak = max(logs)
    if peak == -math.inf:
        return 0.0
    return math.exp(peak) * sum(math.exp(value - peak) for value in logs)


def _mcnemar_critical_regressions(discordant: int, alpha: float) -> int:
    if discordant == 0:
        return 1
    # Accumulate the exact Binomial(d, .5) upper tail from d downwards.
    # This is O(d), whereas repeatedly calling one_sided_mcnemar is O(d^2).
    term = 2.0**-discordant
    tail = 0.0
    critical = discordant + 1
    for regressions in range(discordant, (discordant - 1) // 2, -1):
        if regressions < discordant:
            term *= (regressions + 1) / (discordant - regressions)
        tail += term
        if tail <= alpha:
            critical = regressions
        else:
            break
    return critical


def mcnemar_detection_power(
    sample_size: int,
    regression_probability: float,
    improvement_probability: float,
    *,
    alpha: float = 0.05,
    minimum_effect: float = 0.02,
) -> float:
    """Exact unconditional power under specified paired outcome probabilities."""
    if sample_size < 1:
        raise ValueError("sample_size must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 <= minimum_effect <= 1:
        raise ValueError("minimum_effect must be between 0 and 1")
    if regression_probability < 0 or improvement_probability < 0:
        raise ValueError("paired-change probabilities must be non-negative")
    discordant_probability = regression_probability + improvement_probability
    if discordant_probability > 1:
        raise ValueError("paired-change probabilities must sum to at most one")
    if discordant_probability == 0:
        return 0.0

    regression_share = regression_probability / discordant_probability
    power = 0.0
    for discordant in range(sample_size + 1):
        critical = _mcnemar_critical_regressions(discordant, alpha)
        effect_critical = math.ceil(
            (discordant + sample_size * minimum_effect) / 2 - 1e-12
        )
        threshold = max(critical, effect_critical)
        if threshold > discordant:
            continue
        discordant_mass = math.exp(
            _log_binomial_probability(
                sample_size, discordant, discordant_probability
            )
        )
        power += discordant_mass * _binomial_tail(
            discordant, threshold, regression_share
        )
    return min(1.0, max(0.0, power))


def plan_mcnemar(
    candidate_sizes: Sequence[int],
    regression_probability: float,
    improvement_probability: float,
    *,
    alpha: float = 0.05,
    minimum_effect: float = 0.02,
    target_power: float = 0.8,
) -> dict:
    """Evaluate exact power for explicit candidate benchmark sizes."""
    sizes = sorted(set(candidate_sizes))
    if not sizes or sizes[0] < 1:
        raise ValueError("candidate_sizes must contain positive integers")
    if not 0 < target_power < 1:
        raise ValueError("target_power must be between 0 and 1")
    candidates = []
    for size in sizes:
        power = mcnemar_detection_power(
            size,
            regression_probability,
            improvement_probability,
            alpha=alpha,
            minimum_effect=minimum_effect,
        )
        candidates.append({"items": size, "exact_power": power})
    recommended = next(
        (item["items"] for item in candidates if item["exact_power"] >= target_power),
        None,
    )
    return {
        "schema": "traceone-mcnemar-power-plan-v1",
        "assumptions": {
            "regression_probability": regression_probability,
            "improvement_probability": improvement_probability,
            "net_accuracy_loss": regression_probability - improvement_probability,
            "alpha": alpha,
            "minimum_effect": minimum_effect,
            "target_power": target_power,
        },
        "candidates": candidates,
        "recommended_items": recommended,
        "warning": (
            "Power depends on preregistered paired-change probabilities; "
            "candidate sizes are evaluated, not continuously optimized."
        ),
    }
