# TraceOne Web

[简体中文](site.md) | [English](site.en.md)

Live site: <https://traceone-model-check.nutmeg-basil-6747.chatgpt.site>

## User flow

The same workspace provides two switchable modes:

- **Identify model:** copy the question, paste the answer, and predict one of the five
  target routes or `unknown`.
- **Degradation signal:** first choose the model actually in use, then complete the same
  one-question flow. The page automatically compares the selected model with the
  fingerprint prediction and returns “Fingerprint consistent,” “Fingerprint anomaly,”
  or “Unable to determine.”

Both modes use one self-contained question and show absolute similarity, support
distance, and five-candidate relative weights. The user does not compare model names
manually.

The page asks for no API key and sends no model response to a server. Its HTML, CSS,
JavaScript, and three frozen model artifacts are served statically; identification runs
only in the current browser tab. A Content Security Policy limits scripts, styles, and
data connections to the same origin.

## Parity with the Python release path

`dist/traceone.js` ports the release path step by step:

1. the ModelTrace-derived 13-model marginal Hellinger and ordered-block outer guard;
2. the five-class ridge adapter;
3. shrinkage-Mahalanobis target-support rejection and high-margin rescue; and
4. an explicit `unknown` outcome.

`scripts/test_web_classifier.mjs` compares the browser implementation field by field
with saved Python results: label, format, usable count, outer candidates, similarity,
score margin, adapter margin, support distance, threshold, and empirical p-value. All
80 rows—75 frozen confirmation calls plus five web-prompt pilot calls—match within a
numeric tolerance of `1e-9`.

`scripts/test_site_assets.mjs` also verifies that the site's bank, adapter, and support
files are byte-identical to the Python package assets and that the visible question is
synchronized with `prompts/identity-web-v1.txt`.

## Self-contained prompt pilot

The frozen release prompt uses a Codex JSON Schema to enforce the 9×35 output. A normal
web user cannot conveniently attach that Schema, so `identity-web-v1` states the 9×35
shape inside the same question while still using only one model call.

The 2026-09-15 compatibility pilot collected one Low-reasoning call from each target
route:

- `supported` requested-route agreement was 5/5;
- strict format compliance was 1/5;
- the other four responses each had one or two out-of-range integers, retained 313–314
  usable values, and passed by the distance path; and
- browser and Python decisions matched exactly.

Public responses and evaluation are in
[data/public/web-prompt-v1-pilot.jsonl](../data/public/web-prompt-v1-pilot.jsonl) and
[data/web-prompt-v1-pilot-evaluation.json](../data/web-prompt-v1-pilot-evaluation.json).
With only five calls, 5/5 is not an accuracy claim; it is evidence that the copy–ask–
paste journey functions end to end.

## Interpretation boundary

Candidate bars are a relative softmax of the five adapter scores for visualization,
not probabilities of server identity. Absolute similarity and support distance are not
trusted attestation either. System prompts, reasoning effort, runtime, date, and service
updates can all move a behavioral fingerprint.

The web “Degradation signal” is a **route-fingerprint consistency screen**. A supported
match produces “Fingerprint consistent,” a supported mismatch produces “Fingerprint
anomaly,” and rejection produces “Unable to determine.” A mismatch can also result
from classification error, route substitution, system-prompt changes, reasoning effort,
or temporal drift, so it cannot by itself prove a capability loss. Strict capability-
degradation claims in the repository still require the separate canary, paired McNemar
test, power plan, and multiple-testing correction.

The site explicitly thanks [ModelTrace](https://github.com/xqy2006/ModelTrace), the
most important direct method and implementation foundation of this project. The web
experience makes that excellent lineage easier to use through a one-question workflow,
rejection, and clear visualization.
