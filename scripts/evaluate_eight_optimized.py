#!/usr/bin/env python3
"""Reproduce the eight-route experiment; failed/invalid calls remain in denominators."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from traceone.fingerprint import load_bank
from traceone.optimized import (EIGHT_TARGET_MODELS, analyzable_response, feature_groups, fit_optimized,
                                identify_text_optimized, load_optimized)
from traceone.parsing import parse_grid_response

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    for row in rows:
        parsed = parse_grid_response(row["text"])
        row["valid"] = not row["return_code"] and parsed.valid and not row.get("tool_item_count", 0)
        row["analyzable"] = not row["return_code"] and analyzable_response(row["text"]) and not row.get("tool_item_count",0)
        row["numbers"] = list(parsed.numbers) if row["analyzable"] else [1]*315
        row["repeat"] = int(row["sample_id"].rsplit("__", 1)[1])
    return rows


def development_rows():
    prior = [r for r in read_rows(ROOT/"data/public/gpt61-development-v1.jsonl")
             if r["run_id"] == "eight-replacement-v1"]
    fresh = read_rows(ROOT/"data/public/eight-optimized-development-v1.jsonl")
    training = prior + [r for r in fresh if r["run_id"] == "eight-replacement-enrollment-v2"]
    calibration = [r for r in fresh if r["run_id"] == "eight-replacement-calibration-v1"]
    ids = [r["sample_id"] for r in training+calibration]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate IDs across training and calibration")
    if Counter(r["requested_model"] for r in training) != Counter({m:72 for m in EIGHT_TARGET_MODELS}):
        raise ValueError("development must have 72 calls per model, including failures")
    if Counter(r["requested_model"] for r in calibration) != Counter({m:16 for m in EIGHT_TARGET_MODELS}):
        raise ValueError("calibration must have 16 calls per model, including failures")
    expected_prompt = hashlib.sha256((ROOT/"prompts/identity-replacement-v1.txt").read_text().strip().encode()).hexdigest()
    schema_hash = hashlib.sha256((ROOT/"schemas/identity-v3.json").read_bytes()).hexdigest()
    for r in training+calibration:
        if r["requested_model"] not in EIGHT_TARGET_MODELS or r["prompt_sha256"] != expected_prompt:
            raise ValueError("unexpected route or prompt")
        if r["runtime"] != "codex-cli 0.159.2" or r["reasoning_effort"] != "low":
            raise ValueError("runtime or reasoning drift")
        if r["output_schema_sha256"] != (None if r in calibration else schema_hash):
            raise ValueError("unexpected schema condition")
        if "thread_id" in r or "stderr_tail" in r:
            raise ValueError("private log fields in public corpus")
    valid_training = {tuple(r["numbers"]) for r in training if r["valid"]}
    duplicates = sum(tuple(r["numbers"]) in valid_training for r in calibration if r["valid"])
    if duplicates:
        raise ValueError("identical numeric responses across enrollment and calibration")
    return training, calibration


def development_selection(training, bank):
    groups_list = [feature_groups(r["numbers"], bank) for r in training]
    groups = {name: np.stack([g[name] for g in groups_list]) for name in groups_list[0]}
    labels = np.asarray([EIGHT_TARGET_MODELS.index(r["requested_model"]) for r in training])
    variants = []
    for raw_weight in (.25, 1):
        for structure_weight in (.5, 1, 2, 4):
            for order_weight in (0, .5):
                weights = {"bank":1, "raw":raw_weight, "structure":structure_weight, "order":order_weight}
                specs = [{"classifier":"ridge", "alpha":a, "gamma":1} for a in (.1,1,10)]
                specs += [{"classifier":"kernel", "alpha":.1, "gamma":g} for g in (.5,1,2)]
                for spec in specs:
                    predictions = [None]*len(training)
                    for fold in range(3):
                        held = [i for i,r in enumerate(training) if (r["repeat"]-1)%3 == fold]
                        fitted = [i for i,r in enumerate(training) if i not in held and r["valid"]]
                        xx, zz = [], []
                        for name, weight in weights.items():
                            if weight <= 0:
                                continue
                            f = groups[name]
                            mean, scale = f[fitted].mean(0), f[fitted].std(0)
                            scale[scale < 1e-12] = 1
                            multiplier = weight/np.sqrt(f.shape[1])
                            xx.append((f[fitted]-mean)/scale*multiplier)
                            zz.append((f[held]-mean)/scale*multiplier)
                        x, z = np.concatenate(xx,1), np.concatenate(zz,1)
                        targets = np.eye(8)[labels[fitted]]
                        target_mean = targets.mean(0)
                        k, cross = x@x.T, z@x.T
                        if spec["classifier"] == "kernel":
                            d = np.maximum((x*x).sum(1)[:,None]+(x*x).sum(1)[None,:]-2*k,0)
                            cd = np.maximum((z*z).sum(1)[:,None]+(x*x).sum(1)[None,:]-2*cross,0)
                            bandwidth = np.median(d[np.triu_indices(len(x),1)])
                            k = np.exp(-spec["gamma"]*d/bandwidth)
                            cross = np.exp(-spec["gamma"]*cd/bandwidth)
                        scores = cross@np.linalg.solve(k+spec["alpha"]*np.eye(len(x)),targets-target_mean)+target_mean
                        for i, guess in zip(held,np.argmax(scores,1)):
                            predictions[i] = EIGHT_TARGET_MODELS[int(guess)] if training[i]["valid"] else None
                    per = {m: sum(p==m for r,p in zip(training,predictions) if r["requested_model"]==m) for m in EIGHT_TARGET_MODELS}
                    variants.append({"group_weights":weights, **spec, "matches":sum(per.values()),"per_model":per})
    variants.sort(key=lambda v: (-min(v["per_model"].values()),-v["matches"],v["classifier"]!="ridge"))
    return {"schema":"traceone-eight-optimized-development-v1", "status":"inspected development, not independent accuracy",
            "folds":"repeat modulo 3, all scaling and bandwidth fitted on training folds only",
            "samples":len(training),"calls_per_model":dict(Counter(r["requested_model"] for r in training)),
            "valid_per_model":dict(Counter(r["requested_model"] for r in training if r["valid"])),
            "selection_rule":"maximize minimum per-model matches, then total matches; prefer ridge on ties",
            "selected":variants[0],"variants":variants}


def evaluate(rows, artifact, bank):
    predictions, details = [], []
    for r in rows:
        result = identify_text_optimized(r["text"] if not r["return_code"] and not r.get("tool_item_count",0) else "",
                                         artifact=artifact, bank=bank)
        predictions.append(result.label)
        details.append({"sample_id":r["sample_id"],"requested_model":r["requested_model"],"result":result.to_dict()})
    per = {}
    for m in EIGHT_TARGET_MODELS:
        indices = [i for i,r in enumerate(rows) if r["requested_model"]==m]
        count, correct = len(indices), sum(predictions[i]==m for i in indices)
        per[m] = {"samples":count,"matches":correct,"match_rate":correct/count if count else 0,
                  "unknown":sum(predictions[i] is None for i in indices),
                  "format_compliant":sum(rows[i]["valid"] for i in indices)}
    return {"samples":len(rows),"matches":sum(v["matches"] for v in per.values()),"per_model":per,
            "samples_detail":details}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--select", action="store_true")
    parser.add_argument("--fit", action="store_true")
    parser.add_argument("--responses", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    training, calibration = development_rows()
    bank = load_bank()
    if args.select:
        report = development_selection(training, bank)
        (ROOT/"data/eight-optimized-development-v1.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report["selected"]))
    elif args.fit:
        spec = json.loads((ROOT/"data/eight-optimized-development-v1.json").read_text())["selected"]
        artifact = fit_optimized([(r["requested_model"],r["numbers"]) for r in training if r["valid"]],
                                 [(r["requested_model"],r["numbers"]) for r in calibration if r["analyzable"]], bank,
                                 group_weights=spec["group_weights"],alpha=spec["alpha"],classifier=spec["classifier"],gamma=spec["gamma"])
        rendered = json.dumps(artifact,separators=(",",":"))+"\n"
        for path in (ROOT/"src/traceone/data/codex_low_v8_optimized.json",ROOT/"dist/data/codex_low_v8_optimized.json"):
            path.write_text(rendered)
        print(json.dumps({"training":artifact["training_rows"],"calibration":artifact["calibration_rows"],"bytes":len(rendered)}))
    elif args.responses:
        result = evaluate(read_rows(args.responses), load_optimized(), bank)
        if args.output:
            args.output.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps({k:v for k,v in result.items() if k!="samples_detail"}))
    else:
        print(json.dumps({"training_calls":len(training),"calibration_calls":len(calibration),"conditions_verified":True}))


if __name__ == "__main__":
    main()
