# Results and evidence ledger

[简体中文](results.md) | [English](results.en.md)

## Release result

The final release is `release-candidate-v8` plus `confirmation-v7`: freeze first,
collect second, reveal last.

- All 75 calls returned code 0 and all 75 sample IDs were unique.
- 75/75 conformed to the strict 9×35 Schema. Prompt/Schema hashes, runtime,
  reasoning, and wrapper were constant within the batch.
- TraceOne `supported`: 75/75 with 75/75 coverage; Wilson 95% CI 95.13%–100%.
- Per model: 5.5, Luna, Terra, Sol, and Astra were all 15/15.

These are requested-label agreements, not independently attested served weights.

## Same-response ModelTrace comparator

- TraceOne one-call: 75/75.
- ModelTrace closed-set one-call: 74/75. Its only error was Sol, so Sol was 14/15
  and the other four models were 15/15.
- ModelTrace three-call: all 25 disjoint triplets correct, 5/5 per model.

Paired discordance between TraceOne and ModelTrace one-call is only 1 versus 0;
the one-sided exact sign/McNemar p-value is 0.5. This establishes neither a
statistically significant accuracy advantage nor formal non-inferiority. The supported
claim is narrower: every per-model point estimate was no lower in this batch, Sol
gained one item, each decision used one call instead of three, and the one- and
three-call arms both had a 100% accuracy point estimate. The three-call arm has only
25 decisions, versus 75 one-call decisions.

Evidence:

- [confirmation-v7 evaluation](../data/confirmation-v7-evaluation.json)
- [confirmation-v7 head-to-head](../data/confirmation-v7-head-to-head.json)
- [public confirmation responses](../data/public/confirmation-v7.jsonl)
- [release manifest](../config/release-v0.1.0.json)

## Open-world development

Each fold deletes one complete excluded label before fitting. Across 8×36=288
truly held-label samples:

- TraceOne `supported`: 24/288 false accepts, 8.33%; Wilson 95% CI 5.66%–12.10%.
- TraceOne `enrolled`: 59/288, 20.49%; Wilson 95% CI 16.23%–25.52%.
- ModelTrace closed set: 288/288 false identifications because valid inputs have no
  `unknown` branch.
- The same 75 target holdout rows are reused across eight gallery folds. Supported
  accuracy averages 98.33% and bottoms at 97.33%; these are not 600 independent rows.
- Most errors are GPT-5.4: `supported` accepts 20/36.

These are tuned development data and the unknowns come from the upstream corpus,
not a new-provider blind test. They show a large reduction in forced closed-set
naming, not universal OOD resolution. See
[open-world-development-v2.json](../data/open-world-development-v2.json).

The old v6 result of 2/288 for excluded labels inside a full bank is now correctly
named registered-distractor rejection, because those labels helped build that bank.

## Failures during development

- Schema-free v2 produced a real Luna out-of-range truncation, motivating strict
  9×35 Schema output.
- Confirmation-v2 scored 73/75 with Sol at 13/15 and failed its gate.
- The 190-row adapter scored 71/75 on confirmation-v3 and failed.
- Confirmation-v4 scored 73/75 with Sol at 13/15 and failed.
- The v6 adapter scored 74/75 on confirmation-v5. The only failure was a 240-second
  Astra timeout; every one of the 74 valid responses was correct.
- v7 target support scored 71/75 on confirmation-v6: two adapter errors plus two
  correct Astra responses rejected by support. It failed the per-class gate and
  only then became v8 development data.
- v8 selected alpha=1. Whole-collection CV was 412/415 versus 411/415 for alpha=30.
  KNN, LDA, and RBF prototypes did not exceed it; see
  [adapter-model-exploration.json](../data/adapter-model-exploration.json).

Failed runs are never pooled into the final confirmation. To keep the public release
surface small, raw failed batches are omitted from the curated main branch; their
denominators, key results, and rejection reasons remain in this ledger.

## Active-probe negative result

We tested 128 pairwise binary choices in one response. Random-pair v1 reached 24/25
in a small leave-one-out whose hyperparameters were selected on those same development
rows; v2 pairs optimized from 340 enrollment rows fell to 22/25. Neither reached the
release gate. The negative result remains in this ledger; exploratory prompts, scripts,
and raw evaluations are omitted from the curated release branch. It is not a blind
confirmation claim.

## Degradation status

The repository implements a full test; it does not invent an observed service
degradation result.

- Under regression=0.10, improvement=0.02, and minimum effect=0.05, the 48-item
  canary has only 29.06% exact detection power.
- The 192-item v2 canary has 89.76% power under the same assumptions.
- The implementation reports paired regressions/improvements, invalid and missing
  outcomes, exact one-sided McNemar, and Holm-corrected family tests.

Power depends on preregistered probabilities. Real monitoring must record model,
provider, runtime, reasoning, wrapper, date, and retry policy for both runs.
