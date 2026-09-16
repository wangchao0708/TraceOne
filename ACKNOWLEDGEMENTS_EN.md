# Acknowledgements

[简体中文](ACKNOWLEDGEMENTS.md) | [English](ACKNOWLEDGEMENTS_EN.md)

TraceOne's most important direct foundation is xqy2006's
[ModelTrace](https://github.com/xqy2006/ModelTrace). ModelTrace develops random-number
choice biases into a complete and reproducible black-box fingerprinting method and
openly provides feature implementations, a reference bank, collection tooling,
validation results, and clearly stated boundaries. It is an original, exceptionally
well-executed, and generous open-source contribution. TraceOne expresses its sincere
respect and gratitude.

TraceOne reuses and adapts ModelTrace's marginal Hellinger and ordered-block features,
unified reference bank, and reference corpus. The pinned upstream commit, license, and
modification boundary are recorded in [third_party/NOTICE.md](third_party/NOTICE.md).
Head-to-head comparisons in this repository describe the behavior of added protocols;
they should never be read as diminishing ModelTrace's originality or contribution.

ModelTrace also explicitly credits the earlier
[hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker), while the related
[Linux Do community discussion](https://linux.do/t/topic/2472419/1) helped spread the
random-number distribution approach. TraceOne is grateful to these earlier explorers
as well. The ModelTrace author's
[project retrospective](https://linux.do/t/topic/2827119?tl=en) and its candid account
of experimental boundaries directly helped us design stricter single-call, OOD, and
blind-confirmation protocols.

TraceOne was also informed by LLMmap, LLMPrint, Targeted Counterfactual Fingerprinting,
*Conformal Inference for Open-Set and Imbalanced Classification*, *Do System Prompts
Leave Behavioral Fingerprints?*, the ICLR 2026 paper *When LLMs get significantly
worse*, and Amazon Science's LLM Accuracy Stats. Their specific influence and primary
links are documented in [docs/research.en.md](docs/research.en.md).

If you use TraceOne, please also cite or link ModelTrace and cite the relevant prior
works for the methods you use. `CITATION.cff` preserves this request.
