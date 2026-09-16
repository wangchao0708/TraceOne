# Changelog

## Unreleased

- Added a single-surface mode switch for model identification and route-fingerprint
  consistency screening, with an explicit selected-versus-predicted comparison.
- Clarified that the web comparison provides a degradation signal, not evidence of
  capability loss; rigorous capability claims remain in the paired canary workflow.
- Curated the release surface by removing superseded configurations and exploratory
  raw artifacts while retaining final evidence, frozen assets, and negative-result
  summaries.
- Refined the web layout from browser feedback: the full prompt now wraps without
  horizontal dragging, result titles stay centered on one line, method typography is
  larger, and the visible ModelTrace acknowledgement is reduced to one linked line.
- Added a public, bilingual, local-first web workflow for copying the self-contained
  probe, pasting one response, and visualizing the supported or unknown decision.
- Ported the release classifier to dependency-free browser JavaScript and verified
  exact decision/numeric parity on 75 frozen calls plus a five-route web-prompt pilot.
- Added a five-call compatibility pilot, static-site integrity checks, and a dedicated
  GitHub Actions web-classifier job.

## 0.1.0 — 2026-09-15

- Added one-response attribution for GPT-5.5, GPT-5.6 Luna/Terra/Sol, and GPT-6 Astra.
- Added a 13-model outer guard, ridge enrollment adapter, empirical target support,
  and explicit `unknown` decisions.
- Added a frozen 75/75 confirmation and same-response ModelTrace comparison.
- Added held-label open-world evaluation with limitations and public sanitized data.
- Added paired degradation testing, exact McNemar power planning, 192-item canary v2,
  invalid/missing-data gates, and Holm-corrected family tests.
- Added Chinese/English documentation, CI, release hashes, and third-party notices.

Known limitation: held-out GPT-5.4 remains difficult (20/36 false accepts in tuned
development data); no independent-provider OOD blind set or served-weight attestation
is available.
