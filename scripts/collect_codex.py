#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


MODELS = (
    "gpt-5.5",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
    "gpt-6-astra",
    "gpt-6-sol",
    "gpt-6-luna",
    "gpt-6.1-sol",
)
REFERENCE_OOD_MODELS = ("gpt-5.4",)
PROSPECTIVE_MODELS = ()
BUNDLED_CODEX_CANDIDATES = (
    Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"),
    Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
)


def codex_path(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
    elif bundled := next((item for item in BUNDLED_CODEX_CANDIDATES if item.is_file()), None):
        path = bundled
    else:
        found = shutil.which("codex")
        if not found:
            raise SystemExit("Codex executable not found")
        path = Path(found).resolve()
    return path


def runtime_version(executable: Path) -> str:
    result = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def collect_one(
    executable: Path,
    model: str,
    prompt: str,
    split: str,
    repeat: int,
    output_schema: Path | None = None,
    run_id: str | None = None,
) -> dict:
    with tempfile.TemporaryDirectory(prefix="traceone-") as clean_dir:
        started = time.monotonic()
        command = [
            str(executable),
            "-a",
            "never",
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--json",
            "-m",
            model,
            "-c",
            'model_reasoning_effort="low"',
            "-s",
            "read-only",
        ]
        if output_schema is not None:
            command.extend(["--output-schema", str(output_schema)])
        command.append(prompt)
        timed_out = False
        try:
            result = subprocess.run(
                command,
                cwd=clean_dir,
                capture_output=True,
                text=True,
                timeout=240,
            )
        except subprocess.TimeoutExpired as error:
            timed_out = True
            stdout = (
                error.stdout.decode("utf-8", "replace")
                if isinstance(error.stdout, bytes) else error.stdout or ""
            )
            stderr = (
                error.stderr.decode("utf-8", "replace")
                if isinstance(error.stderr, bytes) else error.stderr or ""
            )
            result = subprocess.CompletedProcess(command, 124, stdout, stderr)
        elapsed = time.monotonic() - started

    events = []
    for line in result.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    messages = [
        event["item"]["text"]
        for event in events
        if event.get("type") == "item.completed"
        and event.get("item", {}).get("type") == "agent_message"
    ]
    usage_events = [event.get("usage") for event in events if event.get("type") == "turn.completed"]
    item_types = Counter(event.get("item", {}).get("type", "unknown")
                         for event in events if event.get("type") == "item.completed")
    tool_item_count = sum(count for kind, count in item_types.items()
                          if kind not in {"agent_message", "reasoning", "error"})
    thread_events = [event for event in events if event.get("type") == "thread.started"]
    stderr_tail = result.stderr.splitlines()[-12:]
    if timed_out:
        stderr_tail.append("codex exec timed out after 240 seconds")
    return {
        "schema": "traceone-sample-v1",
        "sample_id": "__".join(
            part
            for part in (model, run_id, split, f"{repeat:03d}")
            if part is not None
        ),
        "run_id": run_id,
        "split": split,
        "requested_model": model,
        "response_model": None,
        "provider": "openai-codex-subscription",
        "reasoning_effort": "low",
        "thinking_mode": "reasoning-low",
        "runtime": runtime_version(executable),
        "prompt_id": None,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "output_schema_sha256": (
            hashlib.sha256(output_schema.read_bytes()).hexdigest()
            if output_schema is not None
            else None
        ),
        "wrapper": "codex-exec-ephemeral-ignore-user-config-read-only",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed,
        "return_code": result.returncode,
        "thread_id": thread_events[-1].get("thread_id") if thread_events else None,
        "usage": usage_events[-1] if usage_events else None,
        "completed_item_types": dict(item_types),
        "tool_item_count": tool_item_count,
        "completed_error_count": item_types.get("error", 0),
        "text": "" if timed_out else (messages[-1] if messages else ""),
        "stderr_tail": "\n".join(stderr_tail),
    }


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8"))
    finally:
        os.close(descriptor)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--prompt", type=Path, default=Path("prompts/identity-replacement-v1.txt")
    )
    parser.add_argument(
        "--split",
        choices=("development", "calibration", "holdout", "confirmation"),
        required=True,
    )
    parser.add_argument("--repeat", type=int, required=True)
    parser.add_argument(
        "--model", choices=MODELS + REFERENCE_OOD_MODELS + PROSPECTIVE_MODELS,
        required=True,
    )
    parser.add_argument("--codex")
    parser.add_argument("--schema", type=Path, default=Path("schemas/identity-v3.json"))
    parser.add_argument("--no-schema", action="store_true")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    prompt = args.prompt.read_text(encoding="utf-8").strip()
    executable = codex_path(args.codex)
    schema = None if args.no_schema else args.schema.resolve()
    record = collect_one(
        executable, args.model, prompt, args.split, args.repeat, schema, args.run_id
    )
    record["prompt_id"] = args.prompt.stem
    record["output_schema"] = args.schema.name if schema else None
    append_jsonl(args.output, record)
    print(
        json.dumps(
            {
                "sample_id": record["sample_id"],
                "return_code": record["return_code"],
                "text_length": len(record["text"]),
                "elapsed_seconds": round(record["elapsed_seconds"], 3),
            },
            ensure_ascii=False,
        )
    )
    if record["return_code"] != 0:
        raise SystemExit(record["return_code"])


if __name__ == "__main__":
    main()
