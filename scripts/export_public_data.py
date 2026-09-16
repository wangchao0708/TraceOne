#!/usr/bin/env python3
"""Export reproducible numeric responses without local task IDs or stderr logs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PUBLIC_FIELDS = (
    "run_id",
    "split",
    "requested_model",
    "response_model",
    "provider",
    "reasoning_effort",
    "thinking_mode",
    "runtime",
    "prompt_id",
    "prompt_sha256",
    "output_schema",
    "output_schema_sha256",
    "wrapper",
    "collected_at",
    "elapsed_seconds",
    "return_code",
    "usage",
    "text",
)


def export_rows(inputs: list[Path], output: Path, root: Path) -> dict:
    rows = []
    seen = set()
    source_hashes = []
    for path in inputs:
        resolved = path.resolve()
        source_name = str(resolved.relative_to(root.resolve()))
        source_bytes = path.read_bytes()
        source_hashes.append(
            {"source_file": source_name, "sha256": hashlib.sha256(source_bytes).hexdigest()}
        )
        for line_number, line in enumerate(source_bytes.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            raw = json.loads(line)
            original_id = str(raw["sample_id"])
            public_id = f"{source_name}::{original_id}"
            if public_id in seen:
                raise ValueError(f"duplicate public id: {public_id}")
            seen.add(public_id)
            public = {
                "schema": "traceone-public-sample-v1",
                "sample_id": public_id,
                "source_file": source_name,
                "source_line": line_number,
                "source_record_sha256": hashlib.sha256(
                    (line + "\n").encode("utf-8")
                ).hexdigest(),
            }
            public.update({key: raw.get(key) for key in PUBLIC_FIELDS if key in raw})
            rows.append(public)

    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in rows
    )
    output.write_text(rendered, encoding="utf-8")
    return {
        "schema": "traceone-public-export-manifest-v1",
        "output": str(output),
        "rows": len(rows),
        "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "excluded_fields": ["thread_id", "stderr_tail"],
        "sources": source_hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    manifest = export_rows(args.inputs, args.output, args.root)
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
