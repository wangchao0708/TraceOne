#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from traceone.canary import generate_canary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--items-per-family", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = generate_canary(args.seed, args.items_per_family)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "items": len(payload["items"])}))


if __name__ == "__main__":
    main()
