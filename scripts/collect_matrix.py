#!/usr/bin/env python3
"""Collect a balanced model matrix, one isolated call per sample."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


MODELS = (
    "gpt-5.5",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
    "gpt-6-astra",
    "gpt-6-sol",
    "gpt-6-luna",
)
COLLECTABLE_MODELS = MODELS + ("gpt-5.4", "gpt-6.1-sol")
PROJECT = Path(__file__).resolve().parents[1]
COLLECTOR = PROJECT / "scripts" / "collect_codex.py"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--no-schema", action="store_true")
    parser.add_argument("--codex", help="pin a specific Codex executable for every call")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--split", choices=("development", "calibration", "holdout", "confirmation"), required=True)
    parser.add_argument("--repeat-start", type=int, required=True)
    parser.add_argument("--repeat-end", type=int, required=True)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=COLLECTABLE_MODELS,
        default=list(MODELS),
        help="routes to collect; defaults to all release targets",
    )
    args = parser.parse_args()
    if args.repeat_start < 1 or args.repeat_end < args.repeat_start:
        raise SystemExit("invalid repeat range")
    if "gpt-6.1-sol" in args.models and len(args.models) != 1:
        raise SystemExit("collect the prospective gpt-6.1-sol route alone until access is verified")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for repeat in range(args.repeat_start, args.repeat_end + 1):
        processes = {}
        for model in args.models:
            command = [
                sys.executable,
                str(COLLECTOR),
                "--output",
                str(output_dir / f"{model}.jsonl"),
                "--prompt",
                str(args.prompt.resolve()),
                "--split",
                args.split,
                "--repeat",
                str(repeat),
                "--model",
                model,
                "--run-id",
                args.run_id,
            ]
            if args.no_schema:
                command.append("--no-schema")
            else:
                command.extend(["--schema", str(args.schema.resolve())])
            if args.codex:
                command.extend(["--codex", str(Path(args.codex).expanduser().resolve())])
            processes[model] = subprocess.Popen(
                command,
                cwd=PROJECT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        batch = {}
        failed = False
        for model, process in processes.items():
            stdout, stderr = process.communicate(timeout=300)
            batch[model] = {
                "return_code": process.returncode,
                "collector": stdout.strip(),
                "stderr_tail": "\n".join(stderr.splitlines()[-4:]),
            }
            failed |= process.returncode != 0
        print(json.dumps({"repeat": repeat, "models": batch}, ensure_ascii=False), flush=True)
        if failed:
            raise SystemExit(f"collection failed in repeat {repeat}")


if __name__ == "__main__":
    main()
