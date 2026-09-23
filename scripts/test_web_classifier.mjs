import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { identifyWithArtifacts, parseGridResponse } from "../dist/traceone.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const readJson = (relativePath) => JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
const artifacts = {
  bank: readJson("dist/data/unified_bank_v2_16.json"),
  adapter: readJson("dist/data/codex_low_v5_adapter_581.json"),
  support: readJson("dist/data/codex_low_v5_support_581.json"),
};
const readJsonl = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8")
  .trim()
  .split("\n")
  .map((line) => JSON.parse(line));

const close = (left, right, field, sampleId) => {
  if (Math.abs(left - right) > 1e-9) {
    throw new Error(`${sampleId}: ${field} differs: ${left} vs ${right}`);
  }
};

function verifyRows(rows, expectedRows) {
  const expectedById = new Map(expectedRows.map((row) => [row.sample_id, row.supported]));
  for (const row of rows) {
    const result = identifyWithArtifacts(row.text, artifacts);
    const wanted = expectedById.get(row.sample_id);
    if (!wanted) throw new Error(`missing expected result for ${row.sample_id}`);
    const fields = [
      [result.status, wanted.status, "status"],
      [result.label, wanted.label, "label"],
      [result.adapter.outerGuard.topCandidate, wanted.top_candidate, "top_candidate"],
      [result.adapter.outerGuard.marginalCandidate, wanted.marginal_candidate, "marginal_candidate"],
      [result.parsed.valid, wanted.format_compliant, "format_compliant"],
      [result.parsed.numbers.length, wanted.usable_numbers, "usable_numbers"],
      [result.supportPath, wanted.decision_path, "support_path"],
    ];
    for (const [actual, expectedValue, field] of fields) {
      if (actual !== expectedValue) {
        throw new Error(`${row.sample_id}: ${field} differs: ${actual} vs ${expectedValue}`);
      }
    }
    close(result.adapter.outerGuard.similarity, wanted.similarity, "similarity", row.sample_id);
    close(result.adapter.outerGuard.scoreMargin, wanted.score_margin, "score_margin", row.sample_id);
    close(result.adapter.outerGuard.marginalScoreMargin, wanted.marginal_score_margin, "marginal_score_margin", row.sample_id);
    close(result.adapter.adapterMargin, wanted.adapter_margin, "adapter_margin", row.sample_id);
    close(result.supportDistance, wanted.support_distance, "support_distance", row.sample_id);
    close(result.supportThreshold, wanted.support_threshold, "support_threshold", row.sample_id);
    close(result.supportPValue, wanted.support_p_value, "support_p_value", row.sample_id);
  }
  return rows.length;
}

const expectedRows = [
  ...readJson("data/confirmation-v8-evaluation.json").samples,
  ...readJson("data/seven-model-regression-v1.json").samples,
];
const evidenceFiles = [
  "data/public/confirmation-v7.jsonl",
  "data/public/confirmation-v8.jsonl",
  "data/public/web-prompt-v1-pilot.jsonl",
  "data/public/gpt6-web-pilot-v1.jsonl",
];
const counts = evidenceFiles.map((file) => verifyRows(readJsonl(file), expectedRows));

const malformed = parseGridResponse("```json\n[1, 2, 3]\n```");
if (malformed.valid || !malformed.errors[0]?.startsWith("invalid_json:")) {
  throw new Error("strict parser accepted fenced JSON");
}

console.log(JSON.stringify({
  samples: counts.reduce((total, count) => total + count, 0),
  historical_confirmation: counts[0],
  seven_model_confirmation: counts[1],
  historical_web_pilot: counts[2],
  new_model_web_pilot: counts[3],
  numeric_tolerance: 1e-9,
  strict_invalid_case: "passed",
}));
