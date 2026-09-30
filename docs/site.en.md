# TraceOne Web

[简体中文](site.md) | [English](site.en.md)

Public URL: <https://traceone-model-check.nutmeg-basil-6747.chatgpt.site>

## Current public version

Following the subsequent request on September 30, 2026, the eight-route experiment,
including GPT-6.1 Sol, is published at the same public URL. Site version 7 uses source
commit `f9ab16d`, the repository's 315-choice question and frozen classifier.
Deployment does not change the failed research gate. Run the same source locally:

```text
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:8000 on the same machine. Loopback only, not public hosting;
press Ctrl+C to stop.

## Eight-route web workflow

One workspace switches between identification and degradation signals. Identification
copies one self-contained 315-choice question and predicts an enrolled route or unknown
from the pasted answer. Consistency screening selects the model used and compares the
label automatically with its fingerprint prediction: consistent, anomalous or inconclusive.

Astra/6.1 Sol cross-confusion always yields unable to determine. A fingerprint mismatch
cannot prove capability loss; rigorous degradation requires separate paired canaries.

[OpenAI's system-card addendum](https://deploymentsafety.openai.com/gpt-6-1-sol)
describes shared data/training types and safeguards for the two models. The page treats
this as possible context for similar fingerprints, not an established cause of overlap
or evidence of identical training examples or weights.

Both languages retain the full visible prompt, non-wrapping input, centered single-line
result and compact upstream credit. Imperfect format is disclosed. Out-of-range entries
are discarded, never padded or fabricated. Tolerance requires nine rows, 25–45 usable
integers per row and total 280–350; a complete response should be 9x35 integers in 1–355.
Unreadable/inadmissible responses return unknown.

## Source decision path and evidence

1. The unchanged ModelTrace-derived 16-model bank supplies distribution/order features.
2. Eight-class ridge uses 48 bank, 355 raw-frequency and 188 repetition/order features.
3. Independent 73-dimensional target support plus margin retain rejection, without a
   high-margin bypass.
4. The old bank decision is diagnostic, not a closed-set veto on newly enrolled 6.1 Sol.

Enrollment, calibration and confirmation use Codex subscription CLI 0.159.2, Low reasoning.
Calibration and confirmation omit Schema and match the visible question exactly. Other
providers, API wrappers and reasoning settings are not qualified by these data.
Fresh agreement is 101/120 (84.2%), strict-format compliance 61/120, failing the requirement
that EVERY route reach ≥14/15. See the [ledger](results.en.md). This is neither comprehensive
superiority nor authenticated identity. Historical seven-route Schema 103/105 cannot be
relabeled as current web accuracy.

test_eight_classifier.mjs checks all 120 new decisions and numeric outputs, maximum
error about 3.4e-13 at tolerance 1e-9. Historical 105 decisions remain reproducible using
historical artifacts. test_site_assets.mjs checks byte-identical source/deploy assets
and matching web/CLI/collection prompts. Cloud deployment success is checked separately;
the publication record is in the [release manifest](../config/release-v0.3.0.json).

## Privacy, interpretation and credit

The application needs no API key and processes answers in the current browser tab;
application code does not upload them. Candidate bars visualize relative scores, not
served-weight identity probabilities. Similarity and empirical support are not trusted
attestation. System prompts, reasoning, runtimes and provider updates can drift fingerprints.

The page credits [ModelTrace](https://github.com/xqy2006/ModelTrace). The repository
specifically appreciates xqy2006's excellent open-source contribution, explaining
lineage and MIT reuse boundaries in [research notes](research.en.md) and
[third-party NOTICE](../third_party/NOTICE.md).
