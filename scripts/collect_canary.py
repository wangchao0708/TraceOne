#!/usr/bin/env python3
"""Collect one response per canary item for a paired baseline/current run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from collect_codex import append_jsonl, codex_path, collect_one


PROJECT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--schema", type=Path, default=PROJECT / "schemas" / "canary-answer-v1.json")
    parser.add_argument("--codex")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    benchmark_bytes = args.benchmark.read_bytes()
    benchmark = json.loads(benchmark_bytes)
    benchmark_hash = hashlib.sha256(benchmark_bytes).hexdigest()
    items = benchmark["items"][: args.limit] if args.limit else benchmark["items"]
    executable = codex_path(args.codex)
    schema = args.schema.resolve()
    for index, item in enumerate(items, start=1):
        record = collect_one(
            executable,
            args.model,
            item["prompt"],
            "canary",
            index,
            schema,
            args.run_id,
        )
        record.update(
            {
                "schema": "traceone-canary-response-v1",
                "sample_id": f"{args.model}__{args.run_id}__{item['id']}",
                "run_id": args.run_id,
                "item_id": item["id"],
                "item_family": item["family"],
                "benchmark_sha256": benchmark_hash,
                "output_schema": args.schema.name,
            }
        )
        append_jsonl(args.output, record)
        print(
            json.dumps(
                {
                    "item": index,
                    "total": len(items),
                    "item_id": item["id"],
                    "return_code": record["return_code"],
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
