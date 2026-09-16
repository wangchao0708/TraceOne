export const TARGET_MODELS = [
  "gpt-5.5",
  "gpt-5.6-luna",
  "gpt-5.6-terra",
  "gpt-5.6-sol",
  "gpt-6-astra",
];

const VALUE_MIN = 1;
const VALUE_MAX = 355;
const DIMENSION = 355;
const ALPHA = 0.5;
const MINIMUM_NUMBERS = 280;

const OUTER_GUARD = Object.freeze({
  minimumSimilarity: 0.52,
  minimumMargin: 0,
  allowMarginalFallback: true,
  fallbackMinimumSimilarity: 0.54,
  fallbackMinimumMargin: 0.10,
  fallbackMaximumFusedGap: 0.075,
});

const mean = (values) => values.reduce((sum, value) => sum + value, 0) / values.length;

function standardize(values) {
  const center = mean(values);
  const variance = values.reduce((sum, value) => sum + (value - center) ** 2, 0) / values.length;
  const scale = Math.max(Math.sqrt(variance), 1e-12);
  return values.map((value) => (value - center) / scale);
}

function dot(left, right) {
  let total = 0;
  for (let index = 0; index < left.length; index += 1) total += left[index] * right[index];
  return total;
}

function norm(values) {
  return Math.sqrt(dot(values, values));
}

function normalize(values) {
  const scale = Math.max(norm(values), 1e-12);
  return values.map((value) => value / scale);
}

function removeBasis(vector, basis) {
  const projected = vector.slice();
  for (const direction of basis) {
    const coefficient = dot(projected, direction);
    for (let index = 0; index < projected.length; index += 1) {
      projected[index] -= coefficient * direction[index];
    }
  }
  return projected;
}

function softmax(values) {
  const maximum = Math.max(...values);
  const weights = values.map((value) => Math.exp(value - maximum));
  const total = weights.reduce((sum, value) => sum + value, 0);
  return weights.map((value) => value / total);
}

export function parseGridResponse(text) {
  let payload;
  try {
    payload = JSON.parse(text);
  } catch (error) {
    return {
      numbers: [],
      valid: false,
      errors: [`invalid_json:${error instanceof Error ? error.message : "unknown"}`],
      observedItems: 0,
      integerItems: 0,
    };
  }

  if (
    payload &&
    typeof payload === "object" &&
    !Array.isArray(payload) &&
    Object.keys(payload).length === 1 &&
    Object.hasOwn(payload, "numbers")
  ) {
    payload = payload.numbers;
  }

  if (!Array.isArray(payload)) {
    return { numbers: [], valid: false, errors: ["missing_grid_array"], observedItems: 0, integerItems: 0 };
  }

  const errors = [];
  if (payload.length !== 9) errors.push(`wrong_row_count:${payload.length}`);
  const flattened = [];
  payload.forEach((row, rowIndex) => {
    if (!Array.isArray(row)) {
      errors.push(`row_${rowIndex}_not_array`);
      return;
    }
    if (row.length !== 35) errors.push(`row_${rowIndex}_wrong_count:${row.length}`);
    flattened.push(...row);
  });

  const numbers = [];
  let integerItems = 0;
  flattened.forEach((value, index) => {
    if (!Number.isInteger(value)) {
      errors.push(`item_${index}_not_integer`);
      return;
    }
    integerItems += 1;
    if (value < VALUE_MIN || value > VALUE_MAX) {
      errors.push(`item_${index}_out_of_range`);
      return;
    }
    numbers.push(value);
  });
  if (flattened.length !== 315) errors.push(`wrong_count:${flattened.length}`);

  return {
    numbers,
    valid: errors.length === 0,
    errors,
    observedItems: flattened.length,
    integerItems,
  };
}

function countNumbers(numbers) {
  const counts = Array(DIMENSION).fill(0);
  for (const number of numbers) counts[number - 1] += 1;
  return counts;
}

function hellingerFeature(counts) {
  const smoothed = counts.map((count) => count + ALPHA);
  const total = smoothed.reduce((sum, value) => sum + value, 0);
  return smoothed.map((value) => Math.sqrt(value / total));
}

function orderedBlockFeature(numbers) {
  const result = [];
  const baseSize = Math.floor(numbers.length / 4);
  const remainder = numbers.length % 4;
  let start = 0;
  for (let chunkIndex = 0; chunkIndex < 4; chunkIndex += 1) {
    const size = baseSize + (chunkIndex < remainder ? 1 : 0);
    const chunk = numbers.slice(start, start + size);
    start += size;
    const counts = Array(16).fill(0);
    for (const value of chunk) {
      const bin = Math.min(15, Math.floor(((value - 1) * 16) / 355));
      counts[bin] += 1;
    }
    const total = chunk.length + 0.5 * 16;
    result.push(...counts.map((count) => Math.sqrt((count + 0.5) / total)));
  }

  const lastDigits = Array(10).fill(0);
  for (const value of numbers) lastDigits[value % 10] += 1;
  const digitTotal = numbers.length + 0.5 * 10;
  result.push(...lastDigits.map((count) => Math.sqrt((count + 0.5) / digitTotal)));
  return result;
}

function marginalScores(counts, bank) {
  const artifact = bank.robust.hellinger;
  let projected = hellingerFeature(counts).map(
    (value, index) => (value - artifact.feature_mean[index]) / artifact.feature_scale[index],
  );
  if (artifact.nuisance_basis.length) projected = removeBasis(projected, artifact.nuisance_basis);
  projected = normalize(projected);
  return standardize(artifact.centroids.map((centroid) => dot(projected, centroid)));
}

function orderedScores(numbers, bank) {
  const artifact = bank.robust.ordered_blocks;
  const feature = orderedBlockFeature(numbers);
  const standardized = feature.map(
    (value, index) => (value - artifact.feature_mean[index]) / artifact.feature_scale[index],
  );
  const normalized = normalize(standardized);

  const maximums = Array(bank.robust.model_order.length).fill(-Infinity);
  for (const environment of artifact.environment_centroids) {
    environment.forEach((centroid, modelIndex) => {
      maximums[modelIndex] = Math.max(maximums[modelIndex], dot(normalized, centroid));
    });
  }
  const templateScores = standardize(maximums);

  let projected = standardized.slice();
  if (artifact.nuisance_basis.length) projected = removeBasis(projected, artifact.nuisance_basis);
  projected = normalize(projected);
  const nuisanceScores = standardize(artifact.centroids.map((centroid) => dot(projected, centroid)));
  return standardize(templateScores.map((value, index) => 0.5 * value + 0.5 * nuisanceScores[index]));
}

function scoreNumbers(numbers, bank) {
  const counts = countNumbers(numbers);
  const marginal = marginalScores(counts, bank);
  const orderedArtifact = bank.robust.ordered_blocks;
  const weight = Number(orderedArtifact?.weight ?? 0);
  if (!orderedArtifact || weight === 0) return { fused: marginal.slice(), marginal, counts };
  const ordered = orderedScores(numbers, bank);
  return {
    fused: marginal.map((value, index) => (1 - weight) * value + weight * ordered[index]),
    marginal,
    counts,
  };
}

function jsSimilarity(left, right) {
  const leftTotal = left.reduce((sum, value) => sum + value, 0);
  if (!leftTotal) return 0;
  const rightTotal = right.reduce((sum, value) => sum + value, 0) + ALPHA * DIMENSION;
  let divergenceLeft = 0;
  let divergenceRight = 0;
  for (let index = 0; index < DIMENSION; index += 1) {
    const p = left[index] / leftTotal;
    const q = (right[index] + ALPHA) / rightTotal;
    const midpoint = (p + q) / 2;
    if (p > 0) divergenceLeft += p * Math.log(p / midpoint);
    divergenceRight += q * Math.log(q / midpoint);
  }
  const divergence = (divergenceLeft + divergenceRight) / 2;
  return 1 - Math.sqrt(divergence / Math.log(2));
}

function adapterFeature(numbers, bank) {
  const { fused, marginal, counts } = scoreNumbers(numbers, bank);
  const models = new Map(bank.models.map((model) => [model.id, model]));
  const similarities = bank.robust.model_order.map((model) => jsSimilarity(counts, models.get(model).counts));
  return [...fused, ...marginal, ...similarities];
}

function classifyOuter(parsed, bank) {
  if (parsed.numbers.length < MINIMUM_NUMBERS) {
    return {
      status: "unknown",
      label: null,
      topCandidate: null,
      marginalCandidate: null,
      usableNumbers: parsed.numbers.length,
      formatCompliant: parsed.valid,
      parseErrors: parsed.errors,
      guardReasons: ["insufficient_usable_numbers"],
      similarity: null,
      scoreMargin: null,
      marginalScoreMargin: null,
      decisionPath: null,
      candidates: [],
    };
  }

  const modelOrder = bank.robust.model_order;
  const models = new Map(bank.models.map((model) => [model.id, model]));
  const { fused, marginal, counts } = scoreNumbers(parsed.numbers, bank);
  const beta = Number(bank.calibration?.["1"]?.beta ?? 1);
  const probabilities = softmax(fused.map((value) => beta * value));
  const candidates = modelOrder.map((model, index) => ({
    model,
    fusedScore: fused[index],
    marginalScore: marginal[index],
    profileSimilarity: jsSimilarity(counts, models.get(model).counts),
    closedSetProbability: probabilities[index],
  })).sort((left, right) => right.fusedScore - left.fusedScore);

  const top = candidates[0];
  const margin = top.fusedScore - candidates[1].fusedScore;
  const marginalOrder = modelOrder.map((_, index) => index).sort((left, right) => marginal[right] - marginal[left]);
  const marginalCandidate = modelOrder[marginalOrder[0]];
  const marginalMargin = marginal[marginalOrder[0]] - marginal[marginalOrder[1]];
  const candidateByModel = new Map(candidates.map((candidate) => [candidate.model, candidate]));

  let fallbackLabel = null;
  if (
    OUTER_GUARD.allowMarginalFallback &&
    !TARGET_MODELS.includes(top.model) &&
    TARGET_MODELS.includes(marginalCandidate) &&
    candidateByModel.get(marginalCandidate).profileSimilarity >= OUTER_GUARD.fallbackMinimumSimilarity &&
    marginalMargin >= OUTER_GUARD.fallbackMinimumMargin &&
    margin <= OUTER_GUARD.fallbackMaximumFusedGap
  ) fallbackLabel = marginalCandidate;

  const reasons = [];
  if (!TARGET_MODELS.includes(top.model) && fallbackLabel === null) reasons.push("guard_model_won");
  if (fallbackLabel === null && top.profileSimilarity < OUTER_GUARD.minimumSimilarity) reasons.push("low_absolute_similarity");
  if (fallbackLabel === null && margin < OUTER_GUARD.minimumMargin) reasons.push("low_score_margin");

  const label = fallbackLabel ?? (reasons.length === 0 ? top.model : null);
  return {
    status: label ? "identified" : "unknown",
    label,
    topCandidate: top.model,
    marginalCandidate,
    usableNumbers: parsed.numbers.length,
    formatCompliant: parsed.valid,
    parseErrors: parsed.errors,
    guardReasons: reasons,
    similarity: candidateByModel.get(label ?? top.model).profileSimilarity,
    scoreMargin: margin,
    marginalScoreMargin: marginalMargin,
    decisionPath: label ? (fallbackLabel ? "marginal_fallback" : "fused") : null,
    candidates,
  };
}

function scoreAdapter(numbers, bank, adapter) {
  const feature = adapterFeature(numbers, bank);
  const standardized = feature.map(
    (value, index) => (value - adapter.feature_mean[index]) / adapter.feature_scale[index],
  );
  return adapter.target_mean.map((center, modelIndex) => {
    let score = center;
    for (let featureIndex = 0; featureIndex < standardized.length; featureIndex += 1) {
      score += standardized[featureIndex] * adapter.weights[featureIndex][modelIndex];
    }
    return score;
  });
}

function classifyAdapted(parsed, bank, adapter) {
  const outer = classifyOuter(parsed, bank);
  if (outer.status !== "identified") {
    return { status: "unknown", label: null, adapterMargin: null, adapterScores: {}, outerGuard: outer };
  }
  const scores = scoreAdapter(parsed.numbers, bank, adapter);
  const order = scores.map((_, index) => index).sort((left, right) => scores[left] - scores[right]);
  const margin = scores[order.at(-1)] - scores[order.at(-2)];
  const label = adapter.models[order.at(-1)];
  const scoreMap = Object.fromEntries(adapter.models.map((model, index) => [model, scores[index]]));
  if (margin < Number(adapter.minimum_margin)) {
    return { status: "unknown", label: null, adapterMargin: margin, adapterScores: scoreMap, outerGuard: outer };
  }
  return { status: "identified", label, adapterMargin: margin, adapterScores: scoreMap, outerGuard: outer };
}

function supportScore(numbers, label, bank, support) {
  const index = support.models.indexOf(label);
  const feature = adapterFeature(numbers, bank);
  const standardized = feature.map(
    (value, featureIndex) => (value - support.feature_mean[featureIndex]) / support.feature_scale[featureIndex],
  );
  const residual = standardized.map((value, featureIndex) => value - support.centroids[index][featureIndex]);
  let distance = 0;
  for (let row = 0; row < residual.length; row += 1) {
    for (let column = 0; column < residual.length; column += 1) {
      distance += residual[row] * support.precision[row][column] * residual[column];
    }
  }
  const threshold = Number(support.distance_thresholds[index]);
  const calibration = support.calibration_distances[index];
  const pValue = (1 + calibration.filter((value) => value >= distance).length) / (calibration.length + 1);
  return { distance, threshold, pValue, index };
}

export function identifyWithArtifacts(text, { bank, adapter, support }) {
  const parsed = parseGridResponse(text);
  const base = classifyAdapted(parsed, bank, adapter);
  if (base.status !== "identified" || !base.label) {
    return {
      status: "unknown",
      label: null,
      supportPassed: null,
      supportDistance: null,
      supportThreshold: null,
      supportPValue: null,
      supportPath: null,
      adapter: base,
      parsed,
    };
  }

  const score = supportScore(parsed.numbers, base.label, bank, support);
  const rescueThreshold = Number(support.rescue_margin_thresholds[score.index]);
  const distancePassed = score.distance <= score.threshold;
  const marginRescue = base.adapterMargin !== null && base.adapterMargin >= rescueThreshold;
  const passed = distancePassed || marginRescue;
  return {
    status: passed ? "identified" : "unknown",
    label: passed ? base.label : null,
    supportPassed: passed,
    supportDistance: score.distance,
    supportThreshold: score.threshold,
    supportPValue: score.pValue,
    supportPath: distancePassed ? "distance" : marginRescue ? "high_margin_rescue" : "rejected",
    adapter: base,
    parsed,
  };
}

let artifactPromise;

export function loadArtifacts() {
  if (!artifactPromise) {
    artifactPromise = Promise.all([
      fetch(new URL("./data/unified_bank.json", import.meta.url)).then((response) => response.json()),
      fetch(new URL("./data/codex_low_v4_adapter_415.json", import.meta.url)).then((response) => response.json()),
      fetch(new URL("./data/codex_low_v4_support_415.json", import.meta.url)).then((response) => response.json()),
    ]).then(([bank, adapter, support]) => ({ bank, adapter, support }));
  }
  return artifactPromise;
}

export function targetRelativeWeights(adapterScores) {
  return softmax(TARGET_MODELS.map((model) => Number(adapterScores[model] ?? -Infinity)));
}
