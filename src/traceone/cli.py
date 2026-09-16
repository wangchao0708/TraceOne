from __future__ import annotations

import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path

from .adapter import identify_text_adapted
from .canary import score_canary
from .degradation import compare_paired_outcomes, compare_stratified_outcomes, plan_mcnemar
from .fingerprint import (
    ADAPTIVE_GUARD,
    BALANCED_GUARD,
    ENROLLED_OUTER_GUARD,
    STRICT_GUARD,
    identify_text,
)
from .support import identify_text_supported


def _read_text(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def _read_outcome_records(
    path: Path,
) -> tuple[dict[str, bool | None], dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload["items"] if isinstance(payload, dict) and "items" in payload else payload
    if not isinstance(items, list):
        raise ValueError("outcome file must be a list or an object containing 'items'")
    outcomes: dict[str, bool | None] = {}
    families: dict[str, str] = {}
    for item in items:
        item_id = str(item["id"])
        correct = item.get("correct")
        if correct not in (True, False, None):
            raise ValueError(f"item {item_id!r} has a non-boolean 'correct' value")
        if item_id in outcomes:
            raise ValueError(f"duplicate item id: {item_id}")
        outcomes[item_id] = correct
        if item.get("family") is not None:
            families[item_id] = str(item["family"])
    return outcomes, families


def main() -> None:
    parser = argparse.ArgumentParser(prog="traceone")
    commands = parser.add_subparsers(dest="command", required=True)

    identify = commands.add_parser("identify", help="identify one saved response")
    identify.add_argument("response", help="response file, or - for stdin")
    identify.add_argument("--format", choices=("grid", "flat"), default="grid")
    identify.add_argument(
        "--guard",
        choices=("release", "adaptive", "balanced", "strict"),
        default="release",
    )
    identify.add_argument(
        "--method", choices=("supported", "enrolled", "bank"), default="supported"
    )

    commands.add_parser("prompt", help="print the frozen one-call identity prompt")

    score = commands.add_parser("score-canary", help="score responses against a canary artifact")
    score.add_argument("benchmark", type=Path)
    score.add_argument("responses", type=Path)

    degradation = commands.add_parser("degradation", help="compare paired benchmark outcomes")
    degradation.add_argument("baseline", type=Path)
    degradation.add_argument("current", type=Path)
    degradation.add_argument("--alpha", type=float, default=0.05)
    degradation.add_argument("--minimum-effect", type=float, default=0.02)
    degradation.add_argument(
        "--invalid-policy", choices=("fail", "exclude"), default="fail"
    )
    degradation.add_argument(
        "--allow-partial", action="store_true", help="allow different item sets"
    )
    degradation.add_argument(
        "--by-family", action="store_true", help="add Holm-corrected family tests"
    )

    power = commands.add_parser(
        "plan-degradation", help="plan paired McNemar benchmark power"
    )
    power.add_argument(
        "--candidate-items", type=int, nargs="+", default=(48, 96, 192, 384, 768)
    )
    power.add_argument("--regression-probability", type=float, required=True)
    power.add_argument("--improvement-probability", type=float, required=True)
    power.add_argument("--alpha", type=float, default=0.05)
    power.add_argument("--minimum-effect", type=float, default=0.02)
    power.add_argument("--target-power", type=float, default=0.8)
    power.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "identify":
        guard = {
            "release": ENROLLED_OUTER_GUARD,
            "adaptive": ADAPTIVE_GUARD,
            "balanced": BALANCED_GUARD,
            "strict": STRICT_GUARD,
        }[args.guard]
        identify_function = {
            "supported": identify_text_supported,
            "enrolled": identify_text_adapted,
            "bank": identify_text,
        }[args.method]
        result = identify_function(
            _read_text(args.response), response_format=args.format, guard=guard
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "prompt":
        prompt = files("traceone").joinpath("data/identity-v3-schema.txt")
        print(prompt.read_text(encoding="utf-8").strip())
    elif args.command == "score-canary":
        benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
        responses = [
            json.loads(line)
            for line in args.responses.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        print(json.dumps(score_canary(benchmark, responses), ensure_ascii=False, indent=2))
    elif args.command == "degradation":
        baseline, baseline_families = _read_outcome_records(args.baseline)
        current, current_families = _read_outcome_records(args.current)
        if args.by_family:
            families = {**baseline_families, **current_families}
            result = compare_stratified_outcomes(
                baseline,
                current,
                families,
                alpha=args.alpha,
                minimum_effect=args.minimum_effect,
                invalid_policy=args.invalid_policy,
                require_complete_pairing=not args.allow_partial,
            )
        else:
            result = compare_paired_outcomes(
                baseline,
                current,
                alpha=args.alpha,
                minimum_effect=args.minimum_effect,
                invalid_policy=args.invalid_policy,
                require_complete_pairing=not args.allow_partial,
            ).to_dict()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = plan_mcnemar(
            args.candidate_items,
            args.regression_probability,
            args.improvement_probability,
            alpha=args.alpha,
            minimum_effect=args.minimum_effect,
            target_power=args.target_power,
        )
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")


if __name__ == "__main__":
    main()
