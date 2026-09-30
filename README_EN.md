# TraceOne

[简体中文](README.md) | [English](README_EN.md)

<p align="center">
  <a href="https://traceone-model-check.nutmeg-basil-6747.chatgpt.site/">
    <img src="docs/assets/quick-online.svg" alt="快速在线使用" width="280" />
  </a>
</p>

TraceOne offers experimental fingerprint identification for eight Codex model routes
with one 315-choice call. Route-fingerprint drift and capability degradation remain
separate, reproducible questions:

- `gpt-5.5`
- `gpt-5.6-luna`
- `gpt-5.6-terra`
- `gpt-5.6-sol`
- `gpt-6-astra`
- `gpt-6-sol`
- `gpt-6-luna`
- `gpt-6.1-sol`

Version `0.3.0` publishes the preselected, frozen eight-class experimental configuration, including GPT-6.1 Sol, still
using one question requesting 315 integers. The revised question explicitly permits
repetition. The classifier combines ModelTrace-derived bank features, raw frequencies,
and repetition/order statistics with concurrent eight-route enrollment and separate
support calibration collected through Codex CLI 0.159.2. Inspected three-fold
development matched 543/576 (Astra 59/72, 6.1 Sol 58/72), **not an independent accuracy
estimate**. Fresh web-condition confirmation matched only 101/120 (84.2%): Astra
9/15, 6.1 Sol 10/15, and 6 Luna 10/15. The requirement that EVERY route reach ≥14/15 was not met.
Strict-format compliance and failure denominators are documented in the
[evidence ledger](docs/results.en.md).
**Astra and 6.1 Sol can still be confused. We claim neither comprehensive superiority
over ModelTrace nor authenticated model identity.** Historical failures and the
seven-class `supported` method remain reproducible; `traceone prompt --legacy` prints
the old question. Enrollment and evaluation cover Codex subscription Low reasoning;
other providers, API wrappers, and reasoning settings are not qualified by these data.
**This update changes the repository only, not the public site. The online link
still serves the seven-route baseline.** Run the local CLI or local web source for
eight-route identification. Source publication is not qualification against the
research gate. The configuration is selected by the documented development rule,
not an independent confirmation comparison of every configuration.

## Use it online

[Open TraceOne Web](https://traceone-model-check.nutmeg-basil-6747.chatgpt.site)

The web question embeds the output shape in the same prompt, so users need no
installation or separate JSON Schema: copy the question, ask the model, and paste the
complete answer. The 16-model bank features, eight-class ridge adapter, and target-support rejection
all run locally in the browser; responses are not uploaded.

The page switches between “Identify model” and “Degradation signal.” In the latter,
users choose the model they are actually using; the page automatically compares that
selection with the fingerprint prediction and returns “Fingerprint consistent,”
“Fingerprint anomaly,” or “Unable to determine.” This is only a route-fingerprint
consistency screen. Capability loss still requires the separate canary evaluation and
cannot be concluded from one fingerprint mismatch alone.

The new eight-route confirmation is checked field by field against browser JavaScript.
All 105 historical seven-route results are also retained and reproduced. Both the
current web question and confirmation are self-contained, without an external Schema;
the historical 103/105 Schema result must not be relabeled as current web accuracy.
See [docs/site.en.md](docs/site.en.md).

## Extensions built on ModelTrace

TraceOne begins with sincere thanks to **xqy2006**, the author of
[ModelTrace](https://github.com/xqy2006/ModelTrace). ModelTrace turned the community
insight that random-number choices can carry behavioral fingerprints into a complete,
reproducible open-source project with features, a reference bank, collection tooling,
and careful experiments. It is an excellent, insightful, and generous contribution,
and the most important direct foundation of TraceOne. The comparison below should be
read as an extension and stress test of that strong foundation, never as a dismissal
of the original work.

- Identity attribution uses one call and one response instead of the author's
  recommended three probes.
- It is not a bare closed-set argmax. The 16-model bank features, eight-class ridge
  adapter, and target-support envelope can return `unknown`.
- Frozen configurations, preregistered confirmations, complete failure
  denominators, whole-collection holdouts, and publishable data are included.
- Fingerprint drift is not called degradation. Capability regression uses a
  separate canary, paired McNemar tests, power planning, and Holm correction.

TraceOne reuses and adapts ModelTrace's marginal Hellinger and ordered-block features
and reference corpus. See [third_party/NOTICE.md](third_party/NOTICE.md) for the
license and modification boundary. ModelTrace also credits the earlier
[hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker); TraceOne respects
and acknowledges that community lineage as well. See
[ACKNOWLEDGEMENTS_EN.md](ACKNOWLEDGEMENTS_EN.md) for full acknowledgements and
[docs/research.en.md](docs/research.en.md) for research references.

## The single question

The current web question, CLI prompt, and new confirmation use this identical
self-contained question, with no additional JSON Schema. Independence and repetition
are instructions, not a guarantee of independent uniform randomness.

```text
Using only the current language model, make 315 independent first-instinct selections of an integer from 1 through 355 inclusive. Sample mentally with replacement: after each choice, forget the earlier choices. Repeated integers are allowed and expected; do not try to cover the range, balance frequencies, avoid duplicates, or alternate high and low values. Output only one JSON object with the sole key "numbers", containing 9 arrays of exactly 35 integers each. Do not use tools, code execution, calculators, search, APIs, or external random generators. Do not count, use an arithmetic progression, or reuse a designed sequence. No explanation.
```

Historical seven-route Schema prompt; do not mix it with the new eight-route assets:

```text
Using only the current language model, produce 315 separate first-instinct
choices of an integer from 1 through 355 inclusive in the exact JSON structure
required by the supplied output schema. Do not use tools, Python, code execution,
calculators, search, APIs, or external random generators. Do not count upward or
downward and do not use an arithmetic progression, repeating cycle, repeated block,
or another designed pattern. Accidental repetitions are valid. Output only the
schema-conforming JSON value with no explanation.
```

One response contains a 9×35 integer grid. This is one call with many micro-
decisions, not three independent questions. The exact assets are
[prompts/identity-v3-schema.txt](prompts/identity-v3-schema.txt) and
[schemas/identity-v3.json](schemas/identity-v3.json).

## All three seven-model confirmations failed their prespecified gate

GPT-6 Sol and Luna are present in the 16-model reference bank and seven-class
adapter. All 105 fresh `confirmation-v8` calls conformed to the strict Schema.
TraceOne one-call matched 101/105, but GPT-6 Astra and Luna were each 13/15,
below the preregistered 14/15 per-route threshold. The same-response ModelTrace
one-call result was also 101/105; its three-call arm was 35/35. This failed
batch remains visible and cannot support a comprehensive superiority claim.
See [docs/results.en.md](docs/results.en.md).

The subsequently frozen `release-candidate-v10` matched 98/105 on independent
`confirmation-v9`: GPT-5.6 Sol was 13/15 and GPT-6 Sol 12/15, again below the
same gate. ModelTrace one-call on those responses was 96/105, while disjoint
three-call decisions were 35/35.

The historical 315-choice v11 adds raw number-frequency features. On its fresh
`confirmation-v10` it matched 103/105 (98.1%), but GPT-6 Sol was 13/15, below the
prespecified ≥14/15 per-route gate. On the same responses, ModelTrace one-call
matched 104/105 and disjoint three-call decisions matched 35/35. Seven-route
support is usable experimentally, not a verified comprehensive advantage over
upstream. See [docs/results.en.md](docs/results.en.md) for the complete failures.

## Historical 0.1.0 five-model confirmation

Release candidate v8 was frozen before `confirmation-v7`. All 75 fresh calls
succeeded and conformed to the strict schema:

- TraceOne `supported`: 75/75; 15/15 for every model.
- ModelTrace one-call on the same responses: 74/75; Sol was 14/15.
- ModelTrace three-call on disjoint triplets: 25/25; 5/5 per model.

TraceOne therefore reduces the model calls needed for each decision from three to
one. Under the fixed 75-call budget used here, TraceOne produced 75 independent
one-call decisions while the three-call arm produced 25 triplet decisions; both had
a 100% point estimate. TraceOne gained one item over the same-response one-call
comparator, but that is not a statistically significant advantage or a formal
non-inferiority result. Precisely, each per-model point estimate was no lower in this
batch, Sol gained one item, and one-call and three-call accuracy point estimates
matched. Wilson intervals and every
decision are in [data/confirmation-v7-evaluation.json](data/confirmation-v7-evaluation.json)
and [data/confirmation-v7-head-to-head.json](data/confirmation-v7-head-to-head.json).

Labels are Codex `requested_model` values, not independent attestation of served
weights.

## Historical 0.1.0 open-world result and boundary

The held-label evaluation removes one complete excluded label from the bank,
adapter feature space, and support fit before treating it as unseen:

- `supported`: 24/288 false accepts, 8.33% (95% Wilson 5.66%–12.10%).
- `enrolled`: 59/288 false accepts, 20.49%.
- ModelTrace closed set: 288/288 are necessarily assigned a known label.

This is tuned development evidence using upstream samples, not a blind test from
an independent provider. The largest weakness is held-out GPT-5.4: `supported`
still accepts 20/36. Rejection of labels already present in a full bank is only a
registered-distractor check, not true OOD evidence. See
[data/open-world-development-v2.json](data/open-world-development-v2.json).

## Install and identify

Requires Python 3.11 or newer.

```text
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Print the packaged frozen prompt:

```text
traceone prompt
```

Collect one Codex response:

```text
python3 scripts/collect_codex.py \
  --output data/live/one.jsonl \
  --prompt prompts/identity-v3-schema.txt \
  --schema schemas/identity-v3.json \
  --split holdout --repeat 1 --model gpt-5.6-terra --run-id my-run
```

Identify a saved JSON response offline:

```text
traceone identify answer.json --format grid --method optimized
```

`optimized` is the repository's default eight-class experimental method. Use the revised question and its
independently calibrated target-support gate. `supported` and `enrolled` retain the
historical seven-class methods and old outer guard. `unknown` is a valid result and
must not be forced into a model label.

Reproduce the final evaluation and verify frozen assets:

```text
python3 scripts/verify_frozen.py config/release-candidate-v12.json
PYTHONPATH=src python3 scripts/evaluate_eight_optimized.py --verify-only
PYTHONPATH=src python3 scripts/evaluate_eight_optimized.py \
  --responses data/public/confirmation-v12.jsonl --output /tmp/traceone-v12-eval.json
node scripts/test_eight_classifier.mjs
PYTHONPATH=src python3 scripts/evaluate_live.py \
  data/public/confirmation-v7.jsonl --output /tmp/traceone-eval.json
PYTHONPATH=src python3 scripts/evaluate_head_to_head.py \
  data/public/confirmation-v7.jsonl --output /tmp/traceone-h2h.json
python3 scripts/verify_frozen.py config/release-candidate-v8.json --revision 7b52cb1
python3 scripts/verify_release.py config/release-v0.1.0.json
python3 scripts/verify_frozen.py config/release-candidate-v11.json --revision 8d70a3b
PYTHONPATH=src python3 scripts/evaluate_live.py \
  data/public/confirmation-v10.jsonl --output /tmp/traceone-v11-eval.json
```

## Degradation detection

The identity probe detects route behavior; it cannot prove capability degradation.
The v2 canary contains 192 versioned exact-answer items. Baseline and current runs
are paired by item; invalid outputs fail by default, item sets must match, and
family tests can use Holm correction:

```text
traceone degradation baseline-outcomes.json current-outcomes.json \
  --minimum-effect 0.05 --by-family --invalid-policy fail
```

Plan exact power first:

```text
traceone plan-degradation \
  --regression-probability 0.10 --improvement-probability 0.02 \
  --minimum-effect 0.05 --target-power 0.80
```

Under that preregistered scenario, 48 items provide only 29.1% detection power;
192 provide 89.8%, which is why v2 uses 192. These values depend on assumptions
and are not an observed degradation rate. `scripts/collect_canary.py` and
`traceone score-canary` implement collection and scoring. Each canary item is a
separate call to preserve item-level pairing; this is outside the one-call identity
budget.

## Evidence and limitations

- Release manifest: [config/release-v0.1.0.json](config/release-v0.1.0.json)
- Protocol: [docs/protocol.en.md](docs/protocol.en.md)
- Results and failure history: [docs/results.en.md](docs/results.en.md)
- Research and negative results: [docs/research.en.md](docs/research.en.md)
- Sanitized public data: [data/public](data/public)
- Public-data, privacy, and integrity checks: [docs/protocol.en.md](docs/protocol.en.md)
- Upstream work and full acknowledgements: [ACKNOWLEDGEMENTS_EN.md](ACKNOWLEDGEMENTS_EN.md)
- Contributors and AI-assistance boundary: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Web implementation and validation: [docs/site.en.md](docs/site.en.md)

Fingerprints can drift with the system prompt, runtime, reasoning effort, wrapper,
and service updates. Without routing logs or trusted attestation, a mismatch may be
a detector error, natural variation, or real route substitution. TraceOne reports
observable evidence; it does not claim to observe server weights.

MIT License.
