# Evaluation protocol

[简体中文](protocol.md) | [English](protocol.en.md)

## 1. Objective and truth boundary

Under fixed `reasoning_effort=low`, Codex runtime, wrapper, and prompt, one response
must be assigned to one of five `requested_model` route labels or `unknown`. The event
stream contains no independent `response_model` or weight attestation. Results are
requested-label agreement, not ground-truth accuracy for served weights.

Identity attribution permits one model call and one response. The 9×35 grid contains
315 micro-decisions in that response; JSON Schema is an output constraint, not an
extra question. Capability degradation is a separate multi-item workflow.

## 2. Frozen release pipeline

The final release uses [release-candidate-v8.json](../config/release-candidate-v8.json):

1. A strict parser requires an object containing only `numbers`, shape 9×35, with
   integer values from 1 through 355.
2. ModelTrace's 13-model marginal Hellinger and ordered-block bank is reused with
   absolute JS similarity. Fewer than 280 usable values, a non-target top candidate,
   or similarity below 0.52 returns `unknown`.
3. Passing samples enter a five-class alpha=1 ridge adapter over 39 features: 13
   fused, 13 marginal, and 13 absolute similarities. Margin below 0.01 abstains.
4. Default `supported` applies a shrinkage-Mahalanobis target-support envelope with
   per-class 99% empirical distance thresholds and a 90th-percentile adapter-margin
   rescue. This is empirical support, not a distribution-free OOD guarantee.

Training contains 415 rows, 83 per class, from the public 340-row enrollment and the
failed confirmation-v6. Prompt, Schema, bank, implementation, and artifact hashes
were frozen before confirmation-v7 and rechecked afterward.

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

The v7 configuration scored 71/75 on confirmation-v6 and failed its preregistered
gate. Only then did that batch become v8 development data. Confirmation-v7 is v8's
final unseen confirmation and cannot be used to modify v8. Failed calls, invalid
format, errors, and `unknown` all remain in the primary denominator.

## 5. Comparator design

The final head-to-head runs on the same 75 responses:

- TraceOne makes one decision per response.
- ModelTrace-one applies closed-set mean-fused argmax to each response.
- ModelTrace-three partitions responses by model and order into 25 disjoint triplets.

Sharing responses and the bank reduces data confounding, but the prompt and Schema
are TraceOne's, not ModelTrace's randomized challenge text. The three-call arm has
only 25 independent decisions and wider intervals. Cross-paper point estimates are
context only.

## 6. Open-world definition

Rejecting an excluded route that is present in the full bank is only a registered-
distractor result. A true held-label fold rebuilds the bank, adapter feature space,
and support without that complete label. ModelTrace closed set has no `unknown` for
these valid inputs, so all 288 are necessarily named. This means 100% false
identification under unknown truth, not a claim of 0% ordinary classification accuracy.

The open-world v2 data were inspected while tuning; results are development estimates.
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
- Fifteen rows per class establish only this batch; 75/75 still has a Wilson 95%
  interval of approximately 95.13%–100%.
- GPT-5.4 is the hardest unseen label: 20/36 false accepts in development.
- Without routing logs or attestation, detector error, natural variation, and real
  substitution cannot be distinguished.
