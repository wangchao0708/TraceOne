#!/usr/bin/env python3
"""Verify that a frozen experiment config still matches its local assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    checks = []

    prompt = config["prompt"]
    prompt_path = PROJECT / prompt["path"]
    if "file_sha256" in prompt:
        checks.append(("prompt_file", digest(prompt_path.read_bytes()), prompt["file_sha256"]))
    if "normalized_text_sha256" in prompt:
        normalized = prompt_path.read_text(encoding="utf-8").strip().encode("utf-8")
        checks.append(
            ("prompt_normalized_text", digest(normalized), prompt["normalized_text_sha256"])
        )

    for key in ("output_schema", "bank", "classifier"):
        if key not in config:
            continue
        entry = config[key]
        checks.append((key, digest((PROJECT / entry["path"]).read_bytes()), entry["sha256"]))

    if "outer_guard" in config:
        entry = config["outer_guard"]
        checks.append(
            (
                "outer_guard_implementation",
                digest((PROJECT / entry["implementation"]).read_bytes()),
                entry["sha256"],
            )
        )
        checks.append(
            ("outer_guard_bank", digest((PROJECT / entry["bank"]).read_bytes()), entry["bank_sha256"])
        )
    if "enrollment_adapter" in config:
        entry = config["enrollment_adapter"]
        checks.append(
            (
                "adapter_implementation",
                digest((PROJECT / entry["implementation"]).read_bytes()),
                entry["implementation_sha256"],
            )
        )
        checks.append(
            ("adapter_artifact", digest((PROJECT / entry["artifact"]).read_bytes()), entry["artifact_sha256"])
        )
    if "target_support" in config:
        entry = config["target_support"]
        checks.append(
            (
                "support_implementation",
                digest((PROJECT / entry["implementation"]).read_bytes()),
                entry["implementation_sha256"],
            )
        )
        checks.append(
            (
                "support_artifact",
                digest((PROJECT / entry["artifact"]).read_bytes()),
                entry["artifact_sha256"],
            )
        )
    if "public_enrollment" in config:
        entries = config["public_enrollment"]
        if isinstance(entries, dict):
            entries = [entries]
        for index, entry in enumerate(entries):
            checks.append(
                (
                    f"public_enrollment_{index}",
                    digest((PROJECT / entry["path"]).read_bytes()),
                    entry["sha256"],
                )
            )

    result = {
        "config": str(args.config),
        "valid": all(actual == expected for _, actual, expected in checks),
        "checks": [
            {"asset": name, "valid": actual == expected, "actual": actual, "expected": expected}
            for name, actual, expected in checks
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
