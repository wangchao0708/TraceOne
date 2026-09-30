#!/usr/bin/env python3
"""Verify that a frozen experiment config still matches its local assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--revision", help="verify a historical config and assets at this Git commit")
    args = parser.parse_args()
    def read_asset(path: str | Path) -> bytes:
        relative = (PROJECT / path).resolve().relative_to(PROJECT).as_posix()
        if args.revision:
            return subprocess.check_output(["git", "-C", str(PROJECT), "show", f"{args.revision}:{relative}"])
        return (PROJECT / relative).read_bytes()

    config = json.loads(read_asset(args.config))
    checks = []

    prompt = config["prompt"]
    prompt_path = PROJECT / prompt["path"]
    if "file_sha256" in prompt:
        checks.append(("prompt_file", digest(read_asset(prompt_path)), prompt["file_sha256"]))
    if "normalized_text_sha256" in prompt:
        normalized = read_asset(prompt_path).decode("utf-8").strip().encode("utf-8")
        checks.append(
            ("prompt_normalized_text", digest(normalized), prompt["normalized_text_sha256"])
        )

    for key in ("output_schema", "bank", "classifier"):
        if key not in config:
            continue
        entry = config[key]
        checks.append((key, digest(read_asset(entry["path"])), entry["sha256"]))

    if "outer_guard" in config:
        entry = config["outer_guard"]
        checks.append(
            (
                "outer_guard_implementation",
                digest(read_asset(entry["implementation"])),
                entry["sha256"],
            )
        )
        checks.append(
            ("outer_guard_bank", digest(read_asset(entry["bank"])), entry["bank_sha256"])
        )
    if "enrollment_adapter" in config:
        entry = config["enrollment_adapter"]
        checks.append(
            (
                "adapter_implementation",
                digest(read_asset(entry["implementation"])),
                entry["implementation_sha256"],
            )
        )
        checks.append(
            ("adapter_artifact", digest(read_asset(entry["artifact"])), entry["artifact_sha256"])
        )
    if "target_support" in config:
        entry = config["target_support"]
        checks.append(
            (
                "support_implementation",
                digest(read_asset(entry["implementation"])),
                entry["implementation_sha256"],
            )
        )
        checks.append(
            (
                "support_artifact",
                digest(read_asset(entry["artifact"])),
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
                    digest(read_asset(entry["path"])),
                    entry["sha256"],
                )
            )

    for index, entry in enumerate(config.get("extra_files", [])):
        checks.append(
            (
                f"extra_file_{index}",
                digest(read_asset(entry["path"])),
                entry["sha256"],
            )
        )

    result = {
        "config": str(args.config),
        "revision": args.revision,
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
