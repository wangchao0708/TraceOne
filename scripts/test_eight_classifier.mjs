import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { identifyWithArtifacts, TARGET_MODELS } from "../dist/traceone.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => JSON.parse(fs.readFileSync(path.join(root, relative), "utf8"));
const bank = read("dist/data/unified_bank_v2_16.json");
const adapter = read(process.env.TRACEONE_EIGHT_ARTIFACT ?? "dist/data/codex_low_v8_optimized.json");
if (JSON.stringify(adapter.models) !== JSON.stringify(TARGET_MODELS)) throw new Error("eight target order differs");
const responses = fs.readFileSync(path.join(root, process.env.TRACEONE_EIGHT_RESPONSES ?? "data/public/confirmation-v12.jsonl"), "utf8")
  .trim().split("\n").map(JSON.parse);
const expected = read(process.env.TRACEONE_EIGHT_EVALUATION ?? "data/confirmation-v12-evaluation.json");
const byId = new Map(expected.samples_detail.map((row) => [row.sample_id, row.result]));
let maximumError = 0;
function close(actual, wanted, name) {
  if (actual === null || wanted === null) {
    if (actual !== wanted) throw new Error(`${name}: null mismatch`);
    return;
  }
  const error = Math.abs(actual - wanted);
  maximumError = Math.max(maximumError, error);
  if (!Number.isFinite(error) || error > 1e-9) throw new Error(`${name}: numeric error ${error}`);
}
for (const row of responses) {
  const text = row.return_code || row.tool_item_count ? "" : row.text;
  const result = identifyWithArtifacts(text, { bank, adapter });
  const wanted = byId.get(row.sample_id);
  if (!wanted) throw new Error(`missing expected row ${row.sample_id}`);
  for (const [actual, expectedValue, name] of [
    [result.status, wanted.status, "status"], [result.label, wanted.label, "label"],
    [result.supportPath, wanted.support_path, "support path"],
    [result.parsed.valid, wanted.adapter.outer_guard.format_compliant, "format"],
    [result.parsed.numbers.length, wanted.adapter.outer_guard.usable_numbers, "usable count"],
  ]) if (actual !== expectedValue) throw new Error(`${row.sample_id}: ${name} differs`);
  for (const [actual, value, name] of [
    [result.adapter.adapterMargin, wanted.adapter.adapter_margin, "margin"],
    [result.supportDistance, wanted.support_distance, "distance"],
    [result.supportThreshold, wanted.support_threshold, "threshold"],
    [result.supportPValue, wanted.support_p_value, "p-value"],
  ]) close(actual, value, `${row.sample_id}: ${name}`);
  for (const model of TARGET_MODELS) {
    if (model in wanted.adapter.adapter_scores) close(result.adapter.adapterScores[model], wanted.adapter.adapter_scores[model], model);
  }
}
console.log(JSON.stringify({ samples: responses.length, classes: 8, numericTolerance: 1e-9, maximumError }));
