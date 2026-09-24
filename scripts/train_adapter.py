#!/usr/bin/env python3
"""Train the fixed ridge adapter from explicitly listed enrollment JSONL files."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from traceone.adapter import fit_ridge_adapter
from traceone.fingerprint import TARGET_MODELS, load_bank
from traceone.parsing import parse_grid_response


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=10.0)
    parser.add_argument("--minimum-margin", type=float, default=0.05)
    args = parser.parse_args()

    labeled = []
    sources = []
    prompt_hashes = set()
    schema_hashes = set()
    runtimes_by_model = defaultdict(set)
    reasoning = set()
    wrappers = set()
    providers = set()
    seen_records = set()
    for path in args.inputs:
        raw = path.read_bytes()
        sources.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
        for line in raw.decode("utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            record_id = str(row.get("thread_id", row["sample_id"]))
            if record_id in seen_records:
                raise ValueError(f"duplicate enrollment record: {record_id}")
            seen_records.add(record_id)
            parsed = parse_grid_response(row["text"])
            if not parsed.valid:
                raise ValueError(f"non-compliant enrollment row: {row['sample_id']}")
            labeled.append((row["requested_model"], list(parsed.numbers)))
            prompt_hashes.add(row["prompt_sha256"])
            schema_hashes.add(row["output_schema_sha256"])
            runtimes_by_model[row["requested_model"]].add(row["runtime"])
            reasoning.add(row["reasoning_effort"])
            wrappers.add(row["wrapper"])
            providers.add(row["provider"])

    if len(prompt_hashes) != 1 or len(schema_hashes) != 1:
        raise ValueError("enrollment prompt/schema drift detected")
    if reasoning != {"low"} or len(wrappers) != 1 or len(providers) != 1:
        raise ValueError("enrollment reasoning/wrapper/provider drift detected")
    counts = Counter(label for label, _ in labeled)
    if set(counts) != set(TARGET_MODELS) or len(set(counts.values())) != 1:
        raise ValueError(f"enrollment must be balanced across targets: {counts}")

    artifact = fit_ridge_adapter(
        labeled,
        load_bank(),
        alpha=args.alpha,
        minimum_margin=args.minimum_margin,
    )
    artifact["training_sources"] = sources
    artifact["training_label_counts"] = dict(counts)
    artifact["prompt_sha256"] = next(iter(prompt_hashes))
    artifact["output_schema_sha256"] = next(iter(schema_hashes))
    artifact["runtimes_by_model"] = {
        model: sorted(versions) for model, versions in sorted(runtimes_by_model.items())
    }
    artifact["reasoning_effort"] = "low"
    artifact["wrapper"] = next(iter(wrappers))
    artifact["provider"] = next(iter(providers))
    args.output.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "training_rows": len(labeled),
                "label_counts": dict(counts),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
