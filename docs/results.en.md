# Results and evidence ledger

[简体中文](results.md) | [English](results.en.md)

## Second frozen seven-model confirmation: gate failed again

`release-candidate-v10` was frozen at 17:06:12 UTC on September 23, 2026,
before registering `confirmation-v9`. All 105 calls (15 per route) completed
and conformed to the strict Schema with the same prompt, runtime, Low reasoning,
and wrapper. TraceOne `supported` matched 98/105: 5.5 and 5.6 Luna were 14/15;
5.6 Terra, 6 Astra, and 6 Luna were 15/15; 5.6 Sol was 13/15 and 6 Sol was
12/15. This failed the prespecified ≥14/15-per-route gate. V10 therefore cannot
serve as a validated seven-route release.

On those same responses, ModelTrace one-call matched 96/105 and disjoint
three-call decisions matched 35/35. TraceOne gained two one-call items overall,
but that does not prove comprehensive per-route superiority. Every decision is
retained in the [evaluation](../data/confirmation-v9-evaluation.json) and
[head-to-head](../data/confirmation-v9-head-to-head.json). Only after this failure
was recorded may `confirmation-v9` become development data for a later version.

## First frozen seven-model confirmation: gate failed

`release-candidate-v9` was frozen at 16:29:50 UTC on September 23, 2026; the
first `confirmation-v8` call followed at 16:32:05. All 105 calls (15 per route)
completed, conformed to the strict Schema, and shared one Codex runtime, Low
reasoning, prompt, and wrapper.

TraceOne `supported` matched 101/105 (96.19%). GPT-5.5, all three GPT-5.6 routes,
and GPT-6 Sol were each 15/15; GPT-6 Astra and Luna were each 13/15. This failed
the preregistered minimum of 14/15 per route. Two errors were outer-guard
rejections and two were adapter misclassifications. See every row in
[confirmation-v8-evaluation.json](../data/confirmation-v8-evaluation.json).

The updated ModelTrace closed-set one-call comparator also matched 101/105, with
5.6 Sol at 14/15, 6 Astra at 13/15, and 6 Luna at 14/15. Its disjoint three-call
arm matched 35/35. These requested-route point estimates do not prove served
weights or comprehensive superiority for TraceOne. The paired decisions are in
[confirmation-v8-head-to-head.json](../data/confirmation-v8-head-to-head.json).
The failed batch may be used for a later development iteration only after the
v9 gate has been recorded as failed.

## 0.2.0 seven-model development evidence

Only after the first confirmation failure was recorded did `confirmation-v8`
become v10 development data. Its 15 rows per route were held out in three folds;
each fit used the previous 581 rows plus the other 10 rows per route. The selected
rule matched 103/105 held-out rows, at least 14/15 per route. This is not an
independent confirmation. The final fit uses 686 rows, 98 per route, and was frozen
before new collection in
[release-candidate-v10.json](../config/release-candidate-v10.json). Development
variants and errors are in
[seven-model-development-v2.json](../data/seven-model-development-v2.json).

On the same nine-label held-label stress test, new `supported` still falsely
accepted 34/324, while `enrolled` accepted 52/324. GPT-5.4 remained at 19/36
and Claude Opus 5.5 at 10/36. These data were inspected while tuning, not a new
blind OOD result; see
[open-world-v4-development.json](../data/open-world-v4-development.json).
The new plan [confirmation-v9.json](../config/confirmation-v9.json) retains the
≥14/15-per-route gate.

The author's excellent updated 16-model ModelTrace bank (commit
`55a2e4a55170423b484d701e9a82ab62b268c811`) includes 36 Low-reasoning
reference responses each for GPT-6 Sol and Luna. Building on that open work,
TraceOne collected 83 additional independent enrollment responses per new route
with the same 9×35 question. Together with 83 rows per original route, training
is balanced at 581 rows. The two collection epochs used different Codex runtimes,
which are recorded per model.

The 68/15 development split held out 105 responses. `supported` matched 100/105;
`enrolled` matched 102/105. GPT-6 Sol was 15/15. GPT-6 Luna was 13/15 under
`supported`, with one classification error and one support rejection; the historical
Astra route was also 13/15. These failures remain visible in
[seven-model-development-v1.json](../data/seven-model-development-v1.json).

Nine held-out labels with 36 rows each produced 34/324 false accepts under
`supported` (10.49%) and 51/324 under `enrolled` (15.74%). A closed-set ModelTrace
decision necessarily names all 324 valid unknown inputs. GPT-5.4 (19/36) and
Claude Opus 5.5 (10/36) are the largest weaknesses. These are upstream-corpus
development data, not a blind independent-provider test. The label set differs
from the historical 24/288 study, so those percentages are not directly
comparable. See [open-world-development-v3.json](../data/open-world-development-v3.json).

The first 581-row candidate was frozen in
[release-candidate-v9.json](../config/release-candidate-v9.json) before collecting
the fresh 15-per-route batch registered in
[confirmation-v8.json](../config/confirmation-v8.json), which then failed its gate.
Development results do not substitute for confirmation evidence.

## Historical 0.1.0 five-model result

The 0.1.0 release used `release-candidate-v8` plus `confirmation-v7`: freeze first,
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
