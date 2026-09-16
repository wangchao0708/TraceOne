#!/usr/bin/env python3
"""Verify every path/SHA-256 pair in a TraceOne release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def entries(value: object, location: str = "root") -> list[tuple[str, str, str]]:
    found = []
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            found.append((location, value["path"], value["sha256"]))
        for key, child in value.items():
            found.extend(entries(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(entries(child, f"{location}[{index}]"))
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    checks = []
    for location, relative, expected in entries(payload):
        path = (PROJECT / relative).resolve()
        try:
            path.relative_to(PROJECT.resolve())
        except ValueError as error:
            raise ValueError(f"manifest path escapes project: {relative}") from error
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        checks.append(
            {
                "entry": location,
                "path": relative,
                "valid": actual == expected,
                "actual": actual,
                "expected": expected,
            }
        )
    result = {
        "manifest": str(args.manifest),
        "valid": bool(checks) and all(item["valid"] for item in checks),
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
