# 结果与证据账本

[简体中文](results.md) | [English](results.en.md)

## 发布结论

最终发布是 `release-candidate-v8` + `confirmation-v7`：先冻结、后采集、再揭盲。

- 75 次调用全部 `return_code=0`，75 个 sample ID 唯一。
- 75/75 严格 9×35 Schema 合规；prompt/schema hash、runtime、reasoning、wrapper
  在批内均一致。
- TraceOne `supported`：75/75，coverage 75/75，Wilson 95% CI
  95.13%–100%。
- 五类：5.5、Luna、Terra、Sol、Astra 均为 15/15。

这些是 requested-label agreement，不是独立的 served-weight 真值。

## 同响应 ModelTrace 对照

- TraceOne 一问：75/75。
- ModelTrace closed-set 一问：74/75；唯一错误在 Sol，因此 Sol 14/15，另四类
  15/15。
- ModelTrace 三问：25 个非重叠 triplet 全对，每类 5/5。

TraceOne 对 ModelTrace 一问的 paired discordance 只有 1 比 0；单侧 exact sign/
McNemar p=0.5，不足以证明准确率显著更高，也不是正式 non-inferiority 检验。
可以支持的结论是：本批五类逐类点估计未低于一问对照，Sol 多对一条；每次决定
从三次调用降到一次，且一问与三问 arm 的 accuracy 点估计均为 100%。三问只有
25 个决定，不能把 25/25 和 75/75 当作等样本量比较。

证据：

- [confirmation-v7 evaluation](../data/confirmation-v7-evaluation.json)
- [confirmation-v7 head-to-head](../data/confirmation-v7-head-to-head.json)
- [public confirmation responses](../data/public/confirmation-v7.jsonl)
- [release manifest](../config/release-v0.1.0.json)

## Open-world development

每个 fold 删除一个完整 excluded label 后再拟合，合计 8×36=288 个真正未见
label 样本：

- TraceOne `supported`：24/288 false accepts，8.33%，Wilson 95% CI
  5.66%–12.10%。
- TraceOne `enrolled`：59/288，20.49%，Wilson 95% CI 16.23%–25.52%。
- ModelTrace closed-set：288/288 false identifications；它在有效输入上没有
  `unknown` 分支。
- 同一 75 条 target holdout 在八个 gallery fold 中重复使用：`supported` 平均
  98.33%，最低 97.33%；不能把它当成 600 个独立样本。
- 主要失败集中于 GPT-5.4：`supported` 20/36 false accepts。

这是超参数已被查看的 development 结果，而且 unknown 来自上游语料，不是新
provider 盲测。它证明方法显著减少 closed-set 强制命名，但没有证明普适 OOD。
完整 decisions 在 [open-world-development-v2.json](../data/open-world-development-v2.json)。

旧 v6 的“完整 bank 内 excluded labels 2/288”只说明已登记 distractor rejection；
因为那些 labels 参与了 bank 构建，不再称为真正 open world。

## 开发过程中的失败

- 无 Schema 的 v2 曾出现 Luna 越界并截断，促成 strict 9×35 Schema。
- confirmation-v2 为 73/75，Sol 13/15；未过门槛。
- 190-row adapter 的真正盲测 confirmation-v3 为 71/75；未过门槛。
- confirmation-v4 为 73/75，Sol 13/15；未过门槛。
- v6 adapter 的 confirmation-v5 为 74/75；唯一失败是 Astra 240 秒 timeout，
  其余 74 个有效响应全部正确。
- v7 target-support 的 confirmation-v6 为 71/75：adapter 两错，support 又拒绝
  两个正确 Astra；未过每类 ≥14/15 门槛。这批随后才成为 v8 development。
- v8 选择 alpha=1：415-row whole-collection CV 为 412/415，优于 alpha=30 的
  411/415。KNN、LDA、RBF prototype 均未超过；见
  [adapter-model-exploration.json](../data/adapter-model-exploration.json)。

历史失败不与最终 confirmation 合并。为缩小公开发布面，原始失败批次不进入精简
主分支；其分母、关键结果和淘汰原因完整保留在本账本。

## Active probe 负结果

我们尝试把自由数字序列改成一次响应内 128 个成对二选一 bit：随机 pair v1 在
同数据选超参数的小样本 leave-one-out 为 24/25；按 340 条 enrollment 优化 pair
后的 v2 反而为 22/25，均低于主方法，因此没有进入发布 classifier。这项开发负
结果保留在账本中；其探索性 prompt、脚本和原始评测不进入精简发布主分支，也不
构成盲测结论。

## 降质检测状态

仓库提供完整方法，但没有捏造“已检测到服务端降质”的实测结论。

- 48-item canary 在假设 regression=0.10、improvement=0.02、minimum effect=0.05
  时 exact power 只有 29.06%。
- 192-item canary v2 的相应 power 为 89.76%。
- 实现报告 paired regressions/improvements、无效与缺失、exact one-sided McNemar，
  并对题族做 Holm-Bonferroni。

功效依赖预声明概率；实际监测必须重新记录 baseline/current 的 model、provider、
runtime、reasoning、wrapper、日期与重试策略。
