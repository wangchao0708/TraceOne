#!/usr/bin/env python3
"""Train the empirical target-support envelope from listed enrollment files."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from traceone.adapter import load_adapter
from traceone.fingerprint import TARGET_MODELS, load_bank
from traceone.parsing import parse_grid_response
from traceone.support import fit_support


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--covariance-shrinkage", type=float, default=0.3)
    parser.add_argument("--distance-quantile", type=float, default=0.99)
    parser.add_argument("--rescue-margin-quantile", type=float, default=0.95)
    args = parser.parse_args()
    labeled = []
    sources = []
    counts = Counter()
    for path in args.inputs:
        raw = path.read_bytes()
        sources.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
        for line in raw.decode("utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            parsed = parse_grid_response(row.get("text", ""))
            if not parsed.valid:
                raise ValueError(f"invalid enrollment row: {row.get('sample_id')}")
            label = row["requested_model"]
            counts[label] += 1
            labeled.append((label, list(parsed.numbers)))
    if set(counts) != set(TARGET_MODELS) or len(set(counts.values())) != 1:
        raise ValueError(f"balanced enrollment is required: {counts}")
    adapter = load_adapter(args.adapter)
    artifact = fit_support(
        labeled,
        load_bank(),
        adapter,
        covariance_shrinkage=args.covariance_shrinkage,
        distance_quantile=args.distance_quantile,
        rescue_margin_quantile=args.rescue_margin_quantile,
    )
    artifact["training_sources"] = sources
    artifact["training_label_counts"] = dict(counts)
    if args.adapter:
        adapter_bytes = args.adapter.read_bytes()
        artifact["adapter"] = {
            "path": str(args.adapter),
            "sha256": hashlib.sha256(adapter_bytes).hexdigest(),
        }
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
