# Research rationale and method selection

[简体中文](research.md) | [English](research.en.md)

## Upstream foundation and special thanks

[ModelTrace](https://github.com/xqy2006/ModelTrace) is TraceOne's most important direct
foundation. It turns preferences over integers 1–355 into a working black-box
fingerprinting system, combines marginal Hellinger and ordered-block features, and
openly provides the reference bank, collection code, and validation process. We
especially admire that the author contributed not only a creative method but also a
candid account of one- versus three-query and same- versus cross-provider boundaries,
leaving later work an unusually strong and auditable starting point. The author's
[Linux Do retrospective](https://linux.do/t/topic/2827119?tl=en) reports these results
and states that the best result still uses three probes. The earlier
[hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker) implementation and
[random-number distribution discussion](https://linux.do/t/topic/2472419/1) also
deserve explicit credit.

TraceOne builds on this excellent lineage: it preserves and clearly attributes the
reproducible features, bank, and corpus, then adds a single-call protocol, current
Codex enrollment, open-set rejection, frozen confirmation, and a separate degradation
test. Comparative numbers describe differences under this repository's protocol and
do not diminish the originality or value of the upstream work. See
[ACKNOWLEDGEMENTS_EN.md](../ACKNOWLEDGEMENTS_EN.md) and
[third_party/NOTICE.md](../third_party/NOTICE.md) for the full acknowledgement and
reuse boundary.

## How recent work shaped the design

- [LLMmap, USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/pasquini)
  shows that black-box behavior can identify model versions while highlighting open
  world, adaptation, and repeated interaction as hard cases. Behavioral fingerprints
  are useful; closed-set confidence is not unknown detection.
- [LLMPrint, ACL 2026](https://aclanthology.org/2026.acl-long.541/) improves query
  efficiency with optimized prompts and statistical verification. This motivated
  constrained micro-decisions packed into one response, but proprietary Codex routes
  do not provide the full source-optimization access used in the paper.
- [Targeted Counterfactual Fingerprinting](https://arxiv.org/abs/2608.08195) motivates
  constrained answer spaces and targeted probes. Our 128-bit pairwise probe follows
  that direction; it did not beat the main method and remains a negative result.
- [Conformal Inference for Open-Set and Imbalanced Classification](https://arxiv.org/abs/2510.13037)
  makes calibration assumptions explicit in open-set and imbalanced classification.
  It is not an LLM-attribution paper; TraceOne borrows only its open-set framing.
  TraceOne reports empirical ranks and distance thresholds, but the data do not justify
  distribution-free coverage, so the code avoids claiming a conformal guarantee.
- [Do System Prompts Leave Behavioral Fingerprints? A Large-Scale Empirical Study of Clone Detection via Output Similarity](https://arxiv.org/abs/2608.24461)
  shows that system prompts and prefixes can move detectors. TraceOne therefore treats
  prompt, Schema, runtime, wrapper, reasoning, and time as label provenance.

## Why one query can contain 315 choices

The budget counts model calls or turns, not decisions encoded in output tokens. One
long response provides a lower-variance distribution estimate without three network
round trips. A 9×35 Schema prevents the out-of-range values, prose, and truncation
observed in the schema-free version.

This is query packing, not a claim that 315 values are independent statistical
samples. The final accuracy unit is still one of 75 model calls, and the Wilson
interval uses 75 as its denominator.

## Why rejection is layered

A closed-set softmax or argmax can confidently label any valid input. TraceOne splits:

1. a 13-model bank checks absolute similarity and whether the top label is a target;
2. a ridge adapter separates five nearby routes under the current Codex wrapper;
3. a target-support envelope checks whether the prediction lies in enrollment support.

This separates “which is closest?” from “is it like any registered target?” It reduces
held-label false identification from ModelTrace's 288/288 to 24/288, but GPT-5.4 still
overlaps heavily, showing an information limit in one numeric response.

## Negative results: active probes and nonlinear adapters

- Pairwise v1 asked 128 random left/right choices and reached 24/25 in a small
  development leave-one-out whose hyperparameters were selected on the same rows.
- Pairwise v2 selected pairs from 340-row enrollment log-odds and fell to 22/25.
- On the same 39 features, KNN, shrinkage LDA, and RBF prototypes all trailed the
  alpha=1 ridge adapter's 412/415 whole-collection CV.

Novel or active did not automatically mean reliable, so none entered the release path.

## Basis for degradation detection

The ICLR 2026 paper [When LLMs get significantly worse: A statistical approach to detect model degradations](https://proceedings.iclr.cc/paper_files/paper/2026/hash/70de9e3948645a1be2de657f14d85c6d-Abstract-Conference.html)
emphasizes paired item-level outcomes and false-positive control.
[LLM Accuracy Stats](https://github.com/amazon-science/LLM-Accuracy-Stats) likewise
recommends appropriate within-example rerun aggregation before paired or permutation
inference. This supports separating a capability canary from an identity fingerprint.

TraceOne uses exact one-sided McNemar because outcomes are paired binary items and the
question is whether regressions exceed improvements. A minimum effect prevents a tiny
but significant result from being overinterpreted. Holm correction prevents selecting
the smallest p-value across families. Exact power planning prevents a low-power 48-item
design from turning “not significant” into “no degradation.”

## Highest-value next experiments

- Collect an unknown blind set from a provider never used for bank or threshold work.
- Preregister a drift matrix across dates, system prompts, reasoning levels, and Codex
  runtimes.
- Add trusted routing attestation, if available, to replace requested-label agreement
  with real substitution evaluation.
- Define an actionable degradation effect, power, and retry policy before running
  baseline/current canaries; do not change items or thresholds after seeing outcomes.
