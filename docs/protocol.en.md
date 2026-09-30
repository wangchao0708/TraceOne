# Evaluation protocol

[简体中文](protocol.md) | [English](protocol.en.md)

## 1. Objective and truth boundary

With recorded Codex runtime and fixed `reasoning_effort=low`, wrapper, and prompt,
one response is assigned to one of seven `requested_model` route labels or `unknown`. The event
stream contains no independent `response_model` or weight attestation. Results are
requested-label agreement, not ground-truth accuracy for served weights.

Identity attribution permits one model call and one response. The 9×35 grid contains
315 micro-decisions in that response; JSON Schema is an output constraint, not an
extra question. Capability degradation is a separate multi-item workflow.

## 2. Frozen release pipeline

The current seven-model 315-choice configuration is
[release-candidate-v11.json](../config/release-candidate-v11.json).
The failed v9 and v10 candidates remain in the historical record.
The historical five-model
configuration remains in [release-candidate-v8.json](../config/release-candidate-v8.json):

1. A strict parser requires an object containing only `numbers`, shape 9×35, with
   integer values from 1 through 355.
2. ModelTrace's 16-model marginal Hellinger and ordered-block bank is reused with
   absolute JS similarity. Fewer than 280 usable values abstains; a non-target fused
   winner can pass only when a target marginal winner meets the prespecified similarity,
   margin, and fused-gap ≤0.20 fallback conditions.
3. Passing samples enter a seven-class alpha=1 ridge adapter over 48 bank features
   (16 fused, 16 marginal, 16 absolute similarities) plus 355 raw-number frequencies
   weighted by 0.25. Margin below 0.01 abstains. Support still uses only the 48
   bank features.
4. Default `supported` applies a shrinkage-Mahalanobis target-support envelope with
   per-class 99% empirical distance thresholds and a 90th-percentile adapter-margin
   rescue. If adapter margin is below 0.01, bank rescue additionally requires a
   target outer winner with fused margin ≥0.25, similarity ≥0.60, and a passing support
   distance. This is empirical support, not a distribution-free OOD guarantee.

Current seven-model training contains 791 rows, 113 per class: 83 prior rows per
route plus 15 per route from each failed `confirmation-v8` and `confirmation-v9`.
Codex runtimes and dates
span collection epochs and are explicitly recorded. The 0.1.0 training and
confirmation-v7 remain historical evidence.

The initial 68/15 development split led to the frozen v9 candidate, which then failed
confirmation. Only after recording each failure were `confirmation-v8` and
`confirmation-v9` moved into later development. V11 used whole-batch holdouts,
then fit all 791 rows and preregistered a new confirmation in
[confirmation-v10.json](../config/confirmation-v10.json). It matched 103/105,
but GPT-6 Sol was 13/15, failing the prespecified gate.

## 3. Operating profiles

- `supported`: default outer guard + ridge + target support; lower unseen-class FAR.
- `enrolled`: outer guard + ridge; favors registered-route sensitivity.
- `bank`: upstream features and guard only; an ablation, not the release default.

Match rate, coverage, and abstentions must all be reported. Accuracy on identified
samples alone is not a primary metric.

## 4. Splits and tuning discipline

- Development selects prompts, features, guards, adapters, and support.
- Group CV holds out whole collection batches from normalization, fitting, and tuning.
- Confirmation freezes configuration, sample count, decision rule, and hashes first.
- Open world removes a complete label from gallery, feature space, and support fit.

The earlier v7 configuration scored 71/75 on confirmation-v6 and failed its preregistered
gate. Only then did that batch become v8 development data. Confirmation-v7 is v8's
final unseen confirmation and cannot be used to modify v8. Failed calls, invalid
format, errors, and `unknown` all remain in the primary denominator.
Seven-model v9 scored 101/105 on confirmation-v8, with Astra and GPT-6 Luna at
13/15 each, failing the ≥14/15-per-route gate. That batch is v10 development only;
it cannot be relabeled as a v9 success.
V10 matched 98/105 on confirmation-v9. V11 matched 103/105 on confirmation-v10,
but GPT-6 Sol was 13/15. All three failed batches retain their full denominators;
an inspected batch cannot be relabeled as independent success.

## 5. Comparator design

The 0.1.0 head-to-head runs on the same 75 responses. The seven-model confirmation
uses the same comparison definition, with five disjoint triplets per route:

- TraceOne makes one decision per response.
- ModelTrace-one applies closed-set mean-fused argmax to each response.
- ModelTrace-three partitions responses by model and order into disjoint triplets:
  25 in the five-model batch or 35 in a seven-model batch.

Sharing responses and the bank reduces data confounding, but the prompt and Schema
are TraceOne's, not ModelTrace's randomized challenge text. The three-call arm has
only 35 independent decisions in a seven-model batch and wider intervals.
Cross-paper point estimates are
context only.

## 6. Open-world definition

Rejecting an excluded route that is present in the full bank is only a registered-
distractor result. A true held-label fold rebuilds the bank, adapter feature space,
and support without that complete label. ModelTrace closed set has no `unknown` for
these valid inputs, so all 324 current samples are necessarily named. This means 100% false
identification under unknown truth, not a claim of 0% ordinary classification accuracy.

Open-world v5 contains nine excluded labels and 324 rows; `supported` falsely
accepts 22, including 13/36 GPT-5.4 and 8/36 Claude Opus 5.5. These data were
inspected while tuning and are development estimates.
A blind independent-provider, new-date, and unseen-wrapper test remains missing.

## 7. Degradation protocol

Numeric fingerprint drift cannot establish a capability loss. Canary baseline and
current runs must share the same benchmark version, scorer, reasoning, wrapper,
retry policy, and timeout, with item-level pairing:

- Primary test: exact one-sided McNemar. Baseline-correct/current-wrong is a
  regression; the reverse is an improvement.
- Report `degraded` only when observed loss reaches the preregistered minimum effect
  and p≤alpha.
- Invalid responses fail by default. Different item sets default to
  `invalid_comparison`, not a silent intersection.
- Overall is the primary test; family tests are secondary and Holm-corrected.
- Benchmark size is selected with exact power under stated regression and
  improvement probabilities.

Canary v2 has four families with 48 items each, 192 total. Items or independent
sessions are units; tokens from one long response are not independent samples.

## 8. Public data and privacy

`data/live/` is never committed. `scripts/export_public_data.py` removes local
`thread_id` and `stderr_tail` while retaining numeric text, route, runtime, reasoning,
usage, timestamps, and hashes. Manifests record source and public digests. Manually
review exports for fields introduced by future runtimes.

## 9. Known limitations

- Fingerprints drift with system prompts, wrappers, reasoning, and time.
- Upstream reference data lack complete reasoning provenance.
- The 0.1.0 fifteen rows per class establish only that batch; 75/75 still has a Wilson 95%
  interval of approximately 95.13%–100%.
- GPT-5.4 is the hardest unseen label: 13/36 false accepts in seven-model development.
- Without routing logs or attestation, detector error, natural variation, and real
  substitution cannot be distinguished.

## 10. Initial GPT-6.1 Sol expansion development (historical stage)

This section records the first 489-call stage. Version 0.3.0 registers the eighth
route; its subsequent method and confirmation are described in section 11.

The [official OpenAI model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
confirms the exact ID `gpt-6.1-sol` and support for `low` reasoning. An early
September 30, 2026 attempt returned “model not supported”; later that day, access
was verified with Codex CLI 0.159.2 and real responses were collected. Fitting now
accepts explicit eight-class labels and support derives its classes from the adapter.
Default collection, packaged artifacts, and web predictions remain seven-class:
successful access is not successful identification.

All 489 calls used the Codex subscription, Low reasoning, the isolated wrapper,
and one 315-choice question. No paid API or reset credit was used. The original
prompt supplied 113 new 6.1 Sol enrollment responses and 15 development responses
per eight routes. Two small alternative-prompt pilots and a revised-prompt batch
with 24 responses per eight routes were also collected. Earlier-route enrollment
uses older runtimes, whereas all current eight-route development responses use
0.159.2. Some new enrollment was collected after the current development batch;
these are inspected development data, not concurrent blind confirmation.

The initial 17-model-bank plan is revised explicitly: matching multi-environment
6.1 Sol reference data are not available, so the 16-model bank remains a frozen
feature extractor for explicit eight-class adapter/support fitting. No isolated
centroid was appended. A future 17-model bank still requires independent raw
reference data and a full normalization/environment/centroid refit, disjoint from
enrollment and confirmation. Different prompts must not be mixed into a supposed
single-prompt enrollment set.

Astra and 6.1 Sol are not yet reliably separated; see the
[results](results.en.md#gpt-61-sol-expansion-development-not-qualified-for-release).
No final eight-route confirmation or new prediction model is published. Collection
requires `--allow-prospective` to explicitly permit a verified prospective route in
a multi-model development batch; otherwise seven-class defaults and single-route
prospective collection protections remain in force.

Freeze all rules and assets before collecting at least 15 untouched responses per
route. Retain the prespecified ≥14/15 match gate for every route, counting failures,
abstentions, and invalid formats in the denominator. Same-response ModelTrace
one- and disjoint three-call arms remain bounded comparators. The self-contained
web prompt's 16-call pilot is a compatibility check, not an accuracy estimate.
The eighth prediction option stays hidden until a new freeze, independent
confirmation, and Python/JavaScript parity are complete.

Verify historical freezes at their original Git commits rather than changing old
digests to match new code:

```text
python3 scripts/verify_frozen.py config/release-candidate-v11.json --revision 8d70a3b
```

Raw-frequency weighting now starts at three times the bank model count rather
than a hard-coded 48. Default 16-model calculations are unchanged; a one-label-
removed bank correctly uses 45. Historical OOD development results belong to their
original implementation, not this correction or the prospective eight-class method.

Before revalidation, check that every target is callable under the same account,
client and reasoning conditions. Do not splice historical rows into a different-date
or different-environment batch and call it concurrent confirmation. If availability
changes, preregister the callable target set and preserve historical results.

## 11. Version 0.3.0 eight-route experiment and publication boundary

Eight targets include `gpt-6.1-sol`, no longer requiring prospective opt-in for
collection. CLI default `optimized` uses the self-contained `identity-replacement-v1`
question. `supported` and `traceone prompt --legacy` retain seven-route history.
Do not mix questions and classifier versions.

All 576 development calls use CLI 0.159.2, Low reasoning and the same question;
571 enter fitting. Each requests 315 integers. Enrollment uses Schema; independent
128-call calibration and 120-call confirmation do not, matching web conditions.
IDs are disjoint across roles and failures remain in evaluation denominators.

Selection over 96 development configurations prioritizes the lowest per-route match
count, then total matches, preferring ordinary ridge on ties. The result uses alpha=1,
48 bank features, 355 raw frequencies and 188 repetition/order statistics. After
standardization, each group is scaled by weight/sqrt(dim), with weights 1/1/0.5.
The original 16-model bank has no fabricated 6.1 Sol centroid. The 73-dimensional
support envelope uses independent per-class maximum calibration distance, covariance
shrinkage 0.3 and no high-margin bypass. It is empirical, not an identity probability
or distribution-free guarantee under drift.

Input must be readable as nine arrays or a sole-key numbers object. Out-of-range
and non-integer entries may be discarded; each row needs 25–45 usable integers,
total 280–350. Never pad, fabricate or clamp integers. Strict 9x35/1–355 format
compliance is reported separately. Unparseable, inadmissible, tool-using, timed-out
and rejected calls count as misses. Distance comparison has 1e-10 relative and
margin comparison 1e-12 absolute floating-point tolerance for cross-language parity.

Code, data and parameters were frozen at 5b70968 before collecting 15 fresh calls
per route. The rule remains ≥14/15 for EVERY route. Actual agreement is 101/120;
Astra, 6 Luna and 6.1 Sol fail the gate. No retuning or replacing confirmation calls
followed. This publishes the selected experimental source, not an overall-improvement
claim or public-site replacement. Full failures are in the [ledger](results.en.md).
Astra/6.1 Sol cross-confusion always yields an inconclusive web consistency verdict.
Other mismatches likewise cannot prove degradation; capability loss requires separate
paired canary measurement.
