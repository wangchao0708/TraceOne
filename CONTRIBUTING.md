# Contributing

[English](#english) | [简体中文](#简体中文)

## English

Bug reports and reproducible evaluations are welcome. Do not report a new model,
prompt, threshold, or feature as a release result unless it was frozen before the
confirmation data were collected. Keep failed calls and abstentions in the primary
denominator, include provider/runtime/reasoning provenance, and never commit secrets
or local task IDs.

Before opening a pull request, run:

```text
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/verify_frozen.py config/release-candidate-v8.json
```

For algorithm changes, include a whole-collection holdout or a fresh preregistered
confirmation run. Cross-dataset point estimates are context, not head-to-head proof.
Contributor roles and AI-assistance disclosure are recorded in
[CONTRIBUTORS.md](CONTRIBUTORS.md).

## 简体中文

欢迎提交 bug 和可复现实验。新模型、prompt、阈值或 feature 必须先冻结、后采集
confirmation，才能称为发布结果。主指标的分母必须保留失败调用和 abstention；
数据必须记录 provider、runtime、reasoning provenance，且不得提交凭证或本地 task ID。

提交 PR 前请运行上面的三条命令。算法改动需附整批留一结果或新鲜的预注册盲测；
不同数据集上的点估计只能作为背景，不能冒充 head-to-head 证据。贡献角色与 AI
辅助边界记录在 [CONTRIBUTORS.md](CONTRIBUTORS.md)。
