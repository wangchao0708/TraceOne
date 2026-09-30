# Results and evidence ledger

[简体中文](results.md) | [English](results.en.md)

## Eight-route v12 experiment: web-condition confirmation failed; repository-only update

This version adds concurrent enrollment, separate calibration and fresh
confirmation through Codex subscription CLI 0.159.2 with Low reasoning. No paid API
or reset credit was used; each call still requests 315 integers in one question.
New enrollment contains 384 calls, 380 successes and four timeouts. Together with
192 prior same-prompt development calls, 576 calls enter the development denominator.
Selection over 96 candidates prioritized the lowest per-route match count, then
total matches, selecting bank/raw/repetition-order ridge with alpha=1 and group
weights 1/1/0.5. Inspected cross-fit matched 543/576, Astra 59/72 and 6.1 Sol 58/72.

The fit uses 571 rows: four timeouts and one conservatively flagged CLI event are
excluded from fitting, never from the development denominator. The latter records
an `error` item that an early collector counted as `tool_item_count`; this is not
evidence of actual tool execution. The original record is retained. The collector
now records errors separately. Web-condition calibration made 128 calls without
Schema; 124 meet the frozen bounded-tolerance input rule and four cannot be analyzed.
Support uses independent class-conditional maximum calibration distances, without
any high-margin bypass.

After [freezing v12](../config/release-candidate-v12.json) at commit `5b70968`, 120
fresh [confirmation calls](../data/public/confirmation-v12.jsonl) were collected.
All succeeded and emitted no tool-execution items. The web, CLI, and confirmation
use the identical self-contained question without additional Schema:

- GPT-5.5: 15/15 (100%); GPT-5.6 Luna: 14/15 (93.3%).
- GPT-5.6 Terra: 15/15 (100%); GPT-5.6 Sol: 14/15 (93.3%).
- GPT-6 Astra: 9/15 (60%); GPT-6 Sol: 14/15 (93.3%).
- GPT-6 Luna: 10/15 (66.7%); GPT-6.1 Sol: 10/15 (66.7%).
- Total 101/120 (84.2%), failing the ≥14/15 gate for every route. All nine
  abstentions count as misses.
- Strict JSON/shape/range compliance: 61/120 (50.8%); frozen tolerant analysis
  accepts 114/120 responses.

All six Astra errors were assigned to 6.1 Sol. For 6.1 Sol, three were assigned
to Astra and two rejected. 6 Luna had two refusals of the independence/randomness
requirement, two JSON structure errors and one support rejection. Development
94.3% and a working eighth UI option are not evidence of overall improvement;
these errors cannot establish degradation. The repository publishes the frozen
eight-route experimental source and retains the historical seven-class method.
The public site is not redeployed and retains the seven-route baseline.
All 120 Python/JavaScript outputs agree field by field,
with maximum numeric error about 3.4×10⁻¹³.

[Development corpus](../data/public/eight-optimized-development-v1.jsonl),
[selection](../data/eight-optimized-development-v1.json) and
[confirmation evaluation](../data/confirmation-v12-evaluation.json) retain complete
denominators and a private-field exclusion policy. The corpus also includes 24
discarded range-pilot calls; they never enter the final fit/calibration/confirmation.
The candidate has no independent real unseen-model OOD confirmation; synthetic
uniform-number stress tests cannot substitute for it.

## GPT-6.1 Sol expansion development: not qualified for release

The following is the historical first 489-call stage. Decisions about not starting
confirmation refer to that stage; the later failed v12 confirmation is recorded
separately above, without overwriting historical evidence.

On September 30, 2026, 489 real subscription calls were collected with Codex CLI
0.159.2, Low reasoning, and the isolated wrapper. Every call used one 315-choice
question and returned successfully. All 473 Schema-constrained responses were
strictly compliant; only 5/16 self-contained web responses were strictly compliant.
Format deviations and abstentions remain in their denominators. Public exports
remove task IDs and stderr: [responses](../data/public/gpt61-development-v1.jsonl),
[manifest](../data/public/gpt61-development-v1.manifest.json), and
[evaluation](../data/gpt61-development-v1.json).

The original prompt collected 113 enrollment responses for 6.1 Sol plus 15 new
development responses for each of eight routes. The earlier seven routes use
historical 113-per-route enrollment from older runtimes; this is not a concurrent
eight-route reference bank. The unchanged 16-model bank is a feature extractor,
not a fabricated 17-centroid bank. Three-fold eight-class ridge plus support,
with alpha=1 and raw weight=0.25, produced the first column below.

A revised, still single-call 315-choice prompt explicitly permits independent
repeated choices. Each of eight routes supplied 24 development responses, split
into three chronological balanced folds. The best candidate uses bank features,
raw frequencies, and repetition/sequence statistics with RBF kernel ridge
(alpha=1, gamma=1).

| Requested route | Original-prompt supported, 15 per route | Revised-prompt closed-set candidate, 24 per route |
| --- | ---: | ---: |
| GPT-5.5 | 15/15 | 23/24 |
| GPT-5.6 Luna | 15/15 | 23/24 |
| GPT-5.6 Terra | 15/15 | 24/24 |
| GPT-5.6 Sol | 15/15 | 23/24 |
| GPT-6 Astra | 9/15 | 19/24 |
| GPT-6 Sol | 12/15 | 21/24 |
| GPT-6 Luna | 12/15 | 23/24 |
| GPT-6.1 Sol | 8/15 | 19/24 |
| Total | 101/120 | 175/192 |

**These are different batches and decision rules, not a paired improvement estimate.**
The kernel candidate lacks newly calibrated target-support and independent
confirmation. Applying the existing outer guard reduces it to 171/192, with Astra
at 16/24. The 175/192 result is not the accuracy of a complete open-set method.
Prompt, feature, and 51 classifier candidates were selected on inspected development
data. Another nine-preference numeric prompt was tested only in a small two-route
pilot. Neither prompt replaces the public default.

The frozen seven-class v11 matched 98/105 earlier-route responses in the current
original-prompt development batch; all 15 new 6.1 Sol responses instead received
the Astra label. The self-contained web compatibility pilot matched 12/16 routes,
with 6.1 Sol at 0/2. This is a known discrimination failure, not proof of substitution
or capability degradation. The update publishes research evidence, optional
eight-class fitting, and web disclosures while retaining the accepted seven-class
315-choice default. No final eight-route confirmation batch was started.

Reproduction is offline and does not launch new model calls:

```text
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python3 scripts/evaluate_gpt61_development.py
```

ModelTrace's excellent corpus and reproducible features remain the direct foundation.
The frozen upstream 16-model bank used here lacks a registered 6.1 Sol reference; this must not be counted as zero accuracy to
manufacture a win. Historical bounded one-/three-call comparisons remain below;
no comprehensive eight-route superiority claim is made.

## Historical 315-choice v11: third confirmation still failed the gate

[Release candidate v11](../config/release-candidate-v11.json) was frozen before
[confirmation-v10](../config/confirmation-v10.json) collected 15 fresh responses
per route. All 105 calls succeeded and strictly conformed to the 9×35 Schema.
Default `supported` matched requested route labels on 103/105 (98.10%): GPT-5.5,
5.6 Luna/Terra/Sol, 6 Astra, and 6 Luna were each 15/15; GPT-6 Sol was 13/15.
The prespecified ≥14/15-per-route gate therefore failed.

On the same responses, closed-set ModelTrace one-call matched 104/105 and disjoint
three-call decisions matched 35/35. This batch cannot establish comprehensive
superiority over the excellent upstream method. Both comparators reuse TraceOne's
responses and Schema, the three-call arm has only 35 independent decisions, and
requested-route labels are not independently attested served weights. See the
per-response [evaluation](../data/confirmation-v10-evaluation.json) and
[head-to-head](../data/confirmation-v10-head-to-head.json). The 791-row adapter
and raw-frequency development are documented in
[seven-model-development-v3.json](../data/seven-model-development-v3.json); that
development evidence cannot replace independent confirmation.

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
